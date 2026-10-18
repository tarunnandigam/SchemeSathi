"""
services/analytics_service.py
------------------------------
Runs the four required aggregation pipelines and returns results as lists of dicts.
All pipelines execute through PyMongo's db.collection.aggregate().
"""

from __future__ import annotations

from pymongo.database import Database

from config import COL_APPLICATIONS, COL_SCHEMES


# ---------------------------------------------------------------------------
# Pipeline 1: Most frequently missing documents
# ---------------------------------------------------------------------------

def missing_documents_frequency(db: Database) -> list[dict]:
    """
    Business question: Which document categories appear most often in
    incomplete application records?

    Pipeline stages:
      1. $match  — only records with at least one missing document
      2. $unwind — explode the missing_documents array into individual docs
      3. $group  — count occurrences per document type
      4. $sort   — descending count
      5. $project — rename _id to document_type
    """
    pipeline = [
        {"$match": {"missing_documents": {"$exists": True, "$ne": []}}},
        {"$unwind": "$missing_documents"},
        {
            "$group": {
                "_id": "$missing_documents",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {
            "$project": {
                "_id": 0,
                "document_type": "$_id",
                "count": 1,
            }
        },
    ]
    return list(db[COL_APPLICATIONS].aggregate(pipeline))


# ---------------------------------------------------------------------------
# Pipeline 2: Applications by status
# ---------------------------------------------------------------------------

def applications_by_status(db: Database) -> list[dict]:
    """
    Business question: How many application records are in each status?

    Pipeline stages:
      1. $group  — group by application_status, count records
      2. $sort   — descending count
      3. $project — rename _id to status
    """
    pipeline = [
        {
            "$group": {
                "_id": "$application_status",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {
            "$project": {
                "_id": 0,
                "status": "$_id",
                "count": 1,
            }
        },
    ]
    return list(db[COL_APPLICATIONS].aggregate(pipeline))


# ---------------------------------------------------------------------------
# Pipeline 3: Incomplete applications by scheme (by scheme_id)
# ---------------------------------------------------------------------------

def incomplete_applications_by_scheme(db: Database) -> list[dict]:
    """
    Business question: Which schemes have the most incomplete application records
    (i.e., records with at least one missing document)?

    Pipeline stages:
      1. $match  — records with non-empty missing_documents
      2. $group  — count per scheme_id
      3. $sort   — descending count
      4. $project — clean output
    """
    pipeline = [
        {"$match": {"missing_documents": {"$exists": True, "$ne": []}}},
        {
            "$group": {
                "_id": "$scheme_id",
                "incomplete_count": {"$sum": 1},
            }
        },
        {"$sort": {"incomplete_count": -1}},
        {
            "$project": {
                "_id": 0,
                "scheme_id": "$_id",
                "incomplete_count": 1,
            }
        },
    ]
    return list(db[COL_APPLICATIONS].aggregate(pipeline))


# ---------------------------------------------------------------------------
# Pipeline 4: Scheme names and incomplete application counts ($lookup)
# ---------------------------------------------------------------------------

def incomplete_apps_with_scheme_names(db: Database) -> list[dict]:
    """
    Business question: Show readable scheme names alongside the count of
    incomplete application records for each scheme.

    Pipeline stages:
      1. $match    — records with non-empty missing_documents
      2. $group    — count per scheme_id
      3. $lookup   — join schemes collection on scheme_id
      4. $unwind   — flatten the joined array (should be one element)
      5. $project  — scheme_name, scheme_id, incomplete_count
      6. $sort     — descending incomplete_count
    """
    pipeline = [
        {"$match": {"missing_documents": {"$exists": True, "$ne": []}}},
        {
            "$group": {
                "_id": "$scheme_id",
                "incomplete_count": {"$sum": 1},
            }
        },
        {
            "$lookup": {
                "from": COL_SCHEMES,
                "localField": "_id",
                "foreignField": "scheme_id",
                "as": "scheme_info",
            }
        },
        {
            "$unwind": {
                "path": "$scheme_info",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$project": {
                "_id": 0,
                "scheme_id": "$_id",
                "scheme_name": {"$ifNull": ["$scheme_info.name", "Unknown Scheme"]},
                "category": {"$ifNull": ["$scheme_info.category", "—"]},
                "incomplete_count": 1,
            }
        },
        {"$sort": {"incomplete_count": -1}},
    ]
    return list(db[COL_APPLICATIONS].aggregate(pipeline))


# ---------------------------------------------------------------------------
# Optional Pipeline 5: Average stage durations
# ---------------------------------------------------------------------------

def stage_duration_analysis(db: Database) -> list[dict]:
    """
    Business question: On average, how many days does an application spend
    between creation (preparation) and final update?

    Handles:
     - Applications that are still in progress (not yet approved/rejected)
       are excluded from the final duration calculation.
     - Only applications with valid timestamps are used.
    """
    pipeline = [
        {
            "$match": {
                "application_status": {"$in": ["approved", "rejected", "withdrawn"]},
                "created_at": {"$exists": True},
                "updated_at": {"$exists": True},
            }
        },
        {
            "$project": {
                "scheme_id": 1,
                "application_status": 1,
                "duration_days": {
                    "$divide": [
                        {"$subtract": ["$updated_at", "$created_at"]},
                        1000 * 60 * 60 * 24,  # ms → days
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$application_status",
                "avg_days": {"$avg": "$duration_days"},
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "final_status": "$_id",
                "avg_days_to_complete": {"$round": ["$avg_days", 1]},
                "record_count": "$count",
            }
        },
        {"$sort": {"avg_days_to_complete": 1}},
    ]
    return list(db[COL_APPLICATIONS].aggregate(pipeline))


# ---------------------------------------------------------------------------
# Dashboard summary queries (not aggregation pipelines — simple counts)
# ---------------------------------------------------------------------------

def dashboard_metrics(db: Database) -> dict:
    """Return counts for the home dashboard using MongoDB queries."""
    total_schemes = db[COL_SCHEMES].count_documents({"active": True})
    total_apps = db[COL_APPLICATIONS].count_documents({})
    missing_docs_count = db[COL_APPLICATIONS].count_documents(
        {"missing_documents": {"$ne": []}}
    )

    # Count per status
    status_counts_raw = applications_by_status(db)
    status_counts = {row["status"]: row["count"] for row in status_counts_raw}

    return {
        "total_schemes": total_schemes,
        "total_applications": total_apps,
        "applications_with_missing_docs": missing_docs_count,
        "status_counts": status_counts,
    }
