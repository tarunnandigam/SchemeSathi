"""
tests/conftest.py
-----------------
Shared pytest fixtures for SchemeReach tests.

All tests use TEST_DB_NAME (scheme_reach_test) to avoid touching
the demonstration database.

Run:  pytest tests/ -v
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from config import TEST_DB_NAME, COL_SCHEMES, COL_APPLICATIONS, COL_BARRIER_REPORTS
from db import get_client
from setup_validators import setup


@pytest.fixture(scope="session")
def test_db():
    """
    Create a fresh test database for the entire test session.
    Drops and recreates it before tests run; drops it again after.
    """
    client = get_client()

    # Drop any leftovers from a previous failed run
    client.drop_database(TEST_DB_NAME)

    # Set up validators
    setup(TEST_DB_NAME)

    db = client[TEST_DB_NAME]
    yield db

    # Teardown
    client.drop_database(TEST_DB_NAME)


@pytest.fixture
def clean_db(test_db):
    """
    Wipe all collections before each individual test that needs a clean slate.
    """
    test_db[COL_SCHEMES].delete_many({})
    test_db[COL_APPLICATIONS].delete_many({})
    test_db[COL_BARRIER_REPORTS].delete_many({})
    yield test_db


def make_scheme(overrides: dict | None = None) -> dict:
    """Build a minimal valid scheme document."""
    now = datetime.now(timezone.utc)
    doc = {
        "scheme_id": "SCH-000001",
        "name": "Test Scheme Alpha",
        "category": "Education",
        "department": "Test Department",
        "description": "A fictional test scheme for pytest.",
        "benefits_description": "Test benefit only.",
        "eligibility_criteria": ["Must be a test record"],
        "required_documents": ["identity_proof", "income_certificate", "enrolment_proof"],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    if overrides:
        doc.update(overrides)
    return doc


def make_application(overrides: dict | None = None) -> dict:
    """Build a minimal valid application document."""
    now = datetime.now(timezone.utc)
    doc = {
        "application_ref": "APP-000001",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Test Applicant",
        "documents_provided": ["identity_proof"],
        "missing_documents": ["income_certificate", "enrolment_proof"],
        "application_status": "documents_pending",
        "stage_history": [
            {"stage": "preparation", "timestamp": now, "note": "Created"},
            {"stage": "documents_pending", "timestamp": now, "note": "Initial"},
        ],
        "created_at": now,
        "updated_at": now,
    }
    if overrides:
        doc.update(overrides)
    return doc
