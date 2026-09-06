#!/usr/bin/env python
"""
Transformation Stage Runner

Runs only the data transformation stage (cleaning and validation).
Requires raw data to already be downloaded.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Run transformation stage with engine selection.
    """
    parser = argparse.ArgumentParser(
        description='Run Data Transformation Stage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_transformation.py              # Auto-detect engine
  python run_transformation.py --engine pandas   # Force Pandas
  python run_transformation.py --engine spark    # Force Spark
        """
    )
    
    parser.add_argument(
        '--engine',
        choices=['auto', 'pandas', 'spark'],
        default='auto',
        help='Processing engine (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("  DATA TRANSFORMATION STAGE")
    logger.info("="*70)
    
    # Check if raw data exists
    worldcup_excel = config.raw_data_path / config.worldcup_raw
    worldcup_csv = config.raw_data_path / config.worldcup_raw_csv
    temperature = config.raw_data_path / config.temperature_raw
    
    missing_files = []
    if not worldcup_excel.exists() and not worldcup_csv.exists():
        missing_files.append("WorldCupMatches (Excel or CSV)")
    if not temperature.exists():
        missing_files.append(config.temperature_raw)
    
    if missing_files:
        logger.error("\nRaw data files not found:")
        for file in missing_files:
            logger.error(f"  - {file}")
        logger.error("\nPlease run ingestion first:")
        logger.error("  python run_ingestion.py")
        return False
    
    logger.info("\n✓ Raw data files found")
    
    # Determine engine
    if args.engine == 'auto':
        # Auto-detect based on file size
        from src.utils.adaptive_processor import AdaptiveDataProcessor
        processor = AdaptiveDataProcessor()
        engine = processor.detect_optimal_engine(file_path=worldcup_excel)
        logger.info(f"\nAuto-detected engine: {engine.upper()}")
    else:
        engine = args.engine
        logger.info(f"\nUsing forced engine: {engine.upper()}")
    
    # Run transformation
    try:
        if engine == 'spark':
            logger.info("\nRunning transformation with PySpark...\n")
            from src.transformation.clean_data_spark import clean_all_data_spark
            success = clean_all_data_spark()
        else:
            logger.info("\nRunning transformation with Pandas...\n")
            from src.transformation.clean_data import clean_all_data
            success = clean_all_data()
        
        if success:
            logger.info("\n" + "="*70)
            logger.info("✓ TRANSFORMATION STAGE COMPLETE")
            logger.info("="*70)
            logger.info(f"\nCleaned data saved to: {config.processed_data_path}")
            logger.info("\nNext steps:")
            logger.info("  python run_enrichment.py     # (if you create it)")
            logger.info("  python run_adaptive_pipeline.py  # (run all stages)")
            return True
        else:
            logger.error("\n✗ Transformation failed")
            return False
            
    except ImportError as e:
        if 'pyspark' in str(e).lower() and engine == 'spark':
            logger.error("\nPySpark not installed!")
            logger.error("Install with: pip install pyspark")
            logger.error("\nOr use Pandas: python run_transformation.py --engine pandas")
            return False
        else:
            logger.error(f"\nImport error: {e}")
            return False
    except Exception as e:
        logger.error(f"\nTransformation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
