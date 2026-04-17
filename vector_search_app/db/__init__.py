"""Database package exports for the current-state presentation catalog."""

from vector_search_app.db.catalog import (
    count_presentations,
    delete_presentations,
    fetch_presentations,
    get_source_delta_links,
    get_sync_status,
    search_presentations,
    update_sync_status,
    upsert_presentation_source,
    upsert_presentations,
)
from vector_search_app.db.schema import ensure_schema

__all__ = [
    "count_presentations",
    "delete_presentations",
    "ensure_schema",
    "fetch_presentations",
    "get_source_delta_links",
    "get_sync_status",
    "search_presentations",
    "update_sync_status",
    "upsert_presentation_source",
    "upsert_presentations",
]
