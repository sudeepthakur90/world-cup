#!/usr/bin/env python
"""
Enrichment Stage Runner

Runs only the data enrichment stage (temperature matching).
Requires cleaned data to already exist.
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
    Run enrichment stage.
    """
    parser = argparse.ArgumentParser(
        description='Run Data Enrichment Stage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enrichment.py                   # Auto-detect engine
  python run_enrichment.py --engine pandas   # Use Pandas
  python run_enrichment.py --engine spark    # Use PySpark
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
    logger.info("  DATA ENRICHMENT STAGE")
    logger.info("="*70)
    
    # Check if cleaned data exists
    worldcup_cleaned = config.processed_data_path / config.worldcup_cleaned
    temperature_cleaned = config.processed_data_path / config.temperature_cleaned
    
    missing_files = []
    if not worldcup_cleaned.exists():
        missing_files.append(config.worldcup_cleaned)
    if not temperature_cleaned.exists():
        missing_files.append(config.temperature_cleaned)
    
    if missing_files:
        logger.error("\nCleaned data files not found:")
        for file in missing_files:
            logger.error(f"  - {file}")
        logger.error("\nPlease run transformation first:")
        logger.error("  python run_transformation.py")
        logger.error("\nOr run full pipeline:")
        logger.error("  python run_adaptive_pipeline.py")
        return False
    
    logger.info("\n✓ Cleaned data files found")
    logger.info(f"  - {worldcup_cleaned.name}")
    logger.info(f"  - {temperature_cleaned.name}")
    
    # Determine engine
    engine = args.engine
    if engine == 'auto':
        # Use Pandas by default (simpler, faster for this data size)
        engine = 'pandas'
        logger.info(f"Auto-selected engine: {engine}")
    
    logger.info(f"\nUsing engine: {engine.upper()}")
    
    # Run enrichment
    try:
        logger.info("\nRunning temperature enrichment...\n")
        
        if engine == 'spark':
            from src.enrichment.enrich_data_spark import enrich_data_spark
            success, enriched_df = enrich_data_spark()
        else:  # pandas
            from src.enrichment import enrich_data
            success, enriched_df = enrich_data()
        
        if success:
            logger.info("\n" + "="*70)
            logger.info("✓ ENRICHMENT STAGE COMPLETE")
            logger.info("="*70)
            
            # Show enrichment statistics (only for Pandas - Spark already shows stats)
            if enriched_df is not None and engine == 'pandas':
                try:
                    total_matches = len(enriched_df)
                    
                    # Check which temperature column exists
                    temp_col = 'avg_temperature_celsius' if 'avg_temperature_celsius' in enriched_df.columns else 'temperature'
                    
                    matches_with_temp = enriched_df[temp_col].notna().sum()
                    match_rate = (matches_with_temp / total_matches * 100) if total_matches > 0 else 0
                    
                    logger.info(f"\nEnrichment Statistics:")
                    logger.info(f"  Total matches: {total_matches:,}")
                    logger.info(f"  Matches with temperature: {matches_with_temp:,}")
                    logger.info(f"  Match rate: {match_rate:.1f}%")
                    
                    if temp_col in enriched_df.columns:
                        temp_stats = enriched_df[temp_col].describe()
                        logger.info(f"\nTemperature Statistics:")
                        logger.info(f"  Mean: {temp_stats['mean']:.1f}°C")
                        logger.info(f"  Min: {temp_stats['min']:.1f}°C")
                        logger.info(f"  Max: {temp_stats['max']:.1f}°C")
                        
                        # Show temperature distribution if category exists
                        if 'temperature_category' in enriched_df.columns:
                            logger.info(f"\nTemperature Distribution:")
                            cat_dist = enriched_df['temperature_category'].value_counts().to_dict()
                            for category, count in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True):
                                logger.info(f"  {category}: {count:,} matches")
                except Exception as e:
                    logger.debug(f"Could not display statistics: {e}")
            elif engine == 'spark':
                logger.info("\n(Statistics already displayed by Spark enrichment module)")
            
            logger.info(f"\nEnriched data saved to: {config.processed_data_path}")
            logger.info("  - worldcup_enriched.parquet")
            
            logger.info(f"\nEngine used: {engine.upper()}")
            
            logger.info("\nNext steps:")
            logger.info("  python run_modeling.py         # (if you create it)")
            logger.info("  python run_adaptive_pipeline.py  # (run all stages)")
            logger.info("  python run_enrichment.py --engine [pandas|spark]  # (switch engine)")
            
            return True
        else:
            logger.error("\n✗ Enrichment failed")
            return False
            
    except Exception as e:
        logger.error(f"\nEnrichment error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("\nTip: Try switching engine:")
        logger.error(f"  python run_enrichment.py --engine {'pandas' if engine == 'spark' else 'spark'}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
