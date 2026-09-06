"""Data ingestion package for downloading source datasets."""

from .download_data import (
    DataDownloader,
    download_all_data,
    download_temperature_data,
    download_worldcup_data,
)

__all__ = [
    "DataDownloader",
    "download_all_data",
    "download_worldcup_data",
    "download_temperature_data",
]