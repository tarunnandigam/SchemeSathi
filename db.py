"""
db.py
-----
Manages the PyMongo client and exposes helper functions to obtain database
and collection references.  Import `get_db()` in service / query modules.

Keeps connection errors informative and never exposes credentials.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Optional

import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError

from config import MONGO_URI, DB_NAME


# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Return a cached MongoClient.  Creates it on first call."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5-second timeout so errors are quick
            )
        except ConfigurationError as exc:
            _friendly_error("MongoDB URI is misconfigured", exc)
    return _client


def get_db(db_name: str = DB_NAME) -> Database:
    """Return a Database object for *db_name*."""
    return get_client()[db_name]


def check_connection(db_name: str = DB_NAME) -> tuple[bool, str]:
    """
    Ping the MongoDB server.
    Returns (True, version_string) on success or (False, error_message) on failure.
    """
    try:
        client = get_client()
        client.admin.command("ping")
        info = client.server_info()
        version = info.get("version", "unknown")
        return True, f"Connected  — MongoDB {version}"
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        return False, (
            "Cannot reach MongoDB.  Is the service running?\n"
            "Start it with:  net start MongoDB  (PowerShell as Administrator)\n"
            f"Detail: {type(exc).__name__}"
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"Unexpected error: {type(exc).__name__}: {exc}"


def _friendly_error(context: str, exc: Exception) -> None:
    """Print a human-readable error and exit."""
    print(f"\n[SchemeReach] Database error — {context}")
    print(f"  {type(exc).__name__}: {exc}")
    print("  Check your .env file and ensure MongoDB is running.\n")
    sys.exit(1)


def close_connection() -> None:
    """Close the MongoClient (useful in tests)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
