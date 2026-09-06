"""
Data Transformation Module - PySpark Version

Cleans and transforms World Cup and temperature data using PySpark.
Same business logic as Pandas version, different API.
"""

import sys
from pathlib import Path
from typing import Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.functions import (
        col, to_date, year, month, quarter, dayofmonth, dayofweek,
        trim, initcap, lower, regexp_replace, when, coalesce, lit
    )
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("Warning: PySpark not installed. Install with: pip install pyspark")

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


def get_spark_session() -> SparkSession:
    """
    Get or create Spark session.
    
    Returns:
        SparkSession instance
    """
    spark = SparkSession.builder \
        .appName("WorldCupPipeline-Transformation") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    
    return spark


def clean_worldcup_data_spark(spark: SparkSession = None) -> Tuple[bool, DataFrame]:
    """
    Clean World Cup dataset using PySpark.
    Reads from CSV (Spark-compatible format).
    
    Args:
        spark: SparkSession instance (creates new if None)
    
    Returns:
        Tuple of (success: bool, cleaned_dataframe: DataFrame)
    """
    if not PYSPARK_AVAILABLE:
        logger.error("PySpark not installed. Cannot proceed.")
        return False, None
    
    logger.info("="*60)
    logger.info("CLEANING WORLD CUP DATA (PySpark)")
    logger.info("="*60)
    
    try:
        # Get Spark session
        if spark is None:
            spark = get_spark_session()
        
        # Read CSV file (Spark-compatible)
        csv_path = config.raw_data_path / config.worldcup_raw_csv
        logger.info(f"Reading: {csv_path}")
        
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(str(csv_path))
        
        logger.info(f"✓ Loaded {df.count()} records")
        
        # Rename columns to standard names
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
        
        # Apply renaming
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.withColumnRenamed(old_name, new_name)
        
        logger.info("✓ Standardized column names")
        
        # Parse dates (using 'date' column, not 'datetime')
        df = df.withColumn('match_date', to_date(col('date'), 'yyyy-MM-dd'))
        
        # Extract date components
        df = df.withColumn('year', year(col('match_date')))
        df = df.withColumn('month', month(col('match_date')))
        df = df.withColumn('quarter', quarter(col('match_date')))
        df = df.withColumn('day', dayofmonth(col('match_date')))
        df = df.withColumn('day_of_week', dayofweek(col('match_date')))
        
        logger.info("✓ Parsed dates and extracted components")
        
        # Filter by year range
        df = df.filter(
            (col('year') >= config.min_year) & 
            (col('year') <= config.max_year)
        )
        
        logger.info(f"✓ Filtered to years {config.min_year}-{config.max_year}")
        
        # Clean team names
        for team_col in ['home_team', 'away_team']:
            if team_col in df.columns:
                df = df.withColumn(team_col, initcap(trim(col(team_col))))
        
        logger.info("✓ Cleaned team names")
        
        # Clean scores (ensure numeric)
        for score_col in ['home_goals', 'away_goals']:
            if score_col in df.columns:
                df = df.withColumn(
                    score_col,
                    coalesce(col(score_col).cast('integer'), lit(0))
                )
        
        logger.info("✓ Cleaned scores")
        
        # Clean city and stadium
        for location_col in ['city', 'stadium']:
            if location_col in df.columns:
                df = df.withColumn(location_col, initcap(trim(col(location_col))))
        
        # Remove duplicates
        df = df.dropDuplicates()
        
        final_count = df.count()
        logger.info(f"✓ Removed duplicates: {final_count} unique records")
        
        # Save as Parquet
        output_path = config.processed_data_path / config.worldcup_cleaned
        df.write.mode('overwrite').parquet(str(output_path))
        
        logger.info(f"✓ Saved cleaned data: {output_path}")
        logger.info("="*60)
        logger.info("✓ WORLD CUP DATA CLEANING COMPLETE (PySpark)")
        logger.info("="*60)
        
        return True, df
        
    except Exception as e:
        logger.error(f"Error cleaning World Cup data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None


def clean_temperature_data_spark(spark: SparkSession = None) -> Tuple[bool, DataFrame]:
    """
    Clean temperature dataset using PySpark.
    
    Args:
        spark: SparkSession instance (creates new if None)
    
    Returns:
        Tuple of (success: bool, cleaned_dataframe: DataFrame)
    """
    if not PYSPARK_AVAILABLE:
        logger.error("PySpark not installed. Cannot proceed.")
        return False, None
    
    logger.info("\n" + "="*60)
    logger.info("CLEANING TEMPERATURE DATA (PySpark)")
    logger.info("="*60)
    
    try:
        # Get Spark session
        if spark is None:
            spark = get_spark_session()
        
        # Read CSV file
        csv_path = config.raw_data_path / config.temperature_raw
        logger.info(f"Reading: {csv_path}")
        
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(str(csv_path))
        
        logger.info(f"✓ Loaded {df.count()} records")
        
        # Rename columns to standard names
        # Actual columns: Entity, Code, Month, Monthly average
        column_mapping = {
            'Entity': 'country',
            'Code': 'country_code',
            'Month': 'month',
            'Monthly average': 'temperature'
        }
        
        # Apply renaming
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.withColumnRenamed(old_name, new_name)
        
        logger.info("✓ Standardized column names")
        
        # Parse month to date
        df = df.withColumn('date', to_date(col('month'), 'yyyy-MM'))
        
        # Extract year and month number
        df = df.withColumn('year', year(col('date')))
        df = df.withColumn('month_num', month(col('date')))
        
        # Filter valid temperature range
        df = df.filter(
            (col('temperature').isNotNull()) &
            (col('temperature') >= config.min_temperature) &
            (col('temperature') <= config.max_temperature)
        )
        
        logger.info(f"✓ Filtered temperature range: {config.min_temperature}°C to {config.max_temperature}°C")
        
        # Remove duplicates
        df = df.dropDuplicates()
        
        final_count = df.count()
        logger.info(f"✓ Final record count: {final_count:,}")
        
        # Save as Parquet
        output_path = config.processed_data_path / config.temperature_cleaned
        df.write.mode('overwrite').parquet(str(output_path))
        
        logger.info(f"✓ Saved cleaned data: {output_path}")
        logger.info("="*60)
        logger.info("✓ TEMPERATURE DATA CLEANING COMPLETE (PySpark)")
        logger.info("="*60)
        
        return True, df
        
    except Exception as e:
        logger.error(f"Error cleaning temperature data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None


def clean_all_data_spark() -> bool:
    """
    Clean all datasets using PySpark.
    
    Returns:
        bool: True if all cleaning succeeded
    """
    if not PYSPARK_AVAILABLE:
        logger.error("PySpark not installed. Install with: pip install pyspark")
        return False
    
    logger.info("\n" + "#"*60)
    logger.info("#" + " "*58 + "#")
    logger.info("#" + "  DATA TRANSFORMATION (PySpark)".center(58) + "#")
    logger.info("#" + " "*58 + "#")
    logger.info("#"*60 + "\n")
    
    # Create Spark session
    spark = get_spark_session()
    logger.info("✓ Spark session created")
    logger.info(f"  Spark version: {spark.version}")
    
    # Clean World Cup data
    wc_success, wc_df = clean_worldcup_data_spark(spark)
    if not wc_success:
        logger.error("Failed to clean World Cup data")
        spark.stop()
        return False
    
    # Clean temperature data
    temp_success, temp_df = clean_temperature_data_spark(spark)
    if not temp_success:
        logger.error("Failed to clean temperature data")
        spark.stop()
        return False
    
    # Stop Spark session
    spark.stop()
    logger.info("\n✓ Spark session stopped")
    
    logger.info("\n" + "="*60)
    logger.info("✓ ALL DATA TRANSFORMATION COMPLETE (PySpark)")
    logger.info("="*60)
    
    return True


def main():
    """
    Main entry point for PySpark transformation.
    """
    success = clean_all_data_spark()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
