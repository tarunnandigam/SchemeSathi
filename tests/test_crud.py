"""
tests/test_crud.py
------------------
Tests for CRUD operations via the service layer.

Tests:
  T08 — Reading and filtering records
  T09 — Updating documents and recalculating missing requirements
  T10 — Updating status history
  T11 — Deleting a test application
  T12 — Preventing deletion of a referenced scheme
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from config import COL_SCHEMES, COL_APPLICATIONS
from services.scheme_service import (
    create_scheme,
    get_scheme_by_id,
    list_active_schemes,
    search_schemes_by_name,
    update_scheme,
    delete_scheme,
)
from services.application_service import (
    create_application,
    get_application,
    list_applications,
    update_documents,
    update_status,
    delete_application,
    get_checklist_summary,
)
from tests.conftest import make_scheme


class TestCRUD:
    @pytest.fixture(autouse=True)
    def setup_data(self, clean_db):
        """Insert a base scheme and application before each test in this class."""
        self.db = clean_db

        # Insert scheme via service
        res = create_scheme(clean_db, {
            "name": "CRUD Test Scheme",
            "category": "Testing",
            "department": "Test Dept",
            "description": "For CRUD tests",
            "benefits_description": "N/A",
            "eligibility_criteria": ["Test criterion"],
            "required_documents": ["identity_proof", "income_certificate"],
            "official_url": None,
            "source_verified": False,
            "active": True,
        })
        assert res["success"], f"Setup scheme failed: {res}"
        self.scheme_id = res["scheme_id"]

        # Insert application
        app_res = create_application(clean_db, {
            "scheme_id": self.scheme_id,
            "applicant_alias": "Test User",
            "documents_provided": ["identity_proof"],
        })
        assert app_res["success"], f"Setup application failed: {app_res}"
        self.app_ref = app_res["application_ref"]

    def test_T08_read_and_filter_records(self):
        """T08: Reading and filtering operations should return correct records."""
        # Read scheme by ID
        scheme = get_scheme_by_id(self.db, self.scheme_id)
        assert scheme is not None
        assert scheme["name"] == "CRUD Test Scheme"

        # List all active schemes
        schemes = list_active_schemes(self.db)
        assert any(s["scheme_id"] == self.scheme_id for s in schemes)

        # Search by name
        results = search_schemes_by_name(self.db, "CRUD Test")
        assert len(results) >= 1

        # Get application
        app = get_application(self.db, self.app_ref)
        assert app is not None
        assert app["scheme_id"] == self.scheme_id

        # Filter applications by status
        pending = list_applications(self.db, status_filter="documents_pending")
        assert any(a["application_ref"] == self.app_ref for a in pending)

    def test_T09_update_documents_recalculates_missing(self):
        """T09: Providing all required documents should update missing_documents to []."""
        # Provide all required docs
        res = update_documents(
            self.db,
            self.app_ref,
            ["identity_proof", "income_certificate"],
        )
        assert res["success"], f"Update failed: {res}"
        assert res["missing_documents"] == []
        assert res["new_status"] == "ready_to_submit"
        assert res["readiness_pct"] == 100.0

        # Verify in DB
        app = get_application(self.db, self.app_ref)
        assert app["missing_documents"] == []
        assert app["application_status"] == "ready_to_submit"

    def test_T10_update_status_appends_stage_history(self):
        """T10: Updating status should append a new stage_history entry."""
        app_before = get_application(self.db, self.app_ref)
        history_len_before = len(app_before.get("stage_history", []))

        res = update_status(self.db, self.app_ref, "submitted", "Test status update")
        assert res["success"], f"Status update failed: {res}"

        app_after = get_application(self.db, self.app_ref)
        assert app_after["application_status"] == "submitted"
        assert len(app_after.get("stage_history", [])) == history_len_before + 1
        last_entry = app_after["stage_history"][-1]
        assert last_entry["stage"] == "submitted"
        assert "timestamp" in last_entry

    def test_T11_delete_test_application(self):
        """T11: An application should be deletable by its reference."""
        # Create a second application to delete
        app2 = create_application(self.db, {
            "scheme_id": self.scheme_id,
            "applicant_alias": "Delete Me",
            "documents_provided": [],
        })
        assert app2["success"]
        ref2 = app2["application_ref"]

        res = delete_application(self.db, ref2)
        assert res["success"]

        # Verify deletion
        deleted = get_application(self.db, ref2)
        assert deleted is None

    def test_T12_prevent_delete_referenced_scheme(self):
        """T12: Deleting a scheme that has application records should be blocked."""
        # The scheme_id has a linked application from setup
        res = delete_scheme(self.db, self.scheme_id)
        assert not res["success"]
        assert "Cannot delete" in res["error"] or "reference" in res["error"].lower()

        # Scheme should still exist
        scheme = get_scheme_by_id(self.db, self.scheme_id)
        assert scheme is not None

    def test_checklist_summary(self):
        """Checklist summary should compute missing docs and readiness correctly."""
        summary = get_checklist_summary(self.db, self.app_ref)
        assert summary is not None
        assert "required_documents" in summary
        assert "missing_documents" in summary
        assert isinstance(summary["readiness_pct"], float)
        # One of two docs provided → 50%
        assert summary["readiness_pct"] == 50.0

    def test_invalid_status_rejected_by_service(self):
        """Service layer should reject an unknown status before hitting the DB."""
        res = update_status(self.db, self.app_ref, "INVALID_STATUS_XYZ")
        assert not res["success"]
        assert "valid status" in res["error"].lower() or "not a valid" in res["error"].lower()

    def test_delete_nonexistent_application(self):
        """Deleting a non-existent application should return success=False."""
        res = delete_application(self.db, "APP-999999")
        assert not res["success"]
