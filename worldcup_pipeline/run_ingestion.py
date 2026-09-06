#!/usr/bin/env python
"""
Ingestion Runner - Download Data Only

Runs only the data ingestion stage.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run
from src.ingestion.download_data import main

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)