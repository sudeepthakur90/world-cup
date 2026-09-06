"""Data model package for star schema construction."""

from .build_model import StarSchemaBuilder, build_and_save_model

__all__ = ["StarSchemaBuilder", "build_and_save_model"]