"""
Data Ingestion Module

Downloads World Cup and temperature data from remote sources.
Includes multiple sources, retry logic, error handling, and data validation.
"""

import sys
import time
import zipfile
import io
from pathlib import Path
from typing import Optional, Tuple, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


# Data source URLs - Official sources only
WORLDCUP_SOURCES = [
    {
        "url": "https://public.tableau.com/app/sample-data/world_cup_results.xlsx",
        "name": "Tableau Public",
        "format": "excel"
    }
]

TEMPERATURE_SOURCES = [
    {
        "url": "https://ourworldindata.org/grapher/average-monthly-surface-temperature.zip?v=1&csvType=full&useColumnShortNames=false",
        "name": "Our World in Data",
        "format": "zip"
    }
]


class DataDownloader:
    """
    Handles downloading of datasets with retry logic and error handling.
    """
    
    def __init__(self, max_retries: int = None, timeout: int = None):
        """
        Initialize downloader with configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries or config.max_retries
        self.timeout = timeout or config.timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry strategy.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def download_file(
        self,
        url: str,
        destination: Path,
        description: str = "file"
    ) -> Tuple[bool, Optional[str]]:
        """
        Download a file from URL to destination path.
        
        Args:
            url: Source URL
            destination: Destination file path
            description: Human-readable description for logging
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info(f"Downloading {description} from {url}")
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with streaming for large files
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Write file in chunks
            downloaded_size = 0
            chunk_size = 8192
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (chunk_size * 100) == 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.debug(f"Download progress: {progress:.1f}%")
            
            logger.info(f"✓ Successfully downloaded {description} to {destination}")
            logger.info(f"  File size: {downloaded_size / (1024*1024):.2f} MB")
            
            return True, None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to download {description}: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
        
        except IOError as e:
            error_msg = f"Failed to write {description} to disk: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected error downloading {description}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        

def download_worldcup_data() -> Tuple[bool, Optional[Path]]:
    """
    Download World Cup dataset from Tableau Public.
    Saves in both Excel and CSV formats for Pandas/Spark compatibility.
    
    Returns:
        Tuple of (success: bool, file_path: Optional[Path])
    """
    downloader = DataDownloader()
    excel_dest = config.raw_data_path / config.worldcup_raw
    csv_dest = config.raw_data_path / "WorldCupMatches.csv"
    source = WORLDCUP_SOURCES[0]  # Only one source
    
    logger.info("="*60)
    logger.info("DOWNLOADING WORLD CUP DATASET")
    logger.info("="*60)
    logger.info(f"Source: {source['name']}")
    logger.info(f"Format: Excel (.xlsx) + CSV for Spark compatibility")
    
    # Download the Excel file
    success, error = downloader.download_file(
        source['url'],
        excel_dest,
        "World Cup Matches (1930-2014)"
    )
    
    if success:
        # Validate and convert to CSV for Spark compatibility
        try:
            # Read and validate Excel
            df = pd.read_excel(excel_dest)
            logger.info(f"✓ Validation: {len(df)} records loaded")
            logger.info(f"✓ Columns: {list(df.columns)[:5]}...")
            
            # Save as CSV for Spark compatibility
            df.to_csv(csv_dest, index=False)
            csv_size_mb = csv_dest.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Saved CSV version for Spark: {csv_dest.name} ({csv_size_mb:.2f} MB)")
            
            logger.info(f"✓ Successfully downloaded from {source['name']}")
            logger.info(f"✓ Files ready for both Pandas (Excel) and Spark (CSV)")
            return True, excel_dest
        except Exception as e:
            logger.error(f"Downloaded file validation failed: {e}")
            return False, None
    
    # Download failed
    logger.error("\n" + "="*60)
    logger.error("FAILED TO DOWNLOAD WORLD CUP DATA")
    logger.error("="*60)
    logger.error("\nPlease try these options:")
    logger.error("1. Check your internet connection")
    logger.error("2. Verify Tableau website is accessible")
    logger.error("3. Download manually from:")
    logger.error("   https://public.tableau.com/app/sample-data/world_cup_results.xlsx")
    logger.error(f"4. Save the file as: {config.raw_data_path / config.worldcup_raw}")
    logger.error("="*60)
    return False, None


def download_temperature_data() -> Tuple[bool, Optional[Path]]:
    """
    Download temperature dataset from Our World in Data.
    ZIP format containing CSV.
    
    Returns:
        Tuple of (success: bool, file_path: Optional[Path])
    """
    downloader = DataDownloader()
    final_destination = config.raw_data_path / config.temperature_raw
    source = TEMPERATURE_SOURCES[0]  # Only one source
    zip_path = config.raw_data_path / "temperature_data.zip"
    
    logger.info("\n" + "="*60)
    logger.info("DOWNLOADING TEMPERATURE DATASET")
    logger.info("="*60)
    logger.info(f"Source: {source['name']}")
    logger.info(f"Format: ZIP with CSV inside")
    
    # Download ZIP file
    success, error = downloader.download_file(
        source['url'],
        zip_path,
        "Global Temperature Data (ZIP)"
    )
    
    if not success:
        return False, None
    
    # Extract ZIP
    logger.info("Extracting ZIP file...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List contents
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            
            if not csv_files:
                logger.error("No CSV file found in ZIP")
                return False, None
            
            # Extract first CSV
            csv_file = csv_files[0]
            logger.info(f"Extracting: {csv_file}")
            zip_ref.extract(csv_file, config.raw_data_path)
            
            # Rename to standard name
            extracted_path = config.raw_data_path / csv_file
            
            # Remove old file if exists
            if final_destination.exists():
                final_destination.unlink()
                logger.info(f"Removed old {final_destination.name}")
            
            # Rename extracted file
            extracted_path.rename(final_destination)
            logger.info(f"✓ Renamed to {final_destination.name}")
        
        # Clean up ZIP
        if zip_path.exists():
            zip_path.unlink()
            logger.info("✓ Cleaned up ZIP file")
        
        # Clean up any leftover CSV files with original names
        for csv_pattern in ['average-monthly-*.csv']:
            for leftover in config.raw_data_path.glob(csv_pattern):
                if leftover != final_destination:
                    leftover.unlink()
                    logger.info(f"✓ Cleaned up {leftover.name}")
        
        # Validate
        df = pd.read_csv(final_destination, nrows=5)
        logger.info(f"✓ Validation: Temperature data loaded")
        logger.info(f"✓ Columns: {list(df.columns)[:5]}...")
        logger.info(f"✓ Successfully downloaded from {source['name']}")
        return True, final_destination
        
    except Exception as e:
        logger.error(f"ZIP extraction failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return False, None
    
    # Download failed
    logger.error("\n" + "="*60)
    logger.error("FAILED TO DOWNLOAD TEMPERATURE DATA")
    logger.error("="*60)
    logger.error("\nPlease try these options:")
    logger.error("1. Check your internet connection")
    logger.error("2. Verify Our World in Data website is accessible")
    logger.error("3. Download manually from:")
    logger.error("   https://ourworldindata.org/grapher/average-monthly-surface-temperature.zip?v=1&csvType=full&useColumnShortNames=false")
    logger.error("4. Extract the CSV from the ZIP file")
    logger.error(f"5. Save the CSV as: {final_destination}")
    logger.error("="*60)
    return False, None


def download_all_data() -> bool:
    """
    Download all required datasets.
    
    Returns:
        bool: True if all downloads succeeded
    """
    logger.info("\n" + "#"*60)
    logger.info("#" + " "*58 + "#")
    logger.info("#" + "  DATA INGESTION PROCESS".center(58) + "#")
    logger.info("#" + " "*58 + "#")
    logger.info("#"*60 + "\n")
    
    start_time = time.time()
    
    # Download World Cup data
    wc_success, wc_path = download_worldcup_data()
    
    if not wc_success:
        logger.error("\n✗ Critical: Failed to download World Cup data")
        return False
    
    # Download temperature data
    temp_success, temp_path = download_temperature_data()
    
    if not temp_success:
        logger.error("\n✗ Critical: Failed to download temperature data")
        return False
    
    elapsed = time.time() - start_time
    
    logger.info("\n" + "="*60)
    logger.info("DATA INGESTION COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    logger.info(f"✓ World Cup data: {wc_path.name}")
    logger.info(f"✓ Temperature data: {temp_path.name}")
    logger.info(f"✓ Location: {config.raw_data_path}")
    logger.info(f"✓ Time taken: {elapsed:.2f} seconds")
    logger.info("="*60 + "\n")
    
    return True


def main():
    """
    Main entry point for data ingestion.
    """
    success = download_all_data()
    
    if not success:
        logger.error("\nData ingestion failed. Please check the logs above.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
