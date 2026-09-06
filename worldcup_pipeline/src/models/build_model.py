"""
Data Model Module

Builds star schema data model for analytics.
Creates fact and dimension tables optimized for BI.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import sessionmaker

from src.config import config, get_database_url
from src.utils import setup_logger

logger = setup_logger(__name__)


class StarSchemaBuilder:
    """
    Builds star schema data model from enriched data.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize star schema builder.
        
        Args:
            db_url: Database connection URL (optional)
        """
        self.db_url = db_url or get_database_url()
        self.engine = create_engine(self.db_url)
        self.metadata = MetaData()
        self.dimensions = {}
        self.facts = {}
    
    def build_star_schema(self, enriched_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Build complete star schema from enriched data.
        
        Args:
            enriched_df: Enriched match DataFrame
        
        Returns:
            Dictionary of table name -> DataFrame
        """
        logger.info("Building star schema")
        
        # Build dimension tables
        dim_date = self._build_dim_date(enriched_df)
        dim_team = self._build_dim_team(enriched_df)
        dim_location = self._build_dim_location(enriched_df)
        dim_temperature = self._build_dim_temperature(enriched_df)
        
        # Build fact table
        fact_matches = self._build_fact_matches(
            enriched_df,
            dim_date,
            dim_team,
            dim_location,
            dim_temperature
        )
        
        # Store tables
        tables = {
            'dim_date': dim_date,
            'dim_team': dim_team,
            'dim_location': dim_location,
            'dim_temperature': dim_temperature,
            'fact_matches': fact_matches
        }
        
        logger.info("Star schema built successfully")
        self._log_schema_stats(tables)
        
        return tables
    
    def _build_dim_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build date dimension table.
        
        Args:
            df: Source DataFrame
        
        Returns:
            Date dimension DataFrame
        """
        logger.info("Building dim_date")
        
        if 'match_date' not in df.columns:
            logger.warning("match_date column not found, creating minimal date dimension")
            dates = pd.DataFrame({
                'year': df['year'],
                'month': df['month'],
                'day': df.get('day', 1)
            })
            dates['full_date'] = pd.to_datetime(dates[['year', 'month', 'day']])
        else:
            dates = pd.DataFrame({'full_date': df['match_date'].unique()})
            dates = dates.dropna()
            # Ensure full_date is datetime
            dates['full_date'] = pd.to_datetime(dates['full_date'], errors='coerce')
            dates = dates.dropna()  # Drop any that couldn't be converted
            dates['year'] = dates['full_date'].dt.year
            dates['month'] = dates['full_date'].dt.month
            dates['day'] = dates['full_date'].dt.day
        
        # Add additional date attributes
        dates['quarter'] = dates['full_date'].dt.quarter
        dates['day_of_week'] = dates['full_date'].dt.dayofweek
        dates['day_name'] = dates['full_date'].dt.day_name()
        dates['month_name'] = dates['full_date'].dt.month_name()
        dates['is_weekend'] = dates['day_of_week'].isin([5, 6]).astype(int)
        
        # Create surrogate key
        dates = dates.sort_values('full_date').reset_index(drop=True)
        dates.insert(0, 'date_id', range(1, len(dates) + 1))
        
        logger.info(f"Created dim_date with {len(dates)} records")
        
        return dates
    
    def _build_dim_team(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build team dimension table.
        
        Args:
            df: Source DataFrame
        
        Returns:
            Team dimension DataFrame
        """
        logger.info("Building dim_team")
        
        # Find team columns
        team_cols = [col for col in df.columns if 'team' in col.lower()]
        
        if not team_cols:
            logger.warning("No team columns found")
            return pd.DataFrame(columns=['team_id', 'team_name'])
        
        # Collect all unique teams
        teams = set()
        for col in team_cols:
            teams.update(df[col].dropna().unique())
        
        teams = sorted(list(teams))
        
        dim_team = pd.DataFrame({
            'team_id': range(1, len(teams) + 1),
            'team_name': teams
        })
        
        # Add team code (first 3 letters uppercase)
        dim_team['team_code'] = dim_team['team_name'].str[:3].str.upper()
        
        # Add confederation (simplified - could be enhanced with lookup table)
        dim_team['confederation'] = dim_team['team_name'].apply(self._infer_confederation)
        
        logger.info(f"Created dim_team with {len(dim_team)} records")
        
        return dim_team
    
    def _build_dim_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build location dimension table.
        
        Args:
            df: Source DataFrame
        
        Returns:
            Location dimension DataFrame
        """
        logger.info("Building dim_location")
        
        # Identify location columns
        location_cols = ['city', 'country']
        available_cols = [col for col in location_cols if col in df.columns]
        
        if not available_cols:
            logger.warning("No location columns found")
            return pd.DataFrame(columns=['location_id', 'country'])
        
        # Get unique locations
        locations = df[available_cols].drop_duplicates().reset_index(drop=True)
        locations.insert(0, 'location_id', range(1, len(locations) + 1))
        
        # Add stadium if available
        if 'stadium' in df.columns:
            stadium_mapping = df.groupby(available_cols)['stadium'].first()
            locations = locations.merge(
                stadium_mapping.reset_index(),
                on=available_cols,
                how='left'
            )
        
        # Add placeholder for geocoding (latitude, longitude)
        # In production, these would come from a geocoding service
        locations['latitude'] = None
        locations['longitude'] = None
        
        logger.info(f"Created dim_location with {len(locations)} records")
        
        return locations
    
    def _build_dim_temperature(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build temperature dimension table.
        
        Args:
            df: Source DataFrame
        
        Returns:
            Temperature dimension DataFrame
        """
        logger.info("Building dim_temperature")
        
        temp_cols = ['country', 'year', 'avg_temperature_celsius', 'temperature_category']
        
        if 'month' in df.columns and 'avg_temperature_celsius' in df.columns:
            temp_cols.insert(2, 'month')
        
        available_cols = [col for col in temp_cols if col in df.columns]
        
        if 'avg_temperature_celsius' not in available_cols:
            logger.warning("Temperature data not available")
            return pd.DataFrame(columns=['temperature_id'] + temp_cols)
        
        # Get unique temperature records
        dim_temp = df[available_cols].drop_duplicates().dropna(subset=['avg_temperature_celsius'])
        dim_temp = dim_temp.reset_index(drop=True)
        dim_temp.insert(0, 'temperature_id', range(1, len(dim_temp) + 1))
        
        logger.info(f"Created dim_temperature with {len(dim_temp)} records")
        
        return dim_temp
    
    def _build_fact_matches(
        self,
        df: pd.DataFrame,
        dim_date: pd.DataFrame,
        dim_team: pd.DataFrame,
        dim_location: pd.DataFrame,
        dim_temperature: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Build fact table for matches.
        
        Args:
            df: Source DataFrame
            dim_date: Date dimension
            dim_team: Team dimension
            dim_location: Location dimension
            dim_temperature: Temperature dimension
        
        Returns:
            Fact table DataFrame
        """
        logger.info("Building fact_matches")
        
        fact = df.copy()
        
        # Ensure match_date is datetime if it exists
        if 'match_date' in fact.columns:
            fact['match_date'] = pd.to_datetime(fact['match_date'], errors='coerce')
        
        # Join with date dimension
        if 'match_date' in fact.columns and 'full_date' in dim_date.columns:
            fact = fact.merge(
                dim_date[['date_id', 'full_date']],
                left_on='match_date',
                right_on='full_date',
                how='left'
            )
        elif 'year' in fact.columns:
            # Fallback to year/month matching
            merge_cols = ['year', 'month'] if 'month' in fact.columns else ['year']
            fact = fact.merge(
                dim_date[['date_id'] + merge_cols].drop_duplicates(subset=merge_cols),
                on=merge_cols,
                how='left'
            )
        
        # Join with location dimension
        location_cols = [col for col in ['city', 'country'] if col in fact.columns]
        if location_cols:
            fact = fact.merge(
                dim_location[['location_id'] + location_cols],
                on=location_cols,
                how='left'
            )
        
        # Join with team dimension (home and away)
        home_team_col = next((col for col in fact.columns if 'home' in col.lower() and 'team' in col.lower()), None)
        away_team_col = next((col for col in fact.columns if 'away' in col.lower() and 'team' in col.lower()), None)
        
        if home_team_col:
            fact = fact.merge(
                dim_team[['team_id', 'team_name']],
                left_on=home_team_col,
                right_on='team_name',
                how='left',
                suffixes=('', '_home')
            )
            fact = fact.rename(columns={'team_id': 'home_team_id'})
        
        if away_team_col:
            fact = fact.merge(
                dim_team[['team_id', 'team_name']],
                left_on=away_team_col,
                right_on='team_name',
                how='left',
                suffixes=('', '_away')
            )
            fact = fact.rename(columns={'team_id': 'away_team_id'})
        
        # Join with temperature dimension
        temp_join_cols = ['country', 'year']
        if 'month' in dim_temperature.columns:
            temp_join_cols.append('month')
        
        available_temp_cols = [col for col in temp_join_cols if col in fact.columns and col in dim_temperature.columns]
        
        if available_temp_cols and 'avg_temperature_celsius' in dim_temperature.columns:
            fact = fact.merge(
                dim_temperature[['temperature_id'] + available_temp_cols + ['avg_temperature_celsius']].drop_duplicates(subset=available_temp_cols),
                on=available_temp_cols,
                how='left',
                suffixes=('', '_dim')
            )
        
        # Select and rename fact columns
        fact_columns = {
            'match_id': 'match_id',
            'date_id': 'date_id',
            'location_id': 'location_id',
            'home_team_id': 'home_team_id',
            'away_team_id': 'away_team_id',
            'temperature_id': 'temperature_id'
        }
        
        # Add measure columns (goals/scores)
        # Check for both 'goal' and 'score' in column names
        goal_score_cols = [col for col in fact.columns if 'goal' in col.lower() or 'score' in col.lower()]
        logger.info(f"Found goal/score columns: {goal_score_cols}")
        for col in goal_score_cols:
            fact_columns[col] = col
        
        # Specifically add home_goals and away_goals if they exist
        if 'home_goals' in fact.columns:
            fact_columns['home_goals'] = 'home_goals'
            logger.info("Added home_goals column")
        if 'away_goals' in fact.columns:
            fact_columns['away_goals'] = 'away_goals'
            logger.info("Added away_goals column")
        
        # Log all available columns in source data
        logger.info(f"All columns in fact DataFrame: {list(fact.columns)}")
        logger.info(f"Columns to include in fact_matches: {list(fact_columns.keys())}")
        
        # Add other measure columns
        if 'attendance' in fact.columns:
            fact_columns['attendance'] = 'attendance'
        
        if 'stage' in fact.columns:
            fact_columns['stage'] = 'stage'
        
        if 'round' in fact.columns:
            fact_columns['round'] = 'round'
        
        if 'year' in fact.columns:
            fact_columns['year'] = 'year'
        
        # Create match_id if not present
        if 'match_id' not in fact.columns:
            fact['match_id'] = range(1, len(fact) + 1)
        
        # Select only available columns
        available_fact_cols = [col for col in fact_columns.keys() if col in fact.columns]
        fact_final = fact[available_fact_cols].copy()
        
        logger.info(f"Created fact_matches with {len(fact_final)} records")
        
        return fact_final
    
    def _infer_confederation(self, team_name: str) -> str:
        """
        Infer confederation from team name.
        Simplified version - in production would use lookup table.
        """
        # Simplified mapping
        european_teams = ['Germany', 'France', 'Italy', 'Spain', 'England', 'Netherlands', 
                         'Portugal', 'Belgium', 'Russia', 'Poland', 'Ukraine', 'Croatia',
                         'Sweden', 'Switzerland', 'Austria', 'Czech', 'Serbia']
        south_american = ['Brazil', 'Argentina', 'Uruguay', 'Colombia', 'Chile', 'Paraguay', 
                         'Peru', 'Ecuador', 'Bolivia', 'Venezuela']
        
        if any(eu in team_name for eu in european_teams):
            return 'UEFA'
        elif any(sa in team_name for sa in south_american):
            return 'CONMEBOL'
        elif any(region in team_name for region in ['USA', 'United States', 'Mexico', 'Canada', 'Costa Rica']):
            return 'CONCACAF'
        elif any(region in team_name for region in ['Nigeria', 'Ghana', 'Cameroon', 'Senegal', 'South Africa']):
            return 'CAF'
        elif any(region in team_name for region in ['Japan', 'South Korea', 'Australia', 'Iran', 'Saudi']):
            return 'AFC'
        else:
            return 'Other'
    
    def _log_schema_stats(self, tables: Dict[str, pd.DataFrame]):
        """Log statistics about created tables."""
        logger.info("Star Schema Statistics:")
        for table_name, df in tables.items():
            logger.info(f"  {table_name}: {len(df)} records, {len(df.columns)} columns")
    
    def save_to_database(self, tables: Dict[str, pd.DataFrame]):
        """
        Save tables to database.
        
        Args:
            tables: Dictionary of table DataFrames
        """
        logger.info(f"Saving tables to database: {self.db_url}")
        
        for table_name, df in tables.items():
            try:
                df.to_sql(
                    table_name,
                    self.engine,
                    if_exists='replace',
                    index=False
                )
                logger.info(f"Saved {table_name} ({len(df)} records)")
            except Exception as e:
                logger.error(f"Error saving {table_name}: {e}")
        
        logger.info("Database save complete")
    
    def save_to_files(self, tables: Dict[str, pd.DataFrame], output_dir: Path):
        """
        Save tables to parquet files.
        
        Args:
            tables: Dictionary of table DataFrames
            output_dir: Output directory path
        """
        logger.info(f"Saving tables to {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for table_name, df in tables.items():
            output_path = output_dir / f"{table_name}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved {table_name} to {output_path}")
        
        logger.info("File save complete")


def build_and_save_model() -> bool:
    """
    Build star schema model and save to database and files.
    
    Returns:
        bool: True if successful
    """
    try:
        # Load enriched data
        enriched_path = config.processed_data_path / config.GOLD_ENRICHED_FILE
        
        if not enriched_path.exists():
            logger.error(f"Enriched data not found: {enriched_path}")
            return False
        
        logger.info(f"Loading enriched data from {enriched_path}")
        enriched_df = pd.read_parquet(enriched_path)
        
        # Build star schema
        builder = StarSchemaBuilder()
        tables = builder.build_star_schema(enriched_df)
        
        # Save to database
        builder.save_to_database(tables)
        
        # Save to files
        builder.save_to_files(tables, config.GOLD_PATH)
        
        logger.info("Model build and save completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error building model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = build_and_save_model()
    exit(0 if success else 1)