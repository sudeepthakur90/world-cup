#!/usr/bin/env python
"""
Data Cleanup Utility

Removes all downloaded and temporary files.
Useful for troubleshooting or starting fresh.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


def cleanup_directory(directory: Path, description: str, keep_gitkeep: bool = True):
    """
    Clean up all files in a directory.
    
    Args:
        directory: Directory to clean
        description: Human-readable description
        keep_gitkeep: Whether to keep .gitkeep files
    """
    if not directory.exists():
        logger.info(f"  {description}: Directory doesn't exist, skipping")
        return 0
    
    logger.info(f"\n  Cleaning: {description}")
    logger.info(f"  Path: {directory}")
    
    count = 0
    for file in directory.rglob('*'):
        if file.is_file():
            # Keep .gitkeep files if requested
            if keep_gitkeep and file.name == '.gitkeep':
                continue
            
            try:
                file.unlink()
                logger.info(f"    ✗ Removed: {file.name}")
                count += 1
            except Exception as e:
                logger.warning(f"    ⚠ Could not remove {file.name}: {e}")
    
    logger.info(f"  ✓ Removed {count} file(s) from {description}")
    return count


def main():
    """
    Main cleanup process.
    """
    print("="*70)
    print("  DATA CLEANUP UTILITY")
    print("="*70)
    print("\nThis will remove:")
    print("  - Downloaded raw data (Excel, CSV, ZIP files)")
    print("  - Processed data (Parquet files)")
    print("  - Output data (Database, enriched files)")
    print("  - Log files")
    print("\n" + "="*70)
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("\n✓ Cleanup cancelled.")
        return False
    
    print("\n" + "-"*70)
    print("Starting cleanup...")
    print("-"*70)
    
    total_removed = 0
    
    # Clean raw data
    total_removed += cleanup_directory(
        config.raw_data_path,
        "Raw Data",
        keep_gitkeep=True
    )
    
    # Clean processed data
    total_removed += cleanup_directory(
        config.processed_data_path,
        "Processed Data",
        keep_gitkeep=True
    )
    
    # Clean output data
    total_removed += cleanup_directory(
        config.output_path,
        "Output Data",
        keep_gitkeep=True
    )
    
    # Clean logs (optional)
    print("\n  Cleaning: Log Files")
    log_cleaned = 0
    if config.log_file.exists():
        try:
            config.log_file.unlink()
            logger.info(f"    ✗ Removed: {config.log_file.name}")
            log_cleaned = 1
        except Exception as e:
            logger.warning(f"    ⚠ Could not remove log file: {e}")
    logger.info(f"  ✓ Removed {log_cleaned} log file(s)")
    total_removed += log_cleaned
    
    # Summary
    print("\n" + "="*70)
    print("  CLEANUP SUMMARY")
    print("="*70)
    print(f"\n  Total files removed: {total_removed}")
    print("\n  Directories preserved:")
    print(f"    - {config.raw_data_path}")
    print(f"    - {config.processed_data_path}")
    print(f"    - {config.output_path}")
    print(f"    - {config.log_path}")
    print("\n" + "="*70)
    print("\n  ✓ Cleanup complete!")
    print("\n  You can now run:")
    print("    python run_ingestion.py")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Cleanup cancelled by user.")
        sys.exit(1)
