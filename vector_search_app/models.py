"""Pydantic request and response models for the vector search API."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Natural-language search request."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)


class PresentationRecord(BaseModel):
    """Workbook row returned for the spreadsheet UI."""

    source_id: str
    title: str
    workbook_name: str
    sheet_name: str
    row_number: int
    metadata: dict[str, object]


class SearchResult(PresentationRecord):
    """Workbook row plus similarity score."""

    score: float


class SyncStatus(BaseModel):
    """Current reload status for the single-app current-state workflow."""

    status: str
    total_items: int
    processed_items: int
    indexed_rows: int
    removed_rows: int
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
