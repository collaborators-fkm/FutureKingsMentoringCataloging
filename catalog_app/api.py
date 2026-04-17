"""FastAPI app for SharePoint-backed catalog search."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from catalog_app.catalog_sync import is_reload_running, run_catalog_reload
from catalog_app.db import (
    count_presentations,
    ensure_schema,
    fetch_all_presentation_metadata,
    fetch_presentations,
    get_sync_status,
    search_presentations,
    update_sync_status,
)
from catalog_app.embeddings import embed_text
from catalog_app.generation.column_helpers import get_excel_column_names
from catalog_app.generation.configuration import get_presentation_columns
from catalog_app.generation.excel_maker import workbook_to_bytes
from catalog_app.generation.generators import GeneratorRegistry
from catalog_app.models import SearchRequest

STATIC_DIR = Path(__file__).with_name("static")


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    yield


app = FastAPI(title="FKM Catalog", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/index.html", status_code=307)


@app.get("/index.html")
def index_html() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "indexed_rows": count_presentations(),
        "sync_status": get_sync_status().model_dump(),
    }


@app.post("/api/reload")
def reload_catalog(background_tasks: BackgroundTasks) -> dict[str, object]:
    if is_reload_running():
        raise HTTPException(status_code=409, detail="A reload is already running.")

    update_sync_status(status="running", started=True)
    background_tasks.add_task(run_catalog_reload, mark_started=False)
    return {"status": "started"}


@app.get("/api/reload/status")
def reload_status() -> dict[str, object]:
    return get_sync_status().model_dump()


@app.get("/api/presentations")
def presentations(limit: int = 10, offset: int = 0) -> dict[str, object]:
    total = count_presentations()
    items = fetch_presentations(limit=limit, offset=offset)
    columns: list[str] = []
    if items:
        columns = list(items[0].metadata.keys())
    return {
        "items": [item.model_dump() for item in items],
        "columns": columns,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/export.xlsx")
def export_excel() -> Response:
    rows = fetch_all_presentation_metadata()
    registry = GeneratorRegistry(default_drive_id="", headers={})
    headers = get_excel_column_names(get_presentation_columns(registry))
    workbook_bytes = workbook_to_bytes(rows, headers=headers)
    return Response(
        content=workbook_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": 'attachment; filename="workshop_catalog.xlsx"',
        },
    )


@app.post("/api/search")
def semantic_search(request: SearchRequest) -> dict[str, object]:
    if count_presentations() == 0:
        raise HTTPException(
            status_code=400,
            detail="No catalog rows found. Run Reload first.",
        )

    query_embedding = embed_text(request.query)
    results = search_presentations(query_embedding, request.top_k)
    return {"items": [item.model_dump() for item in results]}
