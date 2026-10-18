"""
tests/test_validation.py
------------------------
Tests for MongoDB JSON Schema validation enforcement.

Tests:
  T01 — Successful database connection
  T02 — Valid scheme insertion accepted
  T03 — Invalid scheme rejected (empty name)
  T04 — Invalid scheme rejected (missing required fields)
  T05 — Valid application insertion accepted
  T06 — Invalid application status rejected
  T07 — Invalid application rejected (missing required fields)
  T15 — Scheme with no required documents handled safely
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from pymongo.errors import WriteError

from config import COL_SCHEMES, COL_APPLICATIONS
from db import check_connection
from tests.conftest import make_scheme, make_application


class TestConnection:
    def test_T01_database_connection(self, test_db):
        """T01: MongoDB should be reachable and pingable."""
        ok, msg = check_connection()
        assert ok, f"Expected connection success, got: {msg}"
        assert "Connected" in msg


class TestSchemeValidation:
    def test_T02_valid_scheme_accepted(self, clean_db):
        """T02: A fully valid scheme document must be inserted without error."""
        doc = make_scheme()
        # Should not raise
        result = clean_db[COL_SCHEMES].insert_one(doc)
        assert result.inserted_id is not None

    def test_T03_invalid_scheme_empty_name_rejected(self, clean_db):
        """T03: A scheme with an empty name must be rejected by the validator."""
        doc = make_scheme({"name": ""})  # violates minLength:2
        with pytest.raises((WriteError, Exception)):
            clean_db[COL_SCHEMES].insert_one(doc)

    def test_T04_invalid_scheme_missing_required_fields(self, clean_db):
        """T04: A scheme missing required fields (created_at, updated_at) must be rejected."""
        doc = {
            "scheme_id": "SCH-BAD01",
            "name": "Bad Scheme",
            "category": "Test",
            "department": "Test",
            "active": True,
            # missing created_at and updated_at
        }
        with pytest.raises((WriteError, Exception)):
            clean_db[COL_SCHEMES].insert_one(doc)

    def test_T15_scheme_no_required_documents(self, clean_db):
        """T15: A scheme with an empty required_documents array should be accepted."""
        doc = make_scheme({
            "scheme_id": "SCH-NODOCS",
            "required_documents": [],
        })
        result = clean_db[COL_SCHEMES].insert_one(doc)
        assert result.inserted_id is not None


class TestApplicationValidation:
    def test_T05_valid_application_accepted(self, clean_db):
        """T05: A valid application document must be inserted without error."""
        # Scheme must exist first for referential integrity checks in services,
        # but validator itself only checks fields — so direct insert is fine.
        doc = make_application()
        result = clean_db[COL_APPLICATIONS].insert_one(doc)
        assert result.inserted_id is not None

    def test_T06_invalid_application_status_rejected(self, clean_db):
        """T06: An application with a status not in the enum must be rejected."""
        doc = make_application({"application_status": "COMPLETELY_WRONG_STATUS"})
        with pytest.raises((WriteError, Exception)):
            clean_db[COL_APPLICATIONS].insert_one(doc)

    def test_T07_invalid_application_missing_fields(self, clean_db):
        """T07: An application missing required fields must be rejected."""
        doc = {
            "application_ref": "APP-BADBAD",
            # missing scheme_id, documents_provided, etc.
        }
        with pytest.raises((WriteError, Exception)):
            clean_db[COL_APPLICATIONS].insert_one(doc)
