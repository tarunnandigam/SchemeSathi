"""
services/scheme_service.py
--------------------------
All CRUD operations for the 'schemes' collection.
Every function works through PyMongo and returns plain Python dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, WriteError

from config import COL_SCHEMES, COL_APPLICATIONS


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def _next_scheme_id(db: Database) -> str:
    """Generate next SCH-NNNNNN identifier."""
    last = db[COL_SCHEMES].find_one(
        {}, sort=[("scheme_id", -1)], projection={"scheme_id": 1}
    )
    if last and "scheme_id" in last:
        num = int(last["scheme_id"].split("-")[1]) + 1
    else:
        num = 1
    return f"SCH-{num:06d}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def create_scheme(db: Database, data: dict) -> dict:
    """
    Insert a new scheme document.
    Returns {"success": True, "scheme_id": "SCH-..."} or {"success": False, "error": "..."}
    """
    scheme_id = _next_scheme_id(db)
    now = _now()

    doc = {
        "scheme_id": scheme_id,
        "name": data.get("name", ""),
        "category": data.get("category", ""),
        "department": data.get("department", ""),
        "description": data.get("description", ""),
        "benefits_description": data.get("benefits_description", ""),
        "eligibility_criteria": data.get("eligibility_criteria", []),
        "required_documents": data.get("required_documents", []),
        "official_url": data.get("official_url") or None,
        "source_verified": bool(data.get("source_verified", False)),
        "active": bool(data.get("active", True)),
        "created_at": now,
        "updated_at": now,
    }

    try:
        db[COL_SCHEMES].insert_one(doc)
        return {"success": True, "scheme_id": scheme_id}
    except WriteError as exc:
        return {"success": False, "error": f"Validation error: {exc.details.get('errmsg', str(exc))}"}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def list_active_schemes(db: Database) -> list[dict]:
    """Return all active schemes (without internal _id)."""
    return list(
        db[COL_SCHEMES].find({"active": True}, {"_id": 0}).sort("name", 1)
    )


def get_scheme_by_id(db: Database, scheme_id: str) -> Optional[dict]:
    """Find a scheme by its scheme_id string."""
    return db[COL_SCHEMES].find_one({"scheme_id": scheme_id}, {"_id": 0})


def search_schemes_by_name(db: Database, query: str) -> list[dict]:
    """Case-insensitive name search."""
    return list(
        db[COL_SCHEMES].find(
            {"name": {"$regex": query, "$options": "i"}},
            {"_id": 0},
        ).sort("name", 1)
    )


def filter_schemes(db: Database, category: str = "", department: str = "") -> list[dict]:
    """Filter active schemes by category and/or department."""
    filt: dict = {"active": True}
    if category:
        filt["category"] = {"$regex": category, "$options": "i"}
    if department:
        filt["department"] = {"$regex": department, "$options": "i"}
    return list(db[COL_SCHEMES].find(filt, {"_id": 0}).sort("name", 1))


def get_all_categories(db: Database) -> list[str]:
    return sorted(db[COL_SCHEMES].distinct("category"))


def get_all_departments(db: Database) -> list[str]:
    return sorted(db[COL_SCHEMES].distinct("department"))


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_scheme(db: Database, scheme_id: str, updates: dict) -> dict:
    """
    Update allowed fields of a scheme.
    Always sets updated_at.
    Returns {"success": True, "modified": n} or {"success": False, "error": "..."}
    """
    allowed_fields = {
        "name", "category", "department", "description",
        "benefits_description", "eligibility_criteria",
        "required_documents", "official_url", "source_verified", "active",
    }
    set_fields = {k: v for k, v in updates.items() if k in allowed_fields}
    if not set_fields:
        return {"success": False, "error": "No valid fields to update."}

    set_fields["updated_at"] = _now()

    try:
        result = db[COL_SCHEMES].update_one(
            {"scheme_id": scheme_id},
            {"$set": set_fields},
        )
        if result.matched_count == 0:
            return {"success": False, "error": f"Scheme '{scheme_id}' not found."}
        return {"success": True, "modified": result.modified_count}
    except WriteError as exc:
        return {"success": False, "error": f"Validation error: {exc.details.get('errmsg', str(exc))}"}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_scheme(db: Database, scheme_id: str) -> dict:
    """
    Delete a scheme ONLY when no application references it.
    Returns {"success": True} or {"success": False, "error": "..."}
    """
    # Check for referencing applications
    ref_count = db[COL_APPLICATIONS].count_documents({"scheme_id": scheme_id})
    if ref_count > 0:
        return {
            "success": False,
            "error": (
                f"Cannot delete scheme '{scheme_id}': "
                f"{ref_count} application record(s) reference it. "
                "Delete those applications first."
            ),
        }

    result = db[COL_SCHEMES].delete_one({"scheme_id": scheme_id})
    if result.deleted_count == 0:
        return {"success": False, "error": f"Scheme '{scheme_id}' not found."}
    return {"success": True}
