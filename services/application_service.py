"""
services/application_service.py
--------------------------------
All CRUD operations for the 'applications' collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pymongo.database import Database
from pymongo.errors import WriteError

from config import COL_APPLICATIONS, COL_SCHEMES, VALID_STATUSES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _next_app_ref(db: Database) -> str:
    """Generate next APP-NNNNNN identifier."""
    last = db[COL_APPLICATIONS].find_one(
        {}, sort=[("application_ref", -1)], projection={"application_ref": 1}
    )
    if last and "application_ref" in last:
        num = int(last["application_ref"].split("-")[1]) + 1
    else:
        num = 1
    return f"APP-{num:06d}"


def _calculate_missing(required: list[str], provided: list[str]) -> list[str]:
    """Return documents in required that are not in provided."""
    return [doc for doc in required if doc not in provided]


def _readiness(required: list[str], provided: list[str]) -> float:
    """Return readiness percentage (0–100).  Returns 100 when no documents required."""
    if not required:
        return 100.0
    matched = len([d for d in required if d in provided])
    return round((matched / len(required)) * 100, 1)


def _stage_entry(stage: str, note: str = "") -> dict:
    return {"stage": stage, "timestamp": _now(), "note": note}


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def create_application(db: Database, data: dict) -> dict:
    """
    Create a new simulated application record.
    data keys: scheme_id, applicant_alias, documents_provided
    Returns {"success": True, "application_ref": "APP-..."} or {"success": False, "error": "..."}
    """
    scheme_id = data.get("scheme_id", "")
    scheme = db[COL_SCHEMES].find_one({"scheme_id": scheme_id})
    if not scheme:
        return {"success": False, "error": f"Scheme '{scheme_id}' not found."}

    required = scheme.get("required_documents", [])
    provided = [d.strip() for d in data.get("documents_provided", []) if d.strip()]
    missing = _calculate_missing(required, provided)

    status = "documents_pending" if missing else "ready_to_submit"
    app_ref = _next_app_ref(db)
    now = _now()

    doc = {
        "application_ref": app_ref,
        "scheme_id": scheme_id,
        "applicant_alias": data.get("applicant_alias", "Anonymous"),
        "documents_provided": provided,
        "missing_documents": missing,
        "application_status": status,
        "stage_history": [
            _stage_entry("preparation", "Application record created"),
            _stage_entry(status, "Initial document assessment"),
        ],
        "created_at": now,
        "updated_at": now,
    }

    try:
        db[COL_APPLICATIONS].insert_one(doc)
        return {
            "success": True,
            "application_ref": app_ref,
            "status": status,
            "missing_documents": missing,
            "readiness_pct": _readiness(required, provided),
        }
    except WriteError as exc:
        return {
            "success": False,
            "error": f"Validation error: {exc.details.get('errmsg', str(exc))}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_application(db: Database, app_ref: str) -> Optional[dict]:
    return db[COL_APPLICATIONS].find_one({"application_ref": app_ref}, {"_id": 0})


def list_applications(db: Database, status_filter: str = "", scheme_filter: str = "") -> list[dict]:
    filt: dict = {}
    if status_filter:
        filt["application_status"] = status_filter
    if scheme_filter:
        filt["scheme_id"] = scheme_filter
    return list(db[COL_APPLICATIONS].find(filt, {"_id": 0}).sort("created_at", -1))


def get_checklist_summary(db: Database, app_ref: str) -> Optional[dict]:
    """
    Return a checklist summary for an application:
    required, provided, missing, readiness%.
    """
    app = get_application(db, app_ref)
    if not app:
        return None
    scheme = db[COL_SCHEMES].find_one({"scheme_id": app["scheme_id"]}, {"_id": 0})
    if not scheme:
        return None

    required = scheme.get("required_documents", [])
    provided = app.get("documents_provided", [])
    missing = _calculate_missing(required, provided)
    pct = _readiness(required, provided)

    return {
        "application": app,
        "scheme": scheme,
        "required_documents": required,
        "documents_provided": provided,
        "missing_documents": missing,
        "readiness_pct": pct,
    }


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_documents(db: Database, app_ref: str, new_provided: list[str]) -> dict:
    """
    Replace the documents_provided list and recalculate missing_documents.
    Appends a stage-history entry.
    """
    app = get_application(db, app_ref)
    if not app:
        return {"success": False, "error": f"Application '{app_ref}' not found."}

    scheme = db[COL_SCHEMES].find_one({"scheme_id": app["scheme_id"]}, {"_id": 0})
    if not scheme:
        return {"success": False, "error": "Referenced scheme not found."}

    required = scheme.get("required_documents", [])
    provided = [d.strip() for d in new_provided if d.strip()]
    missing = _calculate_missing(required, provided)
    new_status = "documents_pending" if missing else "ready_to_submit"

    stage = _stage_entry(new_status, "Document checklist updated")

    try:
        result = db[COL_APPLICATIONS].update_one(
            {"application_ref": app_ref},
            {
                "$set": {
                    "documents_provided": provided,
                    "missing_documents": missing,
                    "application_status": new_status,
                    "updated_at": _now(),
                },
                "$push": {"stage_history": stage},
            },
        )
        return {
            "success": True,
            "modified": result.modified_count,
            "new_status": new_status,
            "missing_documents": missing,
            "readiness_pct": _readiness(required, provided),
        }
    except WriteError as exc:
        return {
            "success": False,
            "error": f"Validation error: {exc.details.get('errmsg', str(exc))}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


def update_status(db: Database, app_ref: str, new_status: str, note: str = "") -> dict:
    """
    Update application_status and push a stage_history entry.
    """
    if new_status not in VALID_STATUSES:
        return {
            "success": False,
            "error": f"'{new_status}' is not a valid status. Choose from {VALID_STATUSES}.",
        }

    app = get_application(db, app_ref)
    if not app:
        return {"success": False, "error": f"Application '{app_ref}' not found."}

    stage = _stage_entry(new_status, note or f"Status changed to {new_status}")

    try:
        result = db[COL_APPLICATIONS].update_one(
            {"application_ref": app_ref},
            {
                "$set": {
                    "application_status": new_status,
                    "updated_at": _now(),
                },
                "$push": {"stage_history": stage},
            },
        )
        return {"success": True, "modified": result.modified_count}
    except WriteError as exc:
        return {
            "success": False,
            "error": f"Validation error: {exc.details.get('errmsg', str(exc))}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_application(db: Database, app_ref: str) -> dict:
    """Delete an application by reference."""
    result = db[COL_APPLICATIONS].delete_one({"application_ref": app_ref})
    if result.deleted_count == 0:
        return {"success": False, "error": f"Application '{app_ref}' not found."}
    return {"success": True}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def readiness_pct(required: list[str], provided: list[str]) -> float:
    return _readiness(required, provided)
