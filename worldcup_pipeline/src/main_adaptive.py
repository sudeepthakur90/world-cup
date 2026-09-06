"""
Adaptive Main Pipeline Orchestrator

Automatically selects between Pandas and PySpark based on data size.
This version demonstrates intelligent, self-scaling architecture.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.config import config
from src.utils import setup_logger
from src.utils.adaptive_processor import AdaptiveDataProcessor, DataSizeThresholds

logger = setup_logger(__name__)


class AdaptiveWorldCupPipeline:
    """
    Intelligent pipeline that automatically scales processing engine
    based on data size.
    """
    
    def __init__(self, force_engine: str = None):
        """
        Initialize adaptive pipeline.
        
        Args:
            force_engine: Force specific engine ('pandas', 'spark', or None for auto)
        """
        self.processor = AdaptiveDataProcessor(force_engine=force_engine)
        self.start_time = None
        self.end_time = None
        self.engine_used = None
    
    def run_full_pipeline(self) -> bool:
        """
        Execute the complete adaptive data pipeline.
        
        Returns:
            bool: True if all stages completed successfully
        """
        logger.info("="*80)
        logger.info("ADAPTIVE WORLD CUP DATA PIPELINE")
        logger.info("="*80)
        logger.info("This pipeline intelligently selects Pandas or PySpark")
        logger.info("based on data size for optimal performance.")
        logger.info("="*80)
        
        self.start_time = datetime.now()
        logger.info(f"Pipeline started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Stage 1: Data Ingestion with adaptive engine
            logger.info("\n" + "-"*80)
            logger.info("STAGE 1: ADAPTIVE DATA INGESTION")
            logger.info("-"*80)
            
            if not self._run_adaptive_ingestion():
                return False
            
            # Stage 2: Transformation
            logger.info("\n" + "-"*80)
            logger.info("STAGE 2: DATA TRANSFORMATION")
            logger.info("-"*80)
            
            if not self._run_transformation():
                return False
            
            # Stage 3: Enrichment
            logger.info("\n" + "-"*80)
            logger.info("STAGE 3: DATA ENRICHMENT")
            logger.info("-"*80)
            
            if not self._run_enrichment():
                return False
            
            # Stage 4: Model Building
            logger.info("\n" + "-"*80)
            logger.info("STAGE 4: STAR SCHEMA MODELING")
            logger.info("-"*80)
            
            if not self._run_model_building():
                return False
            
            # Stage 5: Analytics
            logger.info("\n" + "-"*80)
            logger.info("STAGE 5: ANALYTICS EXECUTION")
            logger.info("-"*80)
            
            if not self._run_analytics():
                return False
            
            self._print_summary()
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Clean up Spark session if used
            self.processor.stop_spark()
    
    def _run_adaptive_ingestion(self) -> bool:
        """
        Run ingestion with adaptive engine selection.
        
        Returns:
            bool: Success status
        """
        try:
            from src.ingestion import download_all_data
            
            # Download data files
            if not download_all_data():
                logger.error("Data download failed")
                return False
            
            # Now analyze the downloaded files to determine engine
            worldcup_file = config.raw_data_path / config.worldcup_raw
            
            # Detect optimal engine based on file size
            engine = self.processor.detect_optimal_engine(file_path=worldcup_file)
            self.engine_used = engine
            
            logger.info(f"\n✓ Data ingestion complete")
            logger.info(f"✓ Selected processing engine: {engine.upper()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return False
    
    def _run_transformation(self) -> bool:
        """
        Run transformation using selected engine.
        
        Returns:
            bool: Success status
        """
        try:
            if self.engine_used == 'spark':
                logger.info("Using PySpark for transformation")
                # Import Spark version
                from src.transformation.clean_data_spark import clean_all_data_spark
                return clean_all_data_spark()
            else:
                logger.info("Using Pandas for transformation")
                # Import Pandas version (current)
                from src.transformation import clean_all_data
                return clean_all_data()
                
        except ImportError as e:
            logger.warning(f"Spark version not available: {e}")
            logger.info("Falling back to Pandas")
            from src.transformation import clean_all_data
            return clean_all_data()
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return False
    
    def _run_enrichment(self) -> bool:
        """
        Run enrichment using selected engine.
        
        Returns:
            bool: Success status
        """
        try:
            if self.engine_used == 'spark':
                logger.info("Using PySpark for enrichment")
                from src.enrichment.enrich_data_spark import enrich_data_spark
                success, _ = enrich_data_spark()
                return success
            else:
                logger.info("Using Pandas for enrichment")
                from src.enrichment import enrich_data
                success, _ = enrich_data()
                return success
                
        except ImportError:
            logger.warning("Spark version not available, using Pandas")
            from src.enrichment import enrich_data
            success, _ = enrich_data()
            return success
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            return False
    
    def _run_model_building(self) -> bool:
        """
        Run model building using selected engine.
        
        Returns:
            bool: Success status
        """
        try:
            if self.engine_used == 'spark':
                logger.info("Using PySpark for model building")
                from src.models.build_model_spark import build_and_save_model_spark
                return build_and_save_model_spark()
            else:
                logger.info("Using Pandas for model building")
                from src.models import build_and_save_model
                return build_and_save_model()
                
        except ImportError:
            logger.warning("Spark version not available, using Pandas")
            from src.models import build_and_save_model
            return build_and_save_model()
        except Exception as e:
            logger.error(f"Model building failed: {e}")
            return False
    
    def _run_analytics(self) -> bool:
        """
        Run analytics (same for both engines - SQL!).
        
        Returns:
            bool: Success status
        """
        try:
            from src.analytics import run_all_analytics
            return run_all_analytics()
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return False
    
    def _print_summary(self):
        """
        Print pipeline execution summary.
        """
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        
        logger.info("\n" + "="*80)
        logger.info("ADAPTIVE PIPELINE EXECUTION SUMMARY")
        logger.info("="*80)
        logger.info(f"Engine Selected: {self.engine_used.upper() if self.engine_used else 'N/A'}")
        logger.info(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info("\nOutput Locations:")
        logger.info(f"  Raw Data: {config.raw_data_path}")
        logger.info(f"  Processed Data: {config.processed_data_path}")
        logger.info(f"  Output Data: {config.GOLD_PATH}")
        logger.info(f"  Database: {config.db_url}")
        logger.info(f"  Logs: {config.log_file}")
        logger.info("\n" + "="*80)
        logger.info("✓ ADAPTIVE PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80)


def main():
    """
    CLI entry point with adaptive engine selection.
    """
    parser = argparse.ArgumentParser(
        description='Adaptive World Cup Data Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main_adaptive.py                  # Auto-detect engine based on data size
  python src/main_adaptive.py --engine pandas  # Force Pandas
  python src/main_adaptive.py --engine spark   # Force PySpark
  python src/main_adaptive.py --show-thresholds # Show decision thresholds
        """
    )
    
    parser.add_argument(
        '--engine',
        choices=['auto', 'pandas', 'spark'],
        default='auto',
        help='Processing engine (default: auto-detect based on data size)'
    )
    
    parser.add_argument(
        '--show-thresholds',
        action='store_true',
        help='Show engine selection thresholds and exit'
    )
    
    args = parser.parse_args()
    
    # Show thresholds if requested
    if args.show_thresholds:
        print("\n" + "="*80)
        print("ADAPTIVE ENGINE SELECTION THRESHOLDS")
        print("="*80)
        print(f"\nFile Size Thresholds:")
        print(f"  Small  (Pandas):  < {DataSizeThresholds.MEDIUM_DATA / (1024**2):.0f} MB")
        print(f"  Medium (Pandas):  {DataSizeThresholds.MEDIUM_DATA / (1024**2):.0f} - {DataSizeThresholds.LARGE_DATA / (1024**2):.0f} MB")
        print(f"  Large  (Spark):   > {DataSizeThresholds.LARGE_DATA / (1024**2):.0f} MB")
        print(f"\nRow Count Thresholds:")
        print(f"  Small  (Pandas):  < {DataSizeThresholds.MEDIUM_ROWS:,} rows")
        print(f"  Medium (Pandas):  {DataSizeThresholds.MEDIUM_ROWS:,} - {DataSizeThresholds.LARGE_ROWS:,} rows")
        print(f"  Large  (Spark):   > {DataSizeThresholds.LARGE_ROWS:,} rows")
        print(f"\nMemory Threshold:")
        print(f"  Use Spark if data > {DataSizeThresholds.MEMORY_THRESHOLD * 100:.0f}% of available RAM")
        print("\n" + "="*80 + "\n")
        sys.exit(0)
    
    # Determine engine
    force_engine = None if args.engine == 'auto' else args.engine
    
    # Create and run pipeline
    pipeline = AdaptiveWorldCupPipeline(force_engine=force_engine)
    success = pipeline.run_full_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()