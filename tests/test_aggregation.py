"""
tests/test_aggregation.py
--------------------------
Tests for aggregation pipelines.

Tests:
  T13 — Correct aggregation of missing-document counts
  T14 — Correct aggregation of application-status counts
  T16 — Correct joining of scheme names (Pipeline 4, $lookup)
  T17 — Empty collection handled without crash
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from config import COL_SCHEMES, COL_APPLICATIONS
from services.scheme_service import create_scheme
from services.application_service import create_application
from services.analytics_service import (
    missing_documents_frequency,
    applications_by_status,
    incomplete_applications_by_scheme,
    incomplete_apps_with_scheme_names,
    dashboard_metrics,
)


class TestAggregations:
    @pytest.fixture(autouse=True)
    def setup_data(self, clean_db):
        """Populate two schemes and several applications for aggregation testing."""
        self.db = clean_db

        # Scheme A — Education
        res_a = create_scheme(clean_db, {
            "name": "Agg Test Education Scheme",
            "category": "Education",
            "department": "Dept of Testing",
            "description": "Aggregation test scheme A",
            "benefits_description": "N/A",
            "eligibility_criteria": [],
            "required_documents": ["identity_proof", "income_certificate", "marksheet"],
            "official_url": None,
            "source_verified": False,
            "active": True,
        })
        self.scheme_a = res_a["scheme_id"]

        # Scheme B — Health
        res_b = create_scheme(clean_db, {
            "name": "Agg Test Health Scheme",
            "category": "Health",
            "department": "Dept of Health Testing",
            "description": "Aggregation test scheme B",
            "benefits_description": "N/A",
            "eligibility_criteria": [],
            "required_documents": ["identity_proof", "ration_card", "bpl_certificate"],
            "official_url": None,
            "source_verified": False,
            "active": True,
        })
        self.scheme_b = res_b["scheme_id"]

        # Applications for Scheme A
        create_application(clean_db, {
            "scheme_id": self.scheme_a,
            "applicant_alias": "User 1",
            "documents_provided": ["identity_proof"],  # missing: income_certificate, marksheet
        })
        create_application(clean_db, {
            "scheme_id": self.scheme_a,
            "applicant_alias": "User 2",
            "documents_provided": ["identity_proof", "income_certificate"],  # missing: marksheet
        })
        create_application(clean_db, {
            "scheme_id": self.scheme_a,
            "applicant_alias": "User 3",
            "documents_provided": ["identity_proof", "income_certificate", "marksheet"],  # complete
        })

        # Applications for Scheme B
        create_application(clean_db, {
            "scheme_id": self.scheme_b,
            "applicant_alias": "User 4",
            "documents_provided": ["identity_proof"],  # missing: ration_card, bpl_certificate
        })
        create_application(clean_db, {
            "scheme_id": self.scheme_b,
            "applicant_alias": "User 5",
            "documents_provided": ["identity_proof", "ration_card", "bpl_certificate"],  # complete
        })

    def test_T13_missing_documents_frequency(self):
        """T13: Pipeline 1 must correctly count and rank missing documents."""
        results = missing_documents_frequency(self.db)
        assert isinstance(results, list)
        assert len(results) > 0

        doc_counts = {r["document_type"]: r["count"] for r in results}

        # income_certificate missing in 1 record, marksheet missing in 2 records
        assert "marksheet" in doc_counts
        assert "income_certificate" in doc_counts
        assert "ration_card" in doc_counts
        assert "bpl_certificate" in doc_counts

        # marksheet should appear 2 times (User 1 and User 2)
        assert doc_counts["marksheet"] == 2

        # Results should be sorted descending
        counts = [r["count"] for r in results]
        assert counts == sorted(counts, reverse=True)

    def test_T14_applications_by_status(self):
        """T14: Pipeline 2 must correctly count records per status."""
        results = applications_by_status(self.db)
        assert isinstance(results, list)

        status_map = {r["status"]: r["count"] for r in results}

        # All 5 apps start as documents_pending or ready_to_submit
        total = sum(status_map.values())
        assert total == 5

        # At least some should be documents_pending
        assert "documents_pending" in status_map or "ready_to_submit" in status_map

    def test_T16_incomplete_apps_with_scheme_names(self):
        """T16: Pipeline 4 must join scheme names correctly using $lookup."""
        results = incomplete_apps_with_scheme_names(self.db)
        assert isinstance(results, list)

        # There should be incomplete records for both schemes
        scheme_ids_in_results = {r["scheme_id"] for r in results}
        # Scheme A has 2 incomplete, Scheme B has 1 incomplete
        assert self.scheme_a in scheme_ids_in_results
        assert self.scheme_b in scheme_ids_in_results

        # Scheme names should be populated (not null/Unknown)
        for r in results:
            assert r.get("scheme_name") not in (None, "Unknown Scheme"), (
                f"$lookup failed to resolve scheme name for {r['scheme_id']}"
            )

        # Scheme A should have more incomplete records than Scheme B
        a_result = next((r for r in results if r["scheme_id"] == self.scheme_a), None)
        b_result = next((r for r in results if r["scheme_id"] == self.scheme_b), None)
        assert a_result is not None
        assert b_result is not None
        assert a_result["incomplete_count"] == 2
        assert b_result["incomplete_count"] == 1

    def test_T17_empty_collection_does_not_crash(self):
        """T17: All pipelines should return empty lists on an empty collection, not crash."""
        from config import TEST_DB_NAME
        from db import get_client
        client = get_client()
        empty_db = client[TEST_DB_NAME + "_empty"]
        client.drop_database(TEST_DB_NAME + "_empty")

        from setup_validators import setup
        setup(TEST_DB_NAME + "_empty")

        empty = client[TEST_DB_NAME + "_empty"]

        try:
            r1 = missing_documents_frequency(empty)
            r2 = applications_by_status(empty)
            r3 = incomplete_applications_by_scheme(empty)
            r4 = incomplete_apps_with_scheme_names(empty)

            assert r1 == []
            assert r2 == []
            assert r3 == []
            assert r4 == []
        finally:
            client.drop_database(TEST_DB_NAME + "_empty")

    def test_dashboard_metrics_correct(self):
        """Dashboard metrics should reflect actual database state."""
        metrics = dashboard_metrics(self.db)

        assert metrics["total_schemes"] == 2
        assert metrics["total_applications"] == 5
        # At least the incomplete applications
        assert metrics["applications_with_missing_docs"] >= 3

    def test_incomplete_by_scheme_ordering(self):
        """Pipeline 3 should return Scheme A before Scheme B (more incomplete)."""
        results = incomplete_applications_by_scheme(self.db)
        scheme_order = [r["scheme_id"] for r in results]
        # Scheme A has 2 incomplete, B has 1 — so A should appear first
        assert scheme_order.index(self.scheme_a) < scheme_order.index(self.scheme_b)
