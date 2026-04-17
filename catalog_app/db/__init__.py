"""Database package exports for the current-state presentation catalog."""

from catalog_app.db.catalog import (
    count_presentations,
    delete_presentations,
    fetch_all_presentation_metadata,
    fetch_presentations,
    get_source_delta_links,
    get_sync_status,
    search_presentations,
    update_sync_status,
    upsert_presentation_source,
    upsert_presentations,
)
from catalog_app.db.schema import ensure_schema

__all__ = [
    "count_presentations",
    "delete_presentations",
    "ensure_schema",
    "fetch_all_presentation_metadata",
    "fetch_presentations",
    "get_source_delta_links",
    "get_sync_status",
    "search_presentations",
    "update_sync_status",
    "upsert_presentation_source",
    "upsert_presentations",
]
