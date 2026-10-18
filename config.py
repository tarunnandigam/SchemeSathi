"""
config.py
---------
Reads environment variables from .env and exposes them as typed constants.
All other modules import from here — never read os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env if it exists (safe to call even when .env is absent)
load_dotenv()

# MongoDB connection
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME: str = os.getenv("DB_NAME", "scheme_reach")
TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", "scheme_reach_test")

# Collection names — defined once so every module stays in sync
COL_SCHEMES = "schemes"
COL_APPLICATIONS = "applications"
COL_BARRIER_REPORTS = "barrier_reports"

# Permitted application statuses (used by validation and UI)
VALID_STATUSES = [
    "preparation",
    "documents_pending",
    "ready_to_submit",
    "submitted",
    "under_review",
    "approved",
    "rejected",
    "withdrawn",
]

# Permitted barrier categories
VALID_BARRIER_CATEGORIES = [
    "unclear_instructions",
    "document_difficulty",
    "application_process",
    "technical_issue",
    "other",
]
