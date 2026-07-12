"""Ingestion pipeline: SourceAdapter -> identity resolution -> ProductStore."""

from camerino_api.ingestion.service import IngestionReport, IngestionService

__all__ = ["IngestionReport", "IngestionService"]
