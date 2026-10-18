"""
queries/crud_operations.py
--------------------------
Standalone demonstration of CRUD operations.
Run directly:  python queries/crud_operations.py
"""

from __future__ import annotations

import sys
import os

# Allow running from either the project root or the queries/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_db, check_connection
from services.scheme_service import (
    create_scheme,
    get_scheme_by_id,
    list_active_schemes,
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
)
from config import DB_NAME


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run_demo(db_name: str = DB_NAME) -> None:
    ok, msg = check_connection(db_name)
    print(f"\n[Connection] {msg}")
    if not ok:
        print("Aborting - MongoDB is not reachable.")
        return

    db = get_db(db_name)

    # ------------------------------------------------------------------
    separator("CREATE - Insert a test scheme")
    # ------------------------------------------------------------------
    test_scheme_data = {
        "name": "Test Demo Scheme (CRUD Demo)",
        "category": "Testing",
        "department": "Test Department",
        "description": "Fictional scheme created by the CRUD demo script.",
        "benefits_description": "No real benefit - demo only.",
        "eligibility_criteria": ["Must be a test record"],
        "required_documents": ["identity_proof", "test_document"],
        "official_url": None,
        "source_verified": False,
        "active": True,
    }
    create_result = create_scheme(db, test_scheme_data)
    print(f"  Result: {create_result}")
    test_scheme_id = create_result.get("scheme_id")

    # ------------------------------------------------------------------
    separator("READ - List all active schemes (first 3)")
    # ------------------------------------------------------------------
    schemes = list_active_schemes(db)
    for s in schemes[:3]:
        print(f"  {s.get('scheme_id')} | {s.get('name')} | {s.get('category')}")
    print(f"  ... total active schemes: {len(schemes)}")

    # ------------------------------------------------------------------
    separator("READ - Get scheme by ID")
    # ------------------------------------------------------------------
    if test_scheme_id:
        scheme = get_scheme_by_id(db, test_scheme_id)
        print(f"  Found: {scheme.get('name')} | Active: {scheme.get('active')}")

    # ------------------------------------------------------------------
    separator("CREATE - Insert a test application")
    # ------------------------------------------------------------------
    test_app_data = {
        "scheme_id": test_scheme_id,
        "applicant_alias": "CRUD Demo User",
        "documents_provided": ["identity_proof"],
    }
    app_result = create_application(db, test_app_data)
    print(f"  Result: {app_result}")
    test_app_ref = app_result.get("application_ref")

    # ------------------------------------------------------------------
    separator("READ - Get application by reference")
    # ------------------------------------------------------------------
    if test_app_ref:
        app = get_application(db, test_app_ref)
        print(f"  Found: {app.get('application_ref')} | Status: {app.get('application_status')}")
        print(f"  Missing docs: {app.get('missing_documents')}")

    # ------------------------------------------------------------------
    separator("UPDATE - Add missing document, recalculate checklist")
    # ------------------------------------------------------------------
    if test_app_ref:
        upd = update_documents(db, test_app_ref, ["identity_proof", "test_document"])
        print(f"  Result: {upd}")
        app = get_application(db, test_app_ref)
        print(f"  New status: {app.get('application_status')}")
        print(f"  Missing docs: {app.get('missing_documents')}")

    # ------------------------------------------------------------------
    separator("UPDATE - Change status to 'submitted'")
    # ------------------------------------------------------------------
    if test_app_ref:
        st_upd = update_status(db, test_app_ref, "submitted", "Demo status update")
        print(f"  Result: {st_upd}")
        app = get_application(db, test_app_ref)
        print(f"  Stage history entries: {len(app.get('stage_history', []))}")

    # ------------------------------------------------------------------
    separator("UPDATE - Modify the test scheme's description")
    # ------------------------------------------------------------------
    if test_scheme_id:
        sch_upd = update_scheme(db, test_scheme_id, {"description": "Updated by CRUD demo."})
        print(f"  Result: {sch_upd}")

    # ------------------------------------------------------------------
    separator("DELETE - Delete the test application")
    # ------------------------------------------------------------------
    if test_app_ref:
        del_app = delete_application(db, test_app_ref)
        print(f"  Result: {del_app}")

    # ------------------------------------------------------------------
    separator("DELETE - Try to delete a scheme that still has references")
    # ------------------------------------------------------------------
    # Use a known scheme that has seeded applications
    del_scheme_attempt = delete_scheme(db, "SCH-000001")
    print(f"  Expected failure: {del_scheme_attempt}")

    # ------------------------------------------------------------------
    separator("DELETE - Delete the test scheme (no references)")
    # ------------------------------------------------------------------
    if test_scheme_id:
        del_sch = delete_scheme(db, test_scheme_id)
        print(f"  Result: {del_sch}")

    # ------------------------------------------------------------------
    separator("VALIDATION - Attempt to insert an invalid scheme")
    # ------------------------------------------------------------------
    invalid_scheme = {
        "name": "",          # violates minLength:2
        "category": "Test",
        "department": "Test Dept",
        "active": True,
        # missing created_at and updated_at - will fail validation
    }
    # We bypass the service to hit the validator directly
    from datetime import datetime, timezone
    from pymongo.errors import WriteError
    try:
        db["schemes"].insert_one(invalid_scheme)
        print("  ERROR: Invalid document was accepted - check validators!")
    except WriteError as exc:
        print(f"  Correctly rejected: {exc.details.get('errmsg', str(exc))[:100]}")
    except Exception as exc:  # noqa: BLE001
        print(f"  Rejected with: {type(exc).__name__}: {str(exc)[:100]}")

    print("\n[CRUD Demo] Complete.\n")


if __name__ == "__main__":
    run_demo()
