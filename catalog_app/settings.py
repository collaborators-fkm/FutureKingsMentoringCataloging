"""Configuration helpers for the catalog application."""

import os


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/presentations",
    )


def get_embedding_model() -> str:
    return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedding_dimension() -> int:
    return int(os.getenv("EMBEDDING_DIMENSION", "1536"))
