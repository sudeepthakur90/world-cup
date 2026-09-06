"""
Data Model Module - PySpark Version

Builds star schema data model for analytics using PySpark.
Creates fact and dimension tables optimized for BI.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pyspark.sql import DataFrame, SparkSession, Window
    from pyspark.sql.functions import (
        col, lit, row_number, monotonically_increasing_id,
        year as spark_year, month as spark_month, dayofmonth,
        dayofweek, quarter, concat, when, coalesce
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
    """
    spark = SparkSession.builder \
        .appName("WorldCupPipeline-Modeling") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    
    return spark


def build_dim_date_spark(df: DataFrame) -> DataFrame:
    """
    Build date dimension table (Spark version).
    
    Args:
        df: Source Spark DataFrame
    
    Returns:
        Date dimension DataFrame
    """
    logger.info("Building dim_date (Spark)")
    
    # Extract date components
    if 'match_date' in df.columns:
        dates = df.select('match_date').distinct()
        
        dim_date = dates.withColumn('date_id', row_number().over(Window.orderBy('match_date'))) \
            .withColumn('year', spark_year(col('match_date'))) \
            .withColumn('month', spark_month(col('match_date'))) \
            .withColumn('day', dayofmonth(col('match_date'))) \
            .withColumn('day_of_week', dayofweek(col('match_date'))) \
            .withColumn('quarter', quarter(col('match_date'))) \
            .withColumn('full_date', col('match_date'))
    else:
        # Fallback if match_date doesn't exist
        logger.warning("match_date not found, using year/month")
        dates = df.select('year', 'month').distinct()
        
        dim_date = dates.withColumn('date_id', row_number().over(Window.orderBy('year', 'month'))) \
            .withColumn('day', lit(1)) \
            .withColumn('day_of_week', lit(None)) \
            .withColumn('quarter', ((col('month') - 1) / 3 + 1).cast('int'))
    
    logger.info(f"Built dim_date with {dim_date.count()} records")
    return dim_date


def build_dim_team_spark(df: DataFrame) -> DataFrame:
    """
    Build team dimension table (Spark version).
    
    Args:
        df: Source Spark DataFrame
    
    Returns:
        Team dimension DataFrame
    """
    logger.info("Building dim_team (Spark)")
    
    # Get unique teams from both home and away
    home_teams = df.select(
        col('home_team').alias('team_name'),
        col('country').alias('team_country')
    ).distinct()
    
    away_teams = df.select(
        col('away_team').alias('team_name'),
        col('country').alias('team_country')
    ).distinct()
    
    # Union and deduplicate
    all_teams = home_teams.union(away_teams).distinct()
    
    # Add team_id
    dim_team = all_teams.withColumn(
        'team_id',
        row_number().over(Window.orderBy('team_name'))
    )
    
    logger.info(f"Built dim_team with {dim_team.count()} records")
    return dim_team


def build_dim_location_spark(df: DataFrame) -> DataFrame:
    """
    Build location dimension table (Spark version).
    
    Args:
        df: Source Spark DataFrame
    
    Returns:
        Location dimension DataFrame
    """
    logger.info("Building dim_location (Spark)")
    
    # Get unique locations
    locations = df.select(
        coalesce(col('city'), lit('Unknown')).alias('city'),
        coalesce(col('stadium'), lit('Unknown')).alias('stadium'),
        coalesce(col('country'), lit('Unknown')).alias('country')
    ).distinct()
    
    # Add location_id
    dim_location = locations.withColumn(
        'location_id',
        row_number().over(Window.orderBy('country', 'city', 'stadium'))
    )
    
    logger.info(f"Built dim_location with {dim_location.count()} records")
    return dim_location


def build_dim_temperature_spark(df: DataFrame) -> DataFrame:
    """
    Build temperature dimension table (Spark version).
    
    Args:
        df: Source Spark DataFrame
    
    Returns:
        Temperature dimension DataFrame
    """
    logger.info("Building dim_temperature (Spark)")
    
    # Get unique temperature combinations
    temps = df.select(
        'avg_temperature_celsius',
        'temperature_category'
    ).distinct().filter(col('avg_temperature_celsius').isNotNull())
    
    # Add temperature_id
    dim_temperature = temps.withColumn(
        'temperature_id',
        row_number().over(Window.orderBy('avg_temperature_celsius'))
    )
    
    logger.info(f"Built dim_temperature with {dim_temperature.count()} records")
    return dim_temperature


def build_fact_matches_spark(
    df: DataFrame,
    dim_date: DataFrame,
    dim_team: DataFrame,
    dim_location: DataFrame,
    dim_temperature: DataFrame
) -> DataFrame:
    """
    Build fact matches table (Spark version).
    
    Args:
        df: Source enriched DataFrame
        dim_date: Date dimension
        dim_team: Team dimension
        dim_location: Location dimension
        dim_temperature: Temperature dimension
    
    Returns:
        Fact matches DataFrame
    """
    logger.info("Building fact_matches (Spark)")
    
    # Start with enriched data
    fact = df
    
    # Join with date dimension
    if 'match_date' in fact.columns:
        fact = fact.join(
            dim_date.select('date_id', 'full_date'),
            fact['match_date'] == dim_date['full_date'],
            'left'
        )
    else:
        # Join on year/month
        fact = fact.join(
            dim_date.select('date_id', 'year', 'month'),
            ['year', 'month'],
            'left'
        )
    
    # Join with home team
    fact = fact.join(
        dim_team.select(
            col('team_id').alias('home_team_id'),
            col('team_name').alias('ht_name')
        ),
        fact['home_team'] == col('ht_name'),
        'left'
    ).drop('ht_name')
    
    # Join with away team
    fact = fact.join(
        dim_team.select(
            col('team_id').alias('away_team_id'),
            col('team_name').alias('at_name')
        ),
        fact['away_team'] == col('at_name'),
        'left'
    ).drop('at_name')
    
    # Join with location
    fact = fact.join(
        dim_location.select('location_id', 'city', 'stadium', 'country'),
        ['city', 'stadium', 'country'],
        'left'
    )
    
    # Join with temperature
    fact = fact.join(
        dim_temperature.select('temperature_id', 'avg_temperature_celsius'),
        ['avg_temperature_celsius'],
        'left'
    )
    
    # Add match_id
    fact = fact.withColumn(
        'match_id',
        row_number().over(Window.orderBy('year', 'match_date'))
    )
    
    # Select final columns
    fact_matches = fact.select(
        'match_id',
        'date_id',
        'home_team_id',
        'away_team_id',
        'location_id',
        'temperature_id',
        col('home_goals').alias('home_score'),
        col('away_goals').alias('away_score'),
        when(col('home_goals') > col('away_goals'), 'Home')
        .when(col('home_goals') < col('away_goals'), 'Away')
        .otherwise('Draw').alias('match_result'),
        coalesce(col('round'), lit('Unknown')).alias('round'),
        'year'
    )
    
    logger.info(f"Built fact_matches with {fact_matches.count()} records")
    return fact_matches


def build_star_schema_spark(
    spark: SparkSession,
    enriched_df: DataFrame
) -> Dict[str, DataFrame]:
    """
    Build complete star schema from enriched data (Spark version).
    
    Args:
        spark: SparkSession
        enriched_df: Enriched match DataFrame
    
    Returns:
        Dictionary of table name -> DataFrame
    """
    logger.info("Building star schema (Spark)")
    
    # Build dimension tables
    dim_date = build_dim_date_spark(enriched_df)
    dim_team = build_dim_team_spark(enriched_df)
    dim_location = build_dim_location_spark(enriched_df)
    dim_temperature = build_dim_temperature_spark(enriched_df)
    
    # Build fact table
    fact_matches = build_fact_matches_spark(
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
    
    logger.info("Star schema built successfully (Spark)")
    log_schema_stats_spark(tables)
    
    return tables


def log_schema_stats_spark(tables: Dict[str, DataFrame]):
    """
    Log star schema statistics (Spark version).
    
    Args:
        tables: Dictionary of table DataFrames
    """
    logger.info("\nStar Schema Statistics (Spark):")
    for table_name, df in tables.items():
        count = df.count()
        logger.info(f"  {table_name}: {count:,} records")


def save_to_database_spark(tables: Dict[str, DataFrame], db_url: str):
    """
    Save tables to SQLite database (Spark version).
    
    Args:
        tables: Dictionary of table DataFrames
        db_url: Database URL
    """
    logger.info(f"Saving tables to database (Spark): {db_url}")
    
    # Extract JDBC URL from SQLAlchemy URL
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        jdbc_url = f"jdbc:sqlite:{db_path}"
    else:
        jdbc_url = db_url
    
    for table_name, df in tables.items():
        try:
            # Convert to Pandas for SQLite (Spark JDBC for SQLite is limited)
            pandas_df = df.toPandas()
            
            from sqlalchemy import create_engine
            engine = create_engine(db_url)
            
            pandas_df.to_sql(
                table_name,
                engine,
                if_exists='replace',
                index=False
            )
            logger.info(f"Saved {table_name} ({len(pandas_df)} records)")
        except Exception as e:
            logger.error(f"Error saving {table_name}: {e}")
    
    logger.info("Database save complete (Spark)")


def save_to_files_spark(tables: Dict[str, DataFrame], output_dir: Path):
    """
    Save tables to parquet files (Spark version).
    
    Args:
        tables: Dictionary of table DataFrames
        output_dir: Output directory path
    """
    logger.info(f"Saving tables to {output_dir} (Spark)")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for table_name, df in tables.items():
        output_path = output_dir / f"{table_name}.parquet"
        df.write.mode('overwrite').parquet(str(output_path))
        logger.info(f"Saved {table_name} to {output_path}")
    
    logger.info("File save complete (Spark)")


def build_and_save_model_spark(spark: SparkSession = None) -> Tuple[bool, Optional[Dict[str, DataFrame]]]:
    """
    Build star schema model and save to database and files (Spark version).
    
    Args:
        spark: SparkSession (creates new if None)
    
    Returns:
        Tuple of (success: bool, tables: Optional[Dict])
    """
    if not PYSPARK_AVAILABLE:
        logger.error("PySpark not installed. Cannot proceed.")
        return False, None
    
    try:
        # Get Spark session
        if spark is None:
            spark = get_spark_session()
        
        logger.info("="*60)
        logger.info("DATA MODELING (PySpark)")
        logger.info("="*60)
        
        # Load enriched data
        enriched_path = config.processed_data_path / config.GOLD_ENRICHED_FILE
        
        if not enriched_path.exists():
            logger.error(f"Enriched data not found: {enriched_path}")
            return False, None
        
        logger.info(f"Loading enriched data from {enriched_path}")
        enriched_df = spark.read.parquet(str(enriched_path))
        logger.info(f"Loaded {enriched_df.count()} enriched records")
        
        # Build star schema
        tables = build_star_schema_spark(spark, enriched_df)
        
        # Save to database
        from src.config import get_database_url
        db_url = get_database_url()
        save_to_database_spark(tables, db_url)
        
        # Save to files
        save_to_files_spark(tables, config.GOLD_PATH)
        
        logger.info("\n" + "="*60)
        logger.info("✓ MODEL BUILD COMPLETE (PySpark)")
        logger.info("="*60)
        
        return True, tables
        
    except Exception as e:
        logger.error(f"Error building model (Spark): {e}")
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
    Main entry point for Spark modeling.
    """
    success, _ = build_and_save_model_spark()
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
