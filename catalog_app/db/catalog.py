"""Current-state catalog persistence helpers."""

from collections.abc import Sequence
import json

from catalog_app.db.connection import get_connection
from catalog_app.models import PresentationRecord, SearchResult, SyncStatus
from catalog_app.app_types import IndexedWorkbookRow


def _vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.12f}" for value in values) + "]"


def upsert_presentations(
    rows: Sequence[IndexedWorkbookRow],
    embeddings: Sequence[Sequence[float]],
) -> int:
    if len(rows) != len(embeddings):
        raise ValueError("rows and embeddings must have matching lengths")
    if not rows:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for row, embedding in zip(rows, embeddings, strict=True):
                source_key = row.source_key or ""
                drive_id = row.drive_id or ""
                item_id = row.item_id or str(row.metadata.get("id") or row.source_id)
                web_url = row.web_url or str(row.metadata.get("web_url") or "")
                cursor.execute(
                    """
                    INSERT INTO presentations (
                        source_id,
                        title,
                        workbook_name,
                        sheet_name,
                        row_number,
                        source_key,
                        drive_id,
                        item_id,
                        web_url,
                        last_modified_at,
                        metadata,
                        searchable_text,
                        embedding,
                        updated_at
                    )
                    VALUES (
                        %(source_id)s,
                        %(title)s,
                        %(workbook_name)s,
                        %(sheet_name)s,
                        %(row_number)s,
                        NULLIF(%(source_key)s, ''),
                        NULLIF(%(drive_id)s, ''),
                        NULLIF(%(item_id)s, ''),
                        NULLIF(%(web_url)s, ''),
                        NULLIF(%(last_modified_at)s, '')::timestamptz,
                        %(metadata)s::jsonb,
                        %(searchable_text)s,
                        %(embedding)s::vector,
                        NOW()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        workbook_name = EXCLUDED.workbook_name,
                        sheet_name = EXCLUDED.sheet_name,
                        row_number = EXCLUDED.row_number,
                        source_key = EXCLUDED.source_key,
                        drive_id = EXCLUDED.drive_id,
                        item_id = EXCLUDED.item_id,
                        web_url = EXCLUDED.web_url,
                        last_modified_at = EXCLUDED.last_modified_at,
                        metadata = EXCLUDED.metadata,
                        searchable_text = EXCLUDED.searchable_text,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
                    """,
                    {
                        "source_id": row.source_id,
                        "title": row.title,
                        "workbook_name": row.workbook_name,
                        "sheet_name": row.sheet_name,
                        "row_number": row.row_number,
                        "source_key": source_key,
                        "drive_id": drive_id,
                        "item_id": item_id,
                        "web_url": web_url,
                        "last_modified_at": row.last_modified_at or "",
                        "metadata": json.dumps(row.metadata),
                        "searchable_text": row.searchable_text,
                        "embedding": _vector_literal(embedding),
                    },
                )
        connection.commit()

    return len(rows)


def delete_presentations(source_ids: Sequence[str]) -> int:
    """Hard-delete current catalog rows that no longer exist in SharePoint."""
    if not source_ids:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM presentations WHERE source_id = ANY(%s)",
                (list(source_ids),),
            )
            deleted_count = cursor.rowcount
        connection.commit()

    return deleted_count


def upsert_presentation_source(
    *,
    source_key: str,
    source_name: str,
    drive_id: str,
    folder_id: str | None = None,
    folder_path: str | None = None,
    delta_link: str | None = None,
) -> None:
    """Save one configured SharePoint source without retaining source history."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO presentation_sources (
                    source_key,
                    source_name,
                    drive_id,
                    folder_id,
                    folder_path,
                    delta_link,
                    updated_at
                )
                VALUES (
                    %(source_key)s,
                    %(source_name)s,
                    %(drive_id)s,
                    %(folder_id)s,
                    %(folder_path)s,
                    %(delta_link)s,
                    NOW()
                )
                ON CONFLICT (source_key) DO UPDATE SET
                    source_name = EXCLUDED.source_name,
                    drive_id = EXCLUDED.drive_id,
                    folder_id = EXCLUDED.folder_id,
                    folder_path = EXCLUDED.folder_path,
                    delta_link = EXCLUDED.delta_link,
                    updated_at = NOW()
                """,
                {
                    "source_key": source_key,
                    "source_name": source_name,
                    "drive_id": drive_id,
                    "folder_id": folder_id,
                    "folder_path": folder_path,
                    "delta_link": delta_link,
                },
            )
        connection.commit()


def get_source_delta_links() -> dict[str, str]:
    """Return saved Microsoft Graph delta links keyed by configured source."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_key, delta_link
                FROM presentation_sources
                WHERE delta_link IS NOT NULL
                """
            )
            rows = cursor.fetchall()

    return {str(row["source_key"]): str(row["delta_link"]) for row in rows}


def update_sync_status(
    *,
    status: str,
    total_items: int = 0,
    processed_items: int = 0,
    indexed_rows: int = 0,
    removed_rows: int = 0,
    started: bool = False,
    finished: bool = False,
    error: str | None = None,
) -> None:
    """Overwrite the single current reload status row."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sync_status (
                    id,
                    status,
                    total_items,
                    processed_items,
                    indexed_rows,
                    removed_rows,
                    started_at,
                    finished_at,
                    error,
                    updated_at
                )
                VALUES (
                    1,
                    %(status)s,
                    %(total_items)s,
                    %(processed_items)s,
                    %(indexed_rows)s,
                    %(removed_rows)s,
                    CASE WHEN %(started)s THEN NOW() ELSE NULL END,
                    CASE WHEN %(finished)s THEN NOW() ELSE NULL END,
                    %(error)s,
                    NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    total_items = EXCLUDED.total_items,
                    processed_items = EXCLUDED.processed_items,
                    indexed_rows = EXCLUDED.indexed_rows,
                    removed_rows = EXCLUDED.removed_rows,
                    started_at = CASE
                        WHEN %(started)s THEN NOW()
                        ELSE sync_status.started_at
                    END,
                    finished_at = CASE
                        WHEN %(finished)s THEN NOW()
                        ELSE NULL
                    END,
                    error = EXCLUDED.error,
                    updated_at = NOW()
                """,
                {
                    "status": status,
                    "total_items": total_items,
                    "processed_items": processed_items,
                    "indexed_rows": indexed_rows,
                    "removed_rows": removed_rows,
                    "started": started,
                    "finished": finished,
                    "error": error,
                },
            )
        connection.commit()


def get_sync_status() -> SyncStatus:
    """Return the current reload status."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    status,
                    total_items,
                    processed_items,
                    indexed_rows,
                    removed_rows,
                    started_at::text AS started_at,
                    finished_at::text AS finished_at,
                    error
                FROM sync_status
                WHERE id = 1
                """
            )
            row = cursor.fetchone()

    if row is None:
        return SyncStatus(
            status="idle",
            total_items=0,
            processed_items=0,
            indexed_rows=0,
            removed_rows=0,
        )
    return SyncStatus(**row)


def fetch_presentations(limit: int = 10, offset: int = 0) -> list[PresentationRecord]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id, title, workbook_name, sheet_name, row_number, metadata
                FROM presentations
                ORDER BY sheet_name, row_number
                LIMIT %s
                OFFSET %s
                """,
                (limit, offset),
            )
            results = cursor.fetchall()

    return [PresentationRecord(**row) for row in results]


def count_presentations() -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM presentations")
            row = cursor.fetchone()
    return int(row["count"])


def search_presentations(
    query_embedding: Sequence[float],
    top_k: int,
) -> list[SearchResult]:
    vector = _vector_literal(query_embedding)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    source_id,
                    title,
                    workbook_name,
                    sheet_name,
                    row_number,
                    metadata,
                    1 - (embedding <=> %s::vector) AS score
                FROM presentations
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, vector, top_k),
            )
            results = cursor.fetchall()

    return [SearchResult(**row) for row in results]
