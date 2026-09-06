"""
Data Enrichment Module - PySpark Version

Enriches World Cup match data with temperature information using PySpark.
Same business logic as Pandas version, different API.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.functions import (
        col, when, avg, count, min as spark_min, max as spark_max,
        median, lit, coalesce
    )
    from pyspark.sql import Window
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
    """
    spark = SparkSession.builder \
        .appName("WorldCupPipeline-Enrichment") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    
    return spark


def prepare_temperature_data_spark(temp_df: DataFrame) -> DataFrame:
    """
    Prepare temperature data for joining (Spark version).
    
    Args:
        temp_df: Temperature Spark DataFrame
    
    Returns:
        Prepared temperature DataFrame
    """
    logger.info("Preparing temperature data for joining (Spark)")
    
    # Check which month column exists
    columns = temp_df.columns
    month_col = 'month_num' if 'month_num' in columns else 'month'
    
    # Group by country, year, month and take mean temperature
    if month_col in columns:
        temp_prepared = temp_df.groupBy('country', 'year', month_col) \
            .agg(avg('temperature').alias('temperature_avg'))
        
        # Rename month column to 'month' for consistency
        if month_col == 'month_num':
            temp_prepared = temp_prepared.withColumnRenamed('month_num', 'month')
        
        logger.info("Using monthly temperature averages")
    else:
        # Only yearly data
        temp_prepared = temp_df.groupBy('country', 'year') \
            .agg(avg('temperature').alias('temperature_avg'))
        
        logger.info("Using yearly temperature averages")
    
    # Rename temperature column for clarity
    temp_prepared = temp_prepared.withColumnRenamed('temperature_avg', 'avg_temperature_celsius')
    
    # Add temperature category
    temp_prepared = temp_prepared.withColumn(
        'temperature_category',
        when(col('avg_temperature_celsius') < 10, 'Cold')
        .when(col('avg_temperature_celsius') < 20, 'Moderate')
        .when(col('avg_temperature_celsius') < 30, 'Warm')
        .otherwise('Hot')
    )
    
    record_count = temp_prepared.count()
    logger.info(f"Prepared {record_count:,} temperature records for joining")
    
    return temp_prepared


def join_temperature_data_spark(
    matches: DataFrame,
    temperature: DataFrame
) -> DataFrame:
    """
    Join match and temperature data (Spark version).
    
    Args:
        matches: Match Spark DataFrame
        temperature: Prepared temperature Spark DataFrame
    
    Returns:
        Joined DataFrame
    """
    logger.info("Joining match and temperature data (Spark)")
    
    # Ensure month columns are integers
    matches_join = matches.withColumn('month', col('month').cast('int'))
    temp_join = temperature.withColumn('month', col('month').cast('int')) if 'month' in temperature.columns else temperature
    
    # Determine join keys
    join_keys = ['country', 'year']
    if 'month' in temp_join.columns and 'month' in matches_join.columns:
        join_keys.append('month')
        logger.info("Performing join on country, year, and month")
    else:
        logger.info("Performing join on country and year")
    
    # Perform left join to keep all matches
    enriched = matches_join.join(
        temp_join,
        on=join_keys,
        how='left'
    )
    
    # Calculate match statistics
    total_matches = enriched.count()
    matched = enriched.filter(col('avg_temperature_celsius').isNotNull()).count()
    match_rate = (matched / total_matches * 100) if total_matches > 0 else 0
    
    logger.info(f"Matched {matched}/{total_matches} matches ({match_rate:.1f}%)")
    
    return enriched


def enrich_data_spark(spark: SparkSession = None) -> Tuple[bool, Optional[DataFrame]]:
    """
    Load cleaned data and perform enrichment using Spark.
    
    Args:
        spark: SparkSession instance (creates new if None)
    
    Returns:
        Tuple of (success: bool, enriched_df: Optional[DataFrame])
    """
    if not PYSPARK_AVAILABLE:
        logger.error("PySpark not installed. Cannot proceed.")
        return False, None
    
    try:
        # Get Spark session
        if spark is None:
            spark = get_spark_session()
        
        logger.info("="*60)
        logger.info("DATA ENRICHMENT (PySpark)")
        logger.info("="*60)
        
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
        matches_df = spark.read.parquet(str(worldcup_path))
        temperature_df = spark.read.parquet(str(temperature_path))
        
        logger.info(f"Loaded {matches_df.count()} matches")
        logger.info(f"Loaded {temperature_df.count():,} temperature records")
        
        # Prepare temperature data
        temp_prepared = prepare_temperature_data_spark(temperature_df)
        
        # Perform enrichment join
        enriched_df = join_temperature_data_spark(matches_df, temp_prepared)
        
        # Generate statistics
        total = enriched_df.count()
        with_temp = enriched_df.filter(col('avg_temperature_celsius').isNotNull()).count()
        match_rate = (with_temp / total * 100) if total > 0 else 0
        
        # Temperature statistics
        temp_stats = enriched_df.filter(col('avg_temperature_celsius').isNotNull()) \
            .agg(
                spark_min('avg_temperature_celsius').alias('min'),
                spark_max('avg_temperature_celsius').alias('max'),
                avg('avg_temperature_celsius').alias('mean')
            ).collect()[0]
        
        # Category distribution
        cat_dist = enriched_df.filter(col('temperature_category').isNotNull()) \
            .groupBy('temperature_category') \
            .count() \
            .orderBy(col('count').desc()) \
            .collect()
        
        logger.info("\nEnrichment Statistics:")
        logger.info(f"  Total matches: {total:,}")
        logger.info(f"  Matches with temperature: {with_temp:,}")
        logger.info(f"  Match rate: {match_rate:.1f}%")
        
        logger.info("\nTemperature Statistics:")
        logger.info(f"  Mean: {temp_stats['mean']:.1f}°C")
        logger.info(f"  Min: {temp_stats['min']:.1f}°C")
        logger.info(f"  Max: {temp_stats['max']:.1f}°C")
        
        logger.info("\nTemperature Distribution:")
        for row in cat_dist:
            logger.info(f"  {row['temperature_category']}: {row['count']:,} matches")
        
        # Save enriched data
        output_path = config.processed_data_path / config.GOLD_ENRICHED_FILE
        enriched_df.write.mode('overwrite').parquet(str(output_path))
        logger.info(f"\nSaved enriched data to {output_path}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ ENRICHMENT COMPLETE (PySpark)")
        logger.info("="*60)
        
        return True, enriched_df
        
    except Exception as e:
        logger.error(f"Error during enrichment: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None
    finally:
        # Stop Spark session gracefully
        if spark is not None:
            try:
                spark.stop()
                logger.debug("Spark session stopped")
            except Exception as e:
                logger.debug(f"Spark shutdown warning: {e}")


def main():
    """
    Main entry point for Spark enrichment.
    """
    success, _ = enrich_data_spark()
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
