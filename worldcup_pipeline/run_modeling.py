#!/usr/bin/env python
"""
Modeling Stage Runner

Runs only the data modeling stage (Star Schema build).
Requires enriched data to already exist.
Supports both Pandas and PySpark engines.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
from src.config import config, get_database_url
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Run modeling stage.
    """
    parser = argparse.ArgumentParser(
        description='Run Data Modeling Stage (Star Schema)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_modeling.py                   # Auto-detect engine (Pandas)
  python run_modeling.py --engine pandas   # Use Pandas
  python run_modeling.py --engine spark    # Use PySpark
        """
    )
    
    parser.add_argument(
        '--engine',
        choices=['pandas', 'spark', 'auto'],
        default='auto',
        help='Processing engine: pandas, spark, or auto (default: auto)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("  DATA MODELING STAGE (Star Schema)")
    logger.info("="*70)
    
    # Check if enriched data exists
    enriched_file = config.processed_data_path / "worldcup_enriched.parquet"
    
    if not enriched_file.exists():
        logger.error("\nEnriched data file not found:")
        logger.error(f"  - {enriched_file}")
        logger.error("\nPlease run enrichment first:")
        logger.error("  python run_enrichment.py")
        logger.error("\nOr run full pipeline:")
        logger.error("  python run_adaptive_pipeline.py")
        return False
    
    logger.info("\n✓ Enriched data file found")
    logger.info(f"  - {enriched_file.name}")
    
    # Determine engine
    engine = args.engine
    if engine == 'auto':
        # Use Pandas by default (simpler, works with SQLite)
        engine = 'pandas'
        logger.info(f"Auto-selected engine: {engine}")
    
    logger.info(f"\nUsing engine: {engine.upper()}")
    
    # Show database info
    db_url = get_database_url()
    logger.info(f"Database: {db_url}")
    logger.info(f"Output: {config.GOLD_PATH}")
    
    # Run modeling
    try:
        logger.info("\nBuilding Star Schema...\n")
        
        if engine == 'spark':
            from src.models.build_model_spark import build_and_save_model_spark
            success, tables = build_and_save_model_spark()
        else:  # pandas
            from src.models.build_model import build_and_save_model
            success = build_and_save_model()
            tables = None
        
        if success:
            logger.info("\n" + "="*70)
            logger.info("✓ MODELING STAGE COMPLETE")
            logger.info("="*70)
            
            # Show model statistics (Pandas only, Spark already shows)
            if engine == 'pandas':
                try:
                    # Read back from database to show stats
                    from sqlalchemy import create_engine, inspect
                    
                    engine_db = create_engine(db_url)
                    inspector = inspect(engine_db)
                    table_names = inspector.get_table_names()
                    
                    logger.info("\nStar Schema Tables:")
                    
                    import pandas as pd
                    for table_name in sorted(table_names):
                        df = pd.read_sql_table(table_name, engine_db)
                        logger.info(f"  {table_name}: {len(df):,} records")
                    
                    logger.info("\nSchema Structure:")
                    logger.info("  Fact Table:")
                    logger.info("    - fact_matches (central fact table)")
                    logger.info("  Dimension Tables:")
                    logger.info("    - dim_date (temporal dimension)")
                    logger.info("    - dim_team (team dimension)")
                    logger.info("    - dim_location (location dimension)")
                    logger.info("    - dim_temperature (climate dimension)")
                    
                except Exception as e:
                    logger.debug(f"Could not display statistics: {e}")
            elif engine == 'spark':
                logger.info("\n(Statistics already displayed by Spark modeling module)")
            
            logger.info(f"\nDatabase saved to: {config.GOLD_PATH}")
            logger.info("  - worldcup_analytics.db (SQLite)")
            
            logger.info(f"\nParquet files saved to: {config.GOLD_PATH}")
            logger.info("  - dim_date.parquet")
            logger.info("  - dim_team.parquet")
            logger.info("  - dim_location.parquet")
            logger.info("  - dim_temperature.parquet")
            logger.info("  - fact_matches.parquet")
            
            logger.info(f"\nEngine used: {engine.upper()}")
            
            logger.info("\nNext steps:")
            logger.info("  python run_analytics.py        # (if you create it)")
            logger.info("  python run_adaptive_pipeline.py  # (run all stages)")
            logger.info("  python run_modeling.py --engine [pandas|spark]  # (switch engine)")
            
            logger.info("\nQuery the database:")
            logger.info("  sqlite3 data/output/worldcup_analytics.db")
            logger.info("  .tables")
            logger.info("  SELECT * FROM fact_matches LIMIT 10;")
            
            return True
        else:
            logger.error("\n✗ Modeling failed")
            return False
            
    except Exception as e:
        logger.error(f"\nModeling error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("\nTip: Try switching engine:")
        logger.error(f"  python run_modeling.py --engine {'pandas' if engine == 'spark' else 'spark'}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
