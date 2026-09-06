"""
Adaptive Data Processor

Automatically selects between Pandas and PySpark based on data size.
This demonstrates intelligent architecture that scales automatically.
"""

import os
from pathlib import Path
from typing import Union, Optional, Tuple
import pandas as pd

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


class DataSizeThresholds:
    """
    Define thresholds for automatic Pandas vs PySpark selection.
    """
    # File size thresholds (in bytes)
    SMALL_DATA = 5 * 1024 * 1024        # 5 MB - Use Pandas
    MEDIUM_DATA = 500 * 1024 * 1024     # 500 MB - Use Pandas with chunking
    LARGE_DATA = 5 * 1024 * 1024 * 1024 # 5 GB - Use PySpark
    
    # Row count thresholds
    SMALL_ROWS = 100_000      # < 100K rows - Pandas
    MEDIUM_ROWS = 1_000_000   # 100K-1M rows - Pandas
    LARGE_ROWS = 10_000_000   # > 1M rows - Consider PySpark
    HUGE_ROWS = 50_000_000    # > 10M rows - Definitely PySpark
    
    # Memory thresholds (percentage of available RAM)
    MEMORY_THRESHOLD = 0.6    # If data > 60% of RAM, use Spark


class AdaptiveDataProcessor:
    """
    Intelligent data processor that automatically selects
    between Pandas and PySpark based on data characteristics.
    """
    
    def __init__(self, force_engine: Optional[str] = None):
        """
        Initialize adaptive processor.
        
        Args:
            force_engine: Force specific engine ('pandas' or 'spark')
                         If None, auto-detect based on data size
        """
        self.force_engine = force_engine
        self.spark_session = None
        self.engine_used = None
        
    def detect_optimal_engine(
        self,
        file_path: Optional[Path] = None,
        estimated_rows: Optional[int] = None,
        estimated_size_mb: Optional[float] = None
    ) -> str:
        """
        Detect optimal processing engine based on data characteristics.
        
        Args:
            file_path: Path to data file (for size detection)
            estimated_rows: Estimated number of rows
            estimated_size_mb: Estimated data size in MB
        
        Returns:
            'pandas' or 'spark'
        """
        # If engine is forced, use that
        if self.force_engine:
            logger.info(f"Using forced engine: {self.force_engine}")
            return self.force_engine
        
        # Get data size metrics
        file_size_bytes = 0
        if file_path and file_path.exists():
            file_size_bytes = file_path.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Decision logic
        reasons = []
        spark_score = 0
        pandas_score = 0
        
        # Check 1: File size
        if file_size_bytes > 0:
            if file_size_bytes < DataSizeThresholds.MEDIUM_DATA:
                pandas_score += 3
                reasons.append(f"File size ({file_size_mb:.2f} MB) < 500 MB")
            elif file_size_bytes < DataSizeThresholds.LARGE_DATA:
                pandas_score += 1
                spark_score += 1
                reasons.append(f"File size ({file_size_mb:.2f} MB) in medium range")
            else:
                spark_score += 3
                reasons.append(f"File size ({file_size_mb:.2f} MB) > 5 GB")
        
        # Check 2: Row count
        if estimated_rows:
            if estimated_rows < DataSizeThresholds.MEDIUM_ROWS:
                pandas_score += 2
                reasons.append(f"Estimated rows ({estimated_rows:,}) < 1M")
            elif estimated_rows < DataSizeThresholds.LARGE_ROWS:
                pandas_score += 1
                spark_score += 1
                reasons.append(f"Estimated rows ({estimated_rows:,}) in medium range")
            else:
                spark_score += 2
                reasons.append(f"Estimated rows ({estimated_rows:,}) > 10M")
        
        # Check 3: Estimated size
        if estimated_size_mb:
            if estimated_size_mb < 500:
                pandas_score += 2
                reasons.append(f"Estimated size ({estimated_size_mb:.2f} MB) < 500 MB")
            elif estimated_size_mb < 5000:
                pandas_score += 1
                spark_score += 1
                reasons.append(f"Estimated size ({estimated_size_mb:.2f} MB) in medium range")
            else:
                spark_score += 2
                reasons.append(f"Estimated size ({estimated_size_mb:.2f} MB) > 5 GB")
        
        # Check 4: Available memory
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            
            if file_size_bytes > 0:
                file_size_gb = file_size_bytes / (1024**3)
                memory_ratio = file_size_gb / available_memory_gb
                
                if memory_ratio < 0.3:
                    pandas_score += 2
                    reasons.append(f"Data uses {memory_ratio*100:.1f}% of available RAM")
                elif memory_ratio < 0.6:
                    pandas_score += 1
                    spark_score += 1
                    reasons.append(f"Data uses {memory_ratio*100:.1f}% of available RAM")
                else:
                    spark_score += 3
                    reasons.append(f"Data uses {memory_ratio*100:.1f}% of available RAM - too high")
        except ImportError:
            logger.warning("psutil not available, skipping memory check")
        
        # Make decision
        if spark_score > pandas_score:
            engine = 'spark'
        else:
            engine = 'pandas'
        
        # Log decision
        logger.info(f"\n{'='*60}")
        logger.info("ADAPTIVE ENGINE SELECTION")
        logger.info(f"{'='*60}")
        logger.info(f"Pandas Score: {pandas_score}")
        logger.info(f"Spark Score:  {spark_score}")
        logger.info(f"\nReasons:")
        for reason in reasons:
            logger.info(f"  - {reason}")
        logger.info(f"\nSelected Engine: {engine.upper()}")
        logger.info(f"{'='*60}\n")
        
        self.engine_used = engine
        return engine
    
    def read_data(
        self,
        file_path: Path,
        file_format: str = 'auto',
        **kwargs
    ) -> Union[pd.DataFrame, 'pyspark.sql.DataFrame']:
        """
        Read data using optimal engine.
        
        Args:
            file_path: Path to data file
            file_format: File format ('excel', 'csv', 'parquet', 'auto')
            **kwargs: Additional arguments for read function
        
        Returns:
            DataFrame (Pandas or PySpark)
        """
        # Auto-detect format
        if file_format == 'auto':
            suffix = file_path.suffix.lower()
            format_map = {
                '.xlsx': 'excel',
                '.xls': 'excel',
                '.csv': 'csv',
                '.parquet': 'parquet',
                '.json': 'json'
            }
            file_format = format_map.get(suffix, 'csv')
        
        # Detect optimal engine
        engine = self.detect_optimal_engine(file_path=file_path)
        
        if engine == 'pandas':
            return self._read_with_pandas(file_path, file_format, **kwargs)
        else:
            return self._read_with_spark(file_path, file_format, **kwargs)
    
    def _read_with_pandas(self, file_path: Path, file_format: str, **kwargs) -> pd.DataFrame:
        """
        Read data using Pandas.
        """
        logger.info(f"Reading with Pandas: {file_path}")
        
        if file_format == 'excel':
            return pd.read_excel(file_path, **kwargs)
        elif file_format == 'csv':
            return pd.read_csv(file_path, **kwargs)
        elif file_format == 'parquet':
            return pd.read_parquet(file_path, **kwargs)
        elif file_format == 'json':
            return pd.read_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    def _read_with_spark(self, file_path: Path, file_format: str, **kwargs):
        """
        Read data using PySpark.
        """
        logger.info(f"Reading with PySpark: {file_path}")
        
        # Initialize Spark if not already done
        if not self.spark_session:
            self.spark_session = self._get_spark_session()
        
        spark = self.spark_session
        
        if file_format == 'excel':
            # Excel not natively supported in Spark, convert to CSV first
            logger.warning("Excel not supported in Spark, converting to CSV first")
            df_pandas = pd.read_excel(file_path, **kwargs)
            csv_path = file_path.with_suffix('.csv')
            df_pandas.to_csv(csv_path, index=False)
            return spark.read.csv(str(csv_path), header=True, inferSchema=True)
        elif file_format == 'csv':
            return spark.read.csv(str(file_path), header=True, inferSchema=True, **kwargs)
        elif file_format == 'parquet':
            return spark.read.parquet(str(file_path), **kwargs)
        elif file_format == 'json':
            return spark.read.json(str(file_path), **kwargs)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    def _get_spark_session(self):
        """
        Create or get Spark session.
        """
        try:
            from pyspark.sql import SparkSession
            
            spark = SparkSession.builder \
                .appName("AdaptiveWorldCupPipeline") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.executor.memory", "4g") \
                .config("spark.driver.memory", "2g") \
                .getOrCreate()
            
            logger.info("Spark session created successfully")
            return spark
        except ImportError:
            logger.error("PySpark not installed. Install with: pip install pyspark")
            raise
    
    def write_data(
        self,
        df: Union[pd.DataFrame, 'pyspark.sql.DataFrame'],
        output_path: Path,
        file_format: str = 'parquet',
        **kwargs
    ):
        """
        Write data using appropriate engine.
        
        Args:
            df: DataFrame (Pandas or PySpark)
            output_path: Output file path
            file_format: Output format
            **kwargs: Additional write arguments
        """
        # Detect if it's Pandas or Spark DataFrame
        if isinstance(df, pd.DataFrame):
            logger.info(f"Writing with Pandas to {output_path}")
            if file_format == 'parquet':
                df.to_parquet(output_path, **kwargs)
            elif file_format == 'csv':
                df.to_csv(output_path, **kwargs)
            else:
                raise ValueError(f"Unsupported format: {file_format}")
        else:
            # Assume it's a Spark DataFrame
            logger.info(f"Writing with Spark to {output_path}")
            if file_format == 'parquet':
                df.write.parquet(str(output_path), **kwargs)
            elif file_format == 'csv':
                df.write.csv(str(output_path), header=True, **kwargs)
            else:
                raise ValueError(f"Unsupported format: {file_format}")
    
    def stop_spark(self):
        """
        Stop Spark session if running.
        """
        if self.spark_session:
            self.spark_session.stop()
            logger.info("Spark session stopped")


def get_processor(force_engine: Optional[str] = None) -> AdaptiveDataProcessor:
    """
    Factory function to create adaptive processor.
    
    Args:
        force_engine: Force specific engine ('pandas', 'spark', or None for auto)
    
    Returns:
        AdaptiveDataProcessor instance
    """
    return AdaptiveDataProcessor(force_engine=force_engine)


if __name__ == "__main__":
    # Example usage
    processor = AdaptiveDataProcessor()
    
    # Simulate different data sizes
    test_cases = [
        {"estimated_rows": 10_000, "estimated_size_mb": 5, "expected": "pandas"},
        {"estimated_rows": 500_000, "estimated_size_mb": 300, "expected": "pandas"},
        {"estimated_rows": 5_000_000, "estimated_size_mb": 2000, "expected": "spark"},
        {"estimated_rows": 50_000_000, "estimated_size_mb": 10000, "expected": "spark"},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        engine = processor.detect_optimal_engine(
            estimated_rows=test["estimated_rows"],
            estimated_size_mb=test["estimated_size_mb"]
        )
        assert engine == test["expected"], f"Expected {test['expected']}, got {engine}"
        print(f"✓ Correctly selected {engine}")