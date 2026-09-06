"""
Configuration Management Module

Centralized configuration for the World Cup data pipeline.
Loads environment variables and provides default values.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data Sources
WORLDCUP_DATA_URL = os.getenv(
    "WORLDCUP_DATA_URL",
    "https://public.tableau.com/app/sample-data/world_cup_results.xlsx"
)

TEMPERATURE_DATA_URL = os.getenv(
    "TEMPERATURE_DATA_URL",
    "https://ourworldindata.org/grapher/average-monthly-surface-temperature.zip?v=1&csvType=full&useColumnShortNames=false"
)

# Directory Paths
raw_path = Path(os.getenv("RAW_DATA_PATH", PROJECT_ROOT / "data" / "raw"))
processed_path = Path(os.getenv("PROCESSED_DATA_PATH", PROJECT_ROOT / "data" / "processed"))
output_path = Path(os.getenv("OUTPUT_PATH", PROJECT_ROOT / "data" / "output"))
log_path = Path(os.getenv("LOG_PATH", PROJECT_ROOT / "logs"))

# Uppercase aliases
RAW_DATA_PATH = raw_path
PROCESSED_DATA_PATH = processed_path
OUTPUT_PATH = output_path
LOG_PATH = log_path

# Create directories if they don't exist
for path in [raw_path, processed_path, output_path, log_path]:
    path.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "worldcup_analytics")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# SQLite database path
SQLITE_DB_PATH = output_path / f"{DB_NAME}.db"

# Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "10000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))

# Logging Configuration
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = log_path / os.getenv("LOG_FILE", "pipeline.log")
LOG_LEVEL = log_level
LOG_FILE = log_file

# File Names
WORLDCUP_RAW_FILE = "WorldCupMatches.xlsx"
WORLDCUP_RAW_CSV = "WorldCupMatches.csv"
TEMPERATURE_RAW_FILE = "temperature.csv"
WORLDCUP_CLEANED_FILE = "worldcup_cleaned.parquet"
TEMPERATURE_CLEANED_FILE = "temperature_cleaned.parquet"
WORLDCUP_ENRICHED_FILE = "worldcup_enriched.parquet"
GOLD_ENRICHED_FILE = "worldcup_enriched.parquet"  # Alias

# Data Quality Thresholds
MIN_TEMPERATURE = -50
MAX_TEMPERATURE = 60
MIN_YEAR = 1930
MAX_YEAR = 2014


def get_database_url() -> str:
    """Get database connection URL."""
    if DB_TYPE == "sqlite":
        return f"sqlite:///{SQLITE_DB_PATH}"
    elif DB_TYPE == "postgresql":
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


class Config:
    """Configuration class with all attributes accessible via both naming conventions."""
    
    # Project paths
    project_root = PROJECT_ROOT
    PROJECT_ROOT = PROJECT_ROOT
    
    # Data paths (lowercase)
    raw_path = raw_path
    processed_path = processed_path
    output_path = output_path
    log_path = log_path
    
    # Data paths (lowercase with underscore - for compatibility)
    raw_data_path = raw_path
    processed_data_path = processed_path
    output_data_path = output_path
    log_data_path = log_path
    
    # Data paths (uppercase)
    RAW_DATA_PATH = raw_path
    PROCESSED_DATA_PATH = processed_path
    OUTPUT_PATH = output_path
    LOG_PATH = log_path
    GOLD_PATH = output_path  # Alias for output path (gold layer)
    
    # Database
    db_type = DB_TYPE
    db_name = DB_NAME
    db_host = DB_HOST
    db_port = DB_PORT
    db_user = DB_USER
    db_password = DB_PASSWORD
    sqlite_db_path = SQLITE_DB_PATH
    DB_TYPE = DB_TYPE
    DB_NAME = DB_NAME
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    SQLITE_DB_PATH = SQLITE_DB_PATH
    
    # Logging
    log_level = log_level
    log_file = log_file
    LOG_LEVEL = LOG_LEVEL
    LOG_FILE = LOG_FILE
    
    # Processing
    max_retries = MAX_RETRIES
    timeout_seconds = TIMEOUT_SECONDS
    timeout = TIMEOUT_SECONDS  # Alias
    chunk_size = CHUNK_SIZE
    MAX_RETRIES = MAX_RETRIES
    TIMEOUT_SECONDS = TIMEOUT_SECONDS
    TIMEOUT = TIMEOUT_SECONDS  # Alias
    CHUNK_SIZE = CHUNK_SIZE
    
    # File names (lowercase)
    worldcup_raw_file = WORLDCUP_RAW_FILE
    worldcup_raw_csv = WORLDCUP_RAW_CSV
    temperature_raw_file = TEMPERATURE_RAW_FILE
    worldcup_cleaned_file = WORLDCUP_CLEANED_FILE
    temperature_cleaned_file = TEMPERATURE_CLEANED_FILE
    
    # File names (short versions - for compatibility)
    worldcup_raw = WORLDCUP_RAW_FILE
    temperature_raw = TEMPERATURE_RAW_FILE
    worldcup_cleaned = WORLDCUP_CLEANED_FILE
    temperature_cleaned = TEMPERATURE_CLEANED_FILE
    worldcup_enriched = WORLDCUP_ENRICHED_FILE
    GOLD_ENRICHED_FILE = GOLD_ENRICHED_FILE
    
    # File names (uppercase)
    WORLDCUP_RAW_FILE = WORLDCUP_RAW_FILE
    WORLDCUP_RAW_CSV = WORLDCUP_RAW_CSV
    TEMPERATURE_RAW_FILE = TEMPERATURE_RAW_FILE
    WORLDCUP_CLEANED_FILE = WORLDCUP_CLEANED_FILE
    TEMPERATURE_CLEANED_FILE = TEMPERATURE_CLEANED_FILE
    
    # Data sources (lowercase)
    worldcup_data_url = WORLDCUP_DATA_URL
    temperature_data_url = TEMPERATURE_DATA_URL
    
    # Data sources (uppercase)
    WORLDCUP_DATA_URL = WORLDCUP_DATA_URL
    TEMPERATURE_DATA_URL = TEMPERATURE_DATA_URL
    
    # Quality thresholds (lowercase)
    min_temperature = MIN_TEMPERATURE
    max_temperature = MAX_TEMPERATURE
    min_year = MIN_YEAR
    max_year = MAX_YEAR
    
    # Quality thresholds (uppercase)
    MIN_TEMPERATURE = MIN_TEMPERATURE
    MAX_TEMPERATURE = MAX_TEMPERATURE
    MIN_YEAR = MIN_YEAR
    MAX_YEAR = MAX_YEAR
    
    @staticmethod
    def get_database_url() -> str:
        """Get database URL."""
        return get_database_url()
    
    # Database URL as property
    @property
    def db_url(self) -> str:
        """Get database URL."""
        return get_database_url()


# Create singleton instance
config = Config()
