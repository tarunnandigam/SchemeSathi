"""
queries/aggregation_queries.py
-------------------------------
Demonstrates all four required aggregation pipelines and the optional fifth.
Run directly:  python queries/aggregation_queries.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_db, check_connection
from services.analytics_service import (
    missing_documents_frequency,
    applications_by_status,
    incomplete_applications_by_scheme,
    incomplete_apps_with_scheme_names,
    stage_duration_analysis,
)
from config import DB_NAME


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run_aggregations(db_name: str = DB_NAME) -> None:
    ok, msg = check_connection(db_name)
    print(f"\n[Connection] {msg}")
    if not ok:
        print("Aborting.")
        return

    db = get_db(db_name)

    # ------------------------------------------------------------------
    separator("Pipeline 1: Most Frequently Missing Documents")
    # ------------------------------------------------------------------
    print("""
  Business question: Which document types appear most often in incomplete
  application records? Helps prioritise outreach and guidance.

  Stages:
    $match   -> only applications with missing_documents (non-empty array)
    $unwind  -> expand array to one document per element
    $group   -> count occurrences per document type
    $sort    -> descending count
    $project -> rename _id to document_type
    """)
    results = missing_documents_frequency(db)
    if results:
        print(f"  {'Document Type':<40} {'Count':>5}")
        print(f"  {'-'*45}")
        for r in results:
            print(f"  {r['document_type']:<40} {r['count']:>5}")
    else:
        print("  No incomplete applications found.")

    # ------------------------------------------------------------------
    separator("Pipeline 2: Applications by Status")
    # ------------------------------------------------------------------
    print("""
  Business question: How many application records are in each status?
  Useful for tracking overall pipeline progression.

  Stages:
    $group   -> group by application_status, count records
    $sort    -> descending count
    $project -> rename _id to status
    """)
    results = applications_by_status(db)
    if results:
        print(f"  {'Status':<25} {'Count':>5}")
        print(f"  {'-'*32}")
        for r in results:
            print(f"  {r['status']:<25} {r['count']:>5}")
    else:
        print("  No applications found.")

    # ------------------------------------------------------------------
    separator("Pipeline 3: Incomplete Applications by Scheme")
    # ------------------------------------------------------------------
    print("""
  Business question: Which schemes have the most incomplete records?
  Identifies where applicants are struggling most.

  Stages:
    $match   -> records with non-empty missing_documents
    $group   -> count incomplete records per scheme_id
    $sort    -> descending count
    $project -> clean output
    """)
    results = incomplete_applications_by_scheme(db)
    if results:
        print(f"  {'Scheme ID':<15} {'Incomplete Count':>18}")
        print(f"  {'-'*35}")
        for r in results:
            print(f"  {r['scheme_id']:<15} {r['incomplete_count']:>18}")
    else:
        print("  No incomplete applications found.")

    # ------------------------------------------------------------------
    separator("Pipeline 4: Scheme Names + Incomplete Counts ($lookup)")
    # ------------------------------------------------------------------
    print("""
  Business question: Show human-readable scheme names alongside incomplete
  application counts. Uses $lookup to join the schemes collection.

  Stages:
    $match   -> incomplete applications
    $group   -> count per scheme_id
    $lookup  -> join schemes on scheme_id
    $unwind  -> flatten the joined array
    $project -> scheme_name, category, incomplete_count
    $sort    -> descending incomplete_count
    """)
    results = incomplete_apps_with_scheme_names(db)
    if results:
        print(f"  {'Scheme Name':<45} {'Category':<22} {'Incomplete':>10}")
        print(f"  {'-'*80}")
        for r in results:
            name = r.get("scheme_name", "?")[:43]
            cat = r.get("category", "?")[:20]
            print(f"  {name:<45} {cat:<22} {r['incomplete_count']:>10}")
    else:
        print("  No data.")

    # ------------------------------------------------------------------
    separator("Pipeline 5 (Optional): Stage Duration Analysis")
    # ------------------------------------------------------------------
    print("""
  Business question: On average, how many days does it take for an application
  to reach a terminal status (approved/rejected/withdrawn)?

  Note: Only closed applications are included. Open records are excluded
  so the average is not artificially skewed.

  Stages:
    $match   -> terminal status applications
    $project -> compute duration_days from created_at to updated_at
    $group   -> avg duration per status
    $project -> clean output
    $sort    -> ascending avg_days
    """)
    results = stage_duration_analysis(db)
    if results:
        print(f"  {'Final Status':<20} {'Avg Days':>10} {'Records':>8}")
        print(f"  {'-'*42}")
        for r in results:
            print(f"  {r['final_status']:<20} {r['avg_days_to_complete']:>10} {r['record_count']:>8}")
    else:
        print("  No closed applications in dataset.")

    print("\n[Aggregation Demo] Complete.\n")


if __name__ == "__main__":
    run_aggregations()
