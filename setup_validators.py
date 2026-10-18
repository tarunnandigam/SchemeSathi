"""
setup_validators.py
-------------------
Creates (or recreates) the MongoDB collections with JSON Schema validators.

Run once before seeding:
    python setup_validators.py

Safe to rerun:  existing validators are replaced, existing data is preserved.
"""

from __future__ import annotations

from datetime import datetime

import pymongo
from pymongo.errors import CollectionInvalid, OperationFailure

from config import (
    DB_NAME,
    COL_SCHEMES,
    COL_APPLICATIONS,
    COL_BARRIER_REPORTS,
    VALID_STATUSES,
    VALID_BARRIER_CATEGORIES,
)
from db import get_db


# ---------------------------------------------------------------------------
# JSON Schema definitions
# ---------------------------------------------------------------------------

SCHEMES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "category", "department", "active", "created_at", "updated_at"],
        "additionalProperties": True,
        "properties": {
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "description": "Scheme name — required, non-empty string",
            },
            "category": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Scheme category — required string",
            },
            "department": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Responsible department — required string",
            },
            "description": {
                "bsonType": "string",
                "description": "Scheme description — optional string",
            },
            "benefits_description": {
                "bsonType": "string",
                "description": "Benefits summary — optional string",
            },
            "eligibility_criteria": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of eligibility criterion strings",
            },
            "required_documents": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of required document identifier strings",
            },
            "official_url": {
                "bsonType": ["string", "null"],
                "description": "Official government URL — string or null",
            },
            "source_verified": {
                "bsonType": "bool",
                "description": "True when information has been verified from an official source",
            },
            "active": {
                "bsonType": "bool",
                "description": "Whether this scheme is currently active",
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp — BSON Date",
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Last update timestamp — BSON Date",
            },
        },
    }
}

APPLICATIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "application_ref",
            "scheme_id",
            "documents_provided",
            "missing_documents",
            "application_status",
            "stage_history",
            "created_at",
            "updated_at",
        ],
        "additionalProperties": True,
        "properties": {
            "application_ref": {
                "bsonType": "string",
                "pattern": "^APP-[0-9]{6}$",
                "description": "Application reference in format APP-NNNNNN",
            },
            "scheme_id": {
                "bsonType": "string",
                "pattern": "^SCH-[0-9]{6}$",
                "description": "Scheme identifier in format SCH-NNNNNN",
            },
            "applicant_alias": {
                "bsonType": "string",
                "description": "Optional display name / pseudonym",
            },
            "documents_provided": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Documents recorded as provided",
            },
            "missing_documents": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Documents still missing",
            },
            "application_status": {
                "bsonType": "string",
                "enum": VALID_STATUSES,
                "description": f"Current status — one of {VALID_STATUSES}",
            },
            "stage_history": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["stage", "timestamp"],
                    "properties": {
                        "stage": {"bsonType": "string"},
                        "timestamp": {"bsonType": "date"},
                        "note": {"bsonType": "string"},
                    },
                },
                "description": "Ordered list of stage entries with timestamps",
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp — BSON Date",
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Last update timestamp — BSON Date",
            },
        },
    }
}

BARRIER_REPORTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["scheme_id", "barrier_category", "description", "reported_at", "record_type"],
        "additionalProperties": True,
        "properties": {
            "scheme_id": {
                "bsonType": "string",
                "description": "Referenced scheme identifier",
            },
            "barrier_category": {
                "bsonType": "string",
                "enum": VALID_BARRIER_CATEGORIES,
                "description": f"Category of barrier — one of {VALID_BARRIER_CATEGORIES}",
            },
            "description": {
                "bsonType": "string",
                "minLength": 5,
                "description": "Description of the reported barrier",
            },
            "reported_at": {
                "bsonType": "date",
                "description": "Report timestamp — BSON Date",
            },
            "record_type": {
                "bsonType": "string",
                "enum": ["synthetic", "verified"],
                "description": "synthetic = test data, verified = confirmed real-world report",
            },
        },
    }
}


# ---------------------------------------------------------------------------
# Helper to create / update a collection with a validator
# ---------------------------------------------------------------------------

def _ensure_collection(db, name: str, schema: dict) -> None:
    """Create collection if missing; always apply / replace the validator."""
    existing = db.list_collection_names()

    if name not in existing:
        db.create_collection(
            name,
            validator=schema,
            validationLevel="strict",
            validationAction="error",
        )
        print(f"  [+] Created collection '{name}' with validator.")
    else:
        # Update the validator on the existing collection
        db.command(
            "collMod",
            name,
            validator=schema,
            validationLevel="strict",
            validationAction="error",
        )
        print(f"  [~] Updated validator on existing collection '{name}'.")


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

def _create_indexes(db) -> None:
    """Create indexes for common query patterns."""
    # schemes
    db[COL_SCHEMES].create_index("name")
    db[COL_SCHEMES].create_index("category")
    db[COL_SCHEMES].create_index("department")

    # applications
    db[COL_APPLICATIONS].create_index(
        "application_ref", unique=True, name="uq_application_ref"
    )
    db[COL_APPLICATIONS].create_index("scheme_id")
    db[COL_APPLICATIONS].create_index("application_status")

    print("  [+] Indexes created / verified.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def setup(db_name: str = DB_NAME) -> None:
    print(f"\n[SchemeReach] Setting up database: '{db_name}'\n")
    db = get_db(db_name)

    _ensure_collection(db, COL_SCHEMES, SCHEMES_SCHEMA)
    _ensure_collection(db, COL_APPLICATIONS, APPLICATIONS_SCHEMA)
    _ensure_collection(db, COL_BARRIER_REPORTS, BARRIER_REPORTS_SCHEMA)
    _create_indexes(db)

    print("\n  Setup complete.\n")


if __name__ == "__main__":
    setup()
