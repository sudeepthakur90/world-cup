"""
Data Enrichment Module

Enriches World Cup match data with temperature information.
Handles date and location matching with fuzzy logic.
"""

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


class DataEnricher:
    """
    Handles enrichment of World Cup data with temperature information.
    """
    
    def __init__(self):
        self.match_report = {}
    
    def enrich_matches_with_temperature(
        self,
        matches_df: pd.DataFrame,
        temperature_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Enrich match data with temperature information.
        
        Args:
            matches_df: Cleaned World Cup matches DataFrame
            temperature_df: Cleaned temperature DataFrame
        
        Returns:
            Enriched DataFrame with temperature data
        """
        logger.info("Starting temperature enrichment")
        logger.info(f"Matches: {len(matches_df)}, Temperature records: {len(temperature_df)}")
        
        enriched = matches_df.copy()
        
        # Ensure required columns exist
        if 'year' not in enriched.columns or 'month' not in enriched.columns:
            logger.error("Match data missing year/month columns")
            return enriched
        
        if 'country' not in enriched.columns:
            logger.warning("Match data missing country column")
            # Try to infer from other columns
            enriched['country'] = self._infer_country(enriched)
        
        # Prepare temperature data for joining
        temp_prepared = self._prepare_temperature_data(temperature_df)
        
        # Perform the enrichment join
        enriched = self._join_temperature_data(enriched, temp_prepared)
        
        # Generate matching statistics
        self._generate_match_report(enriched)
        
        # Check which temperature column exists
        temp_col = 'avg_temperature_celsius' if 'avg_temperature_celsius' in enriched.columns else 'temperature'
        logger.info(f"Enrichment complete. Records with temperature: {enriched[temp_col].notna().sum()}")
        
        return enriched
    
    def _prepare_temperature_data(self, temp_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare temperature data for joining.
        
        Args:
            temp_df: Temperature DataFrame
        
        Returns:
            Prepared temperature DataFrame
        """
        logger.info("Preparing temperature data for joining")
        
        temp_prepared = temp_df.copy()
        
        # Check which month column exists (transformation outputs 'month_num')
        month_col = None
        if 'month_num' in temp_prepared.columns:
            month_col = 'month_num'
        elif 'month' in temp_prepared.columns:
            month_col = 'month'
        
        # If we have monthly data, use it directly
        if month_col:
            # Group by country, year, month and take mean temperature
            temp_prepared = temp_prepared.groupby(
                ['country', 'year', month_col],
                as_index=False
            ).agg({
                'temperature': 'mean'
            })
            # Standardize column name to 'month' for joining
            if month_col == 'month_num':
                temp_prepared = temp_prepared.rename(columns={'month_num': 'month'})
            logger.info("Using monthly temperature averages")
        else:
            # If only yearly data, calculate annual average
            temp_prepared = temp_prepared.groupby(
                ['country', 'year'],
                as_index=False
            ).agg({
                'temperature': 'mean'
            })
            logger.info("Using yearly temperature averages")
        
        # Rename temperature column for clarity
        temp_prepared = temp_prepared.rename(columns={
            'temperature': 'avg_temperature_celsius'
        })
        
        # Add temperature category
        temp_prepared['temperature_category'] = pd.cut(
            temp_prepared['avg_temperature_celsius'],
            bins=[-float('inf'), 10, 20, 30, float('inf')],
            labels=['Cold', 'Moderate', 'Warm', 'Hot']
        )
        
        logger.info(f"Prepared {len(temp_prepared)} temperature records for joining")
        
        return temp_prepared
    
    def _join_temperature_data(
        self,
        matches: pd.DataFrame,
        temperature: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Join match and temperature data.
        
        Args:
            matches: Match DataFrame
            temperature: Prepared temperature DataFrame
        
        Returns:
            Joined DataFrame
        """
        logger.info("Joining match and temperature data")
        
        # Prepare DataFrames for joining
        matches_join = matches.copy()
        temp_join = temperature.copy()
        
        # Ensure both month columns are integers (already named 'month' from preparation)
        if 'month' in temp_join.columns and 'month' in matches_join.columns:
            matches_join['month'] = matches_join['month'].astype(int)
            temp_join['month'] = temp_join['month'].astype(int)
        
        # Determine join keys
        join_keys = ['country', 'year']
        if 'month' in temp_join.columns and 'month' in matches_join.columns:
            join_keys.append('month')
            logger.info("Performing join on country, year, and month")
        else:
            logger.info("Performing join on country and year")
        
        # Log data types for debugging
        logger.debug(f"Matches join keys types: {matches_join[join_keys].dtypes.to_dict()}")
        logger.debug(f"Temperature join keys types: {temp_join[join_keys].dtypes.to_dict()}")
        
        # Perform left join to keep all matches
        enriched = matches_join.merge(
            temp_join,
            on=join_keys,
            how='left',
            suffixes=('', '_temp')
        )
        
        # Calculate match statistics
        total_matches = len(enriched)
        matched = enriched['avg_temperature_celsius'].notna().sum()
        match_rate = (matched / total_matches * 100) if total_matches > 0 else 0
        
        logger.info(f"Matched {matched}/{total_matches} matches ({match_rate:.1f}%)")
        
        # For unmatched records, try country-level yearly average
        if matched < total_matches:
            unmatched = enriched['avg_temperature_celsius'].isna()
            logger.info(f"Attempting to fill {unmatched.sum()} unmatched records with yearly averages")
            
            # Create yearly average lookup
            yearly_avg = temperature.groupby(['country', 'year'])['avg_temperature_celsius'].mean()
            
            # Fill missing values
            for idx in enriched[unmatched].index:
                country = enriched.loc[idx, 'country']
                year = enriched.loc[idx, 'year']
                
                if (country, year) in yearly_avg.index:
                    enriched.loc[idx, 'avg_temperature_celsius'] = yearly_avg.loc[(country, year)]
                    enriched.loc[idx, 'temperature_category'] = self._categorize_temperature(
                        yearly_avg.loc[(country, year)]
                    )
        
        return enriched
    
    def _infer_country(self, df: pd.DataFrame) -> pd.Series:
        """
        Infer country from available columns.
        
        Args:
            df: DataFrame
        
        Returns:
            Series with inferred country
        """
        # Look for country-related columns
        for col in ['host_country', 'location', 'venue_country']:
            if col in df.columns:
                logger.info(f"Inferring country from {col}")
                return df[col]
        
        logger.warning("Could not infer country from available columns")
        return pd.Series([None] * len(df))
    
    def _categorize_temperature(self, temp: float) -> str:
        """
        Categorize temperature value.
        
        Args:
            temp: Temperature in Celsius
        
        Returns:
            Category string
        """
        if pd.isna(temp):
            return None
        elif temp < 10:
            return 'Cold'
        elif temp < 20:
            return 'Moderate'
        elif temp < 30:
            return 'Warm'
        else:
            return 'Hot'
    
    def _generate_match_report(self, df: pd.DataFrame):
        """
        Generate statistics about the enrichment process.
        
        Args:
            df: Enriched DataFrame
        """
        total = len(df)
        with_temp = df['avg_temperature_celsius'].notna().sum()
        without_temp = total - with_temp
        
        self.match_report = {
            'total_matches': total,
            'matches_with_temperature': with_temp,
            'matches_without_temperature': without_temp,
            'match_rate_percent': (with_temp / total * 100) if total > 0 else 0,
            'temperature_stats': {
                'min': float(df['avg_temperature_celsius'].min()) if with_temp > 0 else None,
                'max': float(df['avg_temperature_celsius'].max()) if with_temp > 0 else None,
                'mean': float(df['avg_temperature_celsius'].mean()) if with_temp > 0 else None,
                'median': float(df['avg_temperature_celsius'].median()) if with_temp > 0 else None
            },
            'category_distribution': df['temperature_category'].value_counts().to_dict() if 'temperature_category' in df.columns else {}
        }
        
        logger.info(f"Enrichment report: {self.match_report}")


def enrich_data() -> Tuple[bool, Optional[pd.DataFrame]]:
    """
    Load cleaned data and perform enrichment.
    
    Returns:
        Tuple of (success: bool, enriched_df: Optional[pd.DataFrame])
    """
    try:
        # Load cleaned data
        worldcup_path = config.processed_data_path / config.worldcup_cleaned
        temperature_path = config.processed_data_path / config.temperature_cleaned
        
        if not worldcup_path.exists():
            logger.error(f"Cleaned World Cup data not found: {worldcup_path}")
            return False, None
        
        if not temperature_path.exists():
            logger.error(f"Cleaned temperature data not found: {temperature_path}")
            return False, None
        
        logger.info("Loading cleaned datasets")
        matches_df = pd.read_parquet(worldcup_path)
        temperature_df = pd.read_parquet(temperature_path)
        
        # Enrich data
        enricher = DataEnricher()
        enriched_df = enricher.enrich_matches_with_temperature(matches_df, temperature_df)
        
        # Save enriched data
        output_path = config.processed_data_path / config.GOLD_ENRICHED_FILE
        enriched_df.to_parquet(output_path, index=False)
        logger.info(f"Saved enriched data to {output_path}")
        
        return True, enriched_df
        
    except Exception as e:
        logger.error(f"Error during enrichment: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None


if __name__ == "__main__":
    success, _ = enrich_data()
    exit(0 if success else 1)