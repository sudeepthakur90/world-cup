#!/usr/bin/env python
"""
Adaptive Pipeline Runner - Entry Point for Adaptive Architecture

This runs the intelligent pipeline that auto-selects between Pandas and PySpark.
It handles all path setup automatically.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run
from src.main_adaptive import main

if __name__ == "__main__":
    main()