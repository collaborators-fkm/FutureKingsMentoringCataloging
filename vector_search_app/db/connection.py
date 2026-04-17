"""Shared database connection helpers."""

import psycopg
from psycopg.rows import dict_row

from vector_search_app.settings import get_database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_database_url(), row_factory=dict_row)
