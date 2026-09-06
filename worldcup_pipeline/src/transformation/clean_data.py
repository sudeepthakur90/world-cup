"""
Data Transformation Module - Updated for Actual Column Names

Cleans World Cup and temperature data using ACTUAL column names:
- World Cup: Year, Date, Time, Round, Stadium, City, Country, HomeTeam, HomeGoals, AwayGoals, AwayTeam, Observation
- Temperature: Entity, Code, Month, Monthly average
"""

import sys
from pathlib import Path
from typing import Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


def clean_worldcup_data() -> Tuple[bool, pd.DataFrame]:
    """
    Clean World Cup dataset with ACTUAL column names.
    
    Expected columns:
    - Year, Date, Time, Round, Stadium, City, Country, 
    - HomeTeam, HomeGoals, AwayGoals, AwayTeam, Observation
    
    Returns:
        Tuple of (success: bool, cleaned_dataframe: pd.DataFrame)
    """
    logger.info("="*60)
    logger.info("CLEANING WORLD CUP DATA (Pandas)")
    logger.info("="*60)
    
    try:
        # Read Excel or CSV
        excel_path = config.raw_data_path / config.worldcup_raw
        csv_path = config.raw_data_path / config.worldcup_raw_csv
        
        if excel_path.exists():
            logger.info(f"Reading: {excel_path}")
            df = pd.read_excel(excel_path)
        elif csv_path.exists():
            logger.info(f"Reading: {csv_path}")
            df = pd.read_csv(csv_path)
        else:
            logger.error("No World Cup data file found")
            return False, None
        
        logger.info(f"✓ Loaded {len(df)} records")
        logger.info(f"✓ Columns: {list(df.columns)}")
        
        # Create working copy
        df_clean = df.copy()
        
        # ========================================
        # COLUMN STANDARDIZATION
        # ========================================
        # Rename to standard names (lowercase, underscores)
        column_mapping = {
            'Year': 'year',
            'Date': 'date',
            'Time': 'time',
            'Round': 'round',
            'Stadium': 'stadium',
            'City': 'city',
            'Country': 'country',
            'HomeTeam': 'home_team',
            'HomeGoals': 'home_goals',
            'AwayGoals': 'away_goals',
            'AwayTeam': 'away_team',
            'Observation': 'observation'
        }
        
        # Apply renaming (only for columns that exist)
        rename_map = {k: v for k, v in column_mapping.items() if k in df_clean.columns}
        df_clean.rename(columns=rename_map, inplace=True)
        
        logger.info("✓ Standardized column names")
        
        # ========================================
        # DATE PROCESSING
        # ========================================
        # Convert date to datetime
        df_clean['match_date'] = pd.to_datetime(df_clean['date'], errors='coerce')
        
        # Remove records with invalid dates
        before_count = len(df_clean)
        df_clean = df_clean.dropna(subset=['match_date'])
        after_count = len(df_clean)
        
        if before_count > after_count:
            logger.info(f"✓ Removed {before_count - after_count} records with invalid dates")
        
        # Extract date components
        df_clean['year'] = df_clean['match_date'].dt.year
        df_clean['month'] = df_clean['match_date'].dt.month
        df_clean['quarter'] = df_clean['match_date'].dt.quarter
        df_clean['day'] = df_clean['match_date'].dt.day
        df_clean['day_of_week'] = df_clean['match_date'].dt.dayofweek
        df_clean['day_name'] = df_clean['match_date'].dt.day_name()
        
        logger.info("✓ Parsed dates and extracted components")
        
        # Filter by year range
        df_clean = df_clean[
            (df_clean['year'] >= config.min_year) & 
            (df_clean['year'] <= config.max_year)
        ]
        
        logger.info(f"✓ Filtered to years {config.min_year}-{config.max_year}")
        
        # ========================================
        # TEAM NAME CLEANING
        # ========================================
        # Clean team names (remove extra spaces, standardize case)
        for team_col in ['home_team', 'away_team']:
            if team_col in df_clean.columns:
                df_clean[team_col] = df_clean[team_col].str.strip()
                # Standardize common variations
                df_clean[team_col] = df_clean[team_col].replace({
                    'USA': 'United States',
                    'Korea Republic': 'South Korea',
                    'Korea DPR': 'North Korea',
                    'IR Iran': 'Iran',
                    'rn">West Germany': 'West Germany',  # Clean HTML artifacts
                    'rn">': ''  # Remove HTML artifacts
                }, regex=True)
        
        logger.info("✓ Cleaned team names")
        
        # ========================================
        # SCORE CLEANING
        # ========================================
        # Ensure scores are numeric
        for score_col in ['home_goals', 'away_goals']:
            if score_col in df_clean.columns:
                df_clean[score_col] = pd.to_numeric(df_clean[score_col], errors='coerce')
                df_clean[score_col] = df_clean[score_col].fillna(0).astype(int)
        
        logger.info("✓ Cleaned scores")
        
        # ========================================
        # LOCATION CLEANING
        # ========================================
        # Clean city, country, stadium
        for location_col in ['city', 'country', 'stadium']:
            if location_col in df_clean.columns:
                df_clean[location_col] = df_clean[location_col].str.strip()
        
        # ========================================
        # DERIVED COLUMNS
        # ========================================
        # Calculate total goals
        df_clean['total_goals'] = df_clean['home_goals'] + df_clean['away_goals']
        
        # Determine winner
        def determine_winner(row):
            if row['home_goals'] > row['away_goals']:
                return row['home_team']
            elif row['away_goals'] > row['home_goals']:
                return row['away_team']
            else:
                return 'Draw'
        
        df_clean['winner'] = df_clean.apply(determine_winner, axis=1)
        
        # Match outcome from home team perspective
        def match_outcome(row):
            if row['home_goals'] > row['away_goals']:
                return 'Home Win'
            elif row['away_goals'] > row['home_goals']:
                return 'Away Win'
            else:
                return 'Draw'
        
        df_clean['outcome'] = df_clean.apply(match_outcome, axis=1)
        
        logger.info("✓ Added derived columns (total_goals, winner, outcome)")
        
        # ========================================
        # REMOVE DUPLICATES
        # ========================================
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['match_date', 'home_team', 'away_team'])
        after_count = len(df_clean)
        
        if before_count > after_count:
            logger.info(f"✓ Removed {before_count - after_count} duplicate records")
        
        logger.info(f"✓ Final record count: {len(df_clean)}")
        
        # ========================================
        # SAVE CLEANED DATA
        # ========================================
        output_path = config.processed_data_path / config.worldcup_cleaned
        df_clean.to_parquet(output_path, index=False)
        
        logger.info(f"✓ Saved cleaned data: {output_path}")
        logger.info("="*60)
        logger.info("✓ WORLD CUP DATA CLEANING COMPLETE")
        logger.info("="*60)
        
        return True, df_clean
        
    except Exception as e:
        logger.error(f"Error cleaning World Cup data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None


def clean_temperature_data() -> Tuple[bool, pd.DataFrame]:
    """
    Clean temperature dataset with ACTUAL column names.
    
    Expected columns:
    - Entity (country name)
    - Code (country code)
    - Month (YYYY-MM format)
    - Monthly average (temperature in Celsius)
    
    Returns:
        Tuple of (success: bool, cleaned_dataframe: pd.DataFrame)
    """
    logger.info("\n" + "="*60)
    logger.info("CLEANING TEMPERATURE DATA (Pandas)")
    logger.info("="*60)
    
    try:
        # Read CSV
        csv_path = config.raw_data_path / config.temperature_raw
        logger.info(f"Reading: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        logger.info(f"✓ Loaded {len(df):,} records")
        logger.info(f"✓ Columns: {list(df.columns)}")
        
        # Create working copy
        df_clean = df.copy()
        
        # ========================================
        # COLUMN STANDARDIZATION
        # ========================================
        # Rename to standard names
        column_mapping = {
            'Entity': 'country',
            'Code': 'country_code',
            'Month': 'month',
            'Monthly average': 'temperature'
        }
        
        # Apply renaming
        rename_map = {k: v for k, v in column_mapping.items() if k in df_clean.columns}
        df_clean.rename(columns=rename_map, inplace=True)
        
        logger.info("✓ Standardized column names")
        
        # ========================================
        # DATE PROCESSING
        # ========================================
        # Convert month to datetime
        df_clean['date'] = pd.to_datetime(df_clean['month'], errors='coerce')
        
        # Remove invalid dates
        before_count = len(df_clean)
        df_clean = df_clean.dropna(subset=['date'])
        after_count = len(df_clean)
        
        if before_count > after_count:
            logger.info(f"✓ Removed {before_count - after_count:,} records with invalid dates")
        
        # Extract date components
        df_clean['year'] = df_clean['date'].dt.year
        df_clean['month_num'] = df_clean['date'].dt.month
        df_clean['quarter'] = df_clean['date'].dt.quarter
        
        logger.info("✓ Parsed dates and extracted components")
        
        # ========================================
        # TEMPERATURE CLEANING
        # ========================================
        # Ensure temperature is numeric
        df_clean['temperature'] = pd.to_numeric(df_clean['temperature'], errors='coerce')
        
        # Remove null temperatures
        df_clean = df_clean.dropna(subset=['temperature'])
        
        # Filter reasonable temperature range (-60°C to 60°C)
        before_count = len(df_clean)
        df_clean = df_clean[
            (df_clean['temperature'] >= config.min_temperature) &
            (df_clean['temperature'] <= config.max_temperature)
        ]
        after_count = len(df_clean)
        
        if before_count > after_count:
            logger.info(f"✓ Removed {before_count - after_count:,} records with invalid temperatures")
        
        logger.info(f"✓ Filtered temperature range: {config.min_temperature}°C to {config.max_temperature}°C")
        
        # ========================================
        # COUNTRY NAME CLEANING
        # ========================================
        # Clean country names
        df_clean['country'] = df_clean['country'].str.strip()
        
        # Standardize country names to match World Cup data
        country_mapping = {
            'United States': 'United States',
            'Korea': 'South Korea',
            'Iran (Islamic Republic of)': 'Iran',
            'Republic of Korea': 'South Korea',
            'Democratic People\'s Republic of Korea': 'North Korea'
        }
        
        df_clean['country'] = df_clean['country'].replace(country_mapping)
        
        logger.info("✓ Cleaned country names")
        
        # ========================================
        # FILTER BY YEAR RANGE
        # ========================================
        # Filter to World Cup years range
        df_clean = df_clean[
            (df_clean['year'] >= config.min_year) &
            (df_clean['year'] <= config.max_year)
        ]
        
        logger.info(f"✓ Filtered to years {config.min_year}-{config.max_year}")
        
        # ========================================
        # REMOVE DUPLICATES
        # ========================================
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['country', 'date'])
        after_count = len(df_clean)
        
        if before_count > after_count:
            logger.info(f"✓ Removed {before_count - after_count:,} duplicate records")
        
        logger.info(f"✓ Final record count: {len(df_clean):,}")
        
        # ========================================
        # SAVE CLEANED DATA
        # ========================================
        output_path = config.processed_data_path / config.temperature_cleaned
        df_clean.to_parquet(output_path, index=False)
        
        logger.info(f"✓ Saved cleaned data: {output_path}")
        logger.info("="*60)
        logger.info("✓ TEMPERATURE DATA CLEANING COMPLETE")
        logger.info("="*60)
        
        return True, df_clean
        
    except Exception as e:
        logger.error(f"Error cleaning temperature data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None


def clean_all_data() -> bool:
    """
    Clean all datasets.
    
    Returns:
        bool: True if all cleaning succeeded
    """
    logger.info("\n" + "#"*60)
    logger.info("#" + " "*58 + "#")
    logger.info("#" + "  DATA TRANSFORMATION (Pandas)".center(58) + "#")
    logger.info("#" + " "*58 + "#")
    logger.info("#"*60 + "\n")
    
    # Clean World Cup data
    wc_success, wc_df = clean_worldcup_data()
    if not wc_success:
        logger.error("Failed to clean World Cup data")
        return False
    
    # Clean temperature data
    temp_success, temp_df = clean_temperature_data()
    if not temp_success:
        logger.error("Failed to clean temperature data")
        return False
    
    logger.info("\n" + "="*60)
    logger.info("✓ ALL DATA TRANSFORMATION COMPLETE")
    logger.info("="*60)
    logger.info(f"\nCleaned data saved to: {config.processed_data_path}")
    logger.info("  - worldcup_cleaned.parquet")
    logger.info("  - temperature_cleaned.parquet")
    
    return True


def main():
    """
    Main entry point.
    """
    success = clean_all_data()
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
