"""
seed_data.py
------------
Loads sample data into the scheme_reach database.

Run:
    python seed_data.py

Idempotent:  checks for existing records by scheme_id / application_ref
so duplicate seeding is safe.

NOTE: Scheme information is either:
  - Fictional / clearly labelled for testing (source_verified=False), or
  - Based on publicly known scheme names with source_verified=False until
    individually verified against official government portals.
This prototype does NOT claim official government data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from config import DB_NAME, COL_SCHEMES, COL_APPLICATIONS, COL_BARRIER_REPORTS
from db import get_db
from setup_validators import setup


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------

def _ts(year: int, month: int, day: int, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)


NOW = datetime(2026, 10, 18, 10, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Sample schemes (5–8 as required)
# ---------------------------------------------------------------------------

SCHEMES = [
    {
        "scheme_id": "SCH-000001",
        "name": "PM Vidya Scholarship (Fictional Example)",
        "category": "Education",
        "department": "Ministry of Education (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — This scheme is created for academic demonstration. "
            "It provides financial assistance to meritorious students from economically "
            "weaker sections to pursue higher education."
        ),
        "benefits_description": "Annual scholarship amount for tuition and living expenses (fictional).",
        "eligibility_criteria": [
            "Student must have passed Class 12 with minimum 60% marks",
            "Annual family income below ₹2.5 lakh (fictional threshold)",
            "Must be enrolled in a recognised institution",
        ],
        "required_documents": [
            "identity_proof",
            "income_certificate",
            "class_12_marksheet",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 1, 5),
        "updated_at": _ts(2026, 1, 5),
    },
    {
        "scheme_id": "SCH-000002",
        "name": "Rural Health Coverage Scheme (Fictional Example)",
        "category": "Health",
        "department": "Ministry of Health and Family Welfare (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Provides health insurance coverage to rural families "
            "below the poverty line for hospitalisation and critical illness treatment."
        ),
        "benefits_description": "Annual health cover up to ₹5 lakh per family (fictional).",
        "eligibility_criteria": [
            "Resident of a rural area as per local records",
            "Family included in the BPL (below poverty line) list",
            "Valid ration card holder",
        ],
        "required_documents": [
            "identity_proof",
            "ration_card",
            "bpl_certificate",
            "residence_proof",
            "family_composition_certificate",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 1, 10),
        "updated_at": _ts(2026, 1, 10),
    },
    {
        "scheme_id": "SCH-000003",
        "name": "Women Entrepreneur Support Programme (Fictional Example)",
        "category": "Women Empowerment",
        "department": "Ministry of Women and Child Development (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Offers collateral-free micro-loans and skill training "
            "to women entrepreneurs in the informal economy."
        ),
        "benefits_description": "Loan up to ₹1 lakh at subsidised interest with training support (fictional).",
        "eligibility_criteria": [
            "Applicant must be a woman aged 18–55",
            "Must be engaged in or planning a micro or small enterprise",
            "Must not have defaulted on any government loan previously",
        ],
        "required_documents": [
            "identity_proof",
            "age_proof",
            "residence_proof",
            "business_plan_document",
            "self_declaration_form",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 2, 1),
        "updated_at": _ts(2026, 2, 1),
    },
    {
        "scheme_id": "SCH-000004",
        "name": "Skill Development Stipend Scheme (Fictional Example)",
        "category": "Employment",
        "department": "Ministry of Skill Development and Entrepreneurship (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Provides a monthly stipend to youth who enrol in "
            "approved vocational training programmes."
        ),
        "benefits_description": "Monthly stipend during training, plus certification fee reimbursement (fictional).",
        "eligibility_criteria": [
            "Aged 15–35 years",
            "Class 8 pass or above",
            "Enrolled in an approved training centre",
        ],
        "required_documents": [
            "identity_proof",
            "age_proof",
            "educational_qualification_certificate",
            "training_centre_enrolment_letter",
            "bank_passbook_copy",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 2, 15),
        "updated_at": _ts(2026, 2, 15),
    },
    {
        "scheme_id": "SCH-000005",
        "name": "Farmer Input Subsidy Scheme (Fictional Example)",
        "category": "Agriculture",
        "department": "Ministry of Agriculture and Farmers Welfare (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Provides direct subsidy credits for seeds, fertilisers, "
            "and minor irrigation equipment to small and marginal farmers."
        ),
        "benefits_description": "Direct benefit transfer of subsidy amount to registered bank account (fictional).",
        "eligibility_criteria": [
            "Must own or operate agricultural land",
            "Landholding must not exceed 2 hectares",
            "Must be registered in the state farmer database",
        ],
        "required_documents": [
            "identity_proof",
            "land_records",
            "bank_passbook_copy",
            "farmer_registration_certificate",
            "aadhaar_linked_mobile_proof",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 3, 1),
        "updated_at": _ts(2026, 3, 1),
    },
    {
        "scheme_id": "SCH-000006",
        "name": "Senior Citizen Pension Scheme (Fictional Example)",
        "category": "Social Welfare",
        "department": "Ministry of Social Justice and Empowerment (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Provides a monthly pension to elderly citizens who "
            "have no regular income or family support."
        ),
        "benefits_description": "Monthly pension credited to bank account (fictional).",
        "eligibility_criteria": [
            "Age 60 years or above",
            "No regular income exceeding ₹3,000 per month",
            "Indian citizen",
        ],
        "required_documents": [
            "identity_proof",
            "age_proof",
            "income_affidavit",
            "residence_proof",
            "bank_passbook_copy",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 3, 15),
        "updated_at": _ts(2026, 3, 15),
    },
    {
        "scheme_id": "SCH-000007",
        "name": "Housing Assistance for Urban Poor (Fictional Example)",
        "category": "Housing",
        "department": "Ministry of Housing and Urban Affairs (Fictional)",
        "description": (
            "FICTIONAL EXAMPLE — Subsidises construction and improvement of dwelling "
            "units for economically weaker sections in urban areas."
        ),
        "benefits_description": "Grant towards construction linked to project milestones (fictional).",
        "eligibility_criteria": [
            "Urban resident without pucca house",
            "Annual household income below ₹3 lakh",
            "Scheme not availed previously",
        ],
        "required_documents": [
            "identity_proof",
            "income_certificate",
            "residence_proof",
            "land_ownership_proof",
            "no_objection_certificate",
            "bank_passbook_copy",
        ],
        "official_url": None,
        "source_verified": False,
        "active": True,
        "created_at": _ts(2026, 4, 1),
        "updated_at": _ts(2026, 4, 1),
    },
]


# ---------------------------------------------------------------------------
# Helper — build a stage history entry
# ---------------------------------------------------------------------------

def _stage(stage: str, ts: datetime, note: str) -> dict:
    return {"stage": stage, "timestamp": ts, "note": note}


# ---------------------------------------------------------------------------
# Sample applications (25–40 records)
# ---------------------------------------------------------------------------

APPLICATIONS = [
    # --- SCH-000001 : Education ---
    {
        "application_ref": "APP-000001",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Priya S.",
        "documents_provided": [
            "identity_proof",
            "class_12_marksheet",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "missing_documents": ["income_certificate"],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 1), "Record created"),
            _stage("documents_pending", _ts(2026, 5, 2), "Income certificate not yet recorded"),
        ],
        "created_at": _ts(2026, 5, 1),
        "updated_at": _ts(2026, 5, 2),
    },
    {
        "application_ref": "APP-000002",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Ravi M.",
        "documents_provided": [
            "identity_proof",
            "income_certificate",
            "class_12_marksheet",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "ready_to_submit",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 3), "Record created"),
            _stage("ready_to_submit", _ts(2026, 5, 5), "All required documents recorded"),
        ],
        "created_at": _ts(2026, 5, 3),
        "updated_at": _ts(2026, 5, 5),
    },
    {
        "application_ref": "APP-000003",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Anjali K.",
        "documents_provided": ["identity_proof"],
        "missing_documents": [
            "income_certificate",
            "class_12_marksheet",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 10), "Record created"),
            _stage("documents_pending", _ts(2026, 5, 10), "Multiple documents missing"),
        ],
        "created_at": _ts(2026, 5, 10),
        "updated_at": _ts(2026, 5, 10),
    },
    {
        "application_ref": "APP-000004",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Mohan T.",
        "documents_provided": [
            "identity_proof",
            "income_certificate",
            "class_12_marksheet",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "submitted",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 8), "Record created"),
            _stage("ready_to_submit", _ts(2026, 5, 9), "All documents recorded"),
            _stage("submitted", _ts(2026, 5, 10), "Prototype submission recorded"),
        ],
        "created_at": _ts(2026, 5, 8),
        "updated_at": _ts(2026, 5, 10),
    },
    # --- SCH-000002 : Health ---
    {
        "application_ref": "APP-000005",
        "scheme_id": "SCH-000002",
        "applicant_alias": "Savita B.",
        "documents_provided": [
            "identity_proof",
            "ration_card",
        ],
        "missing_documents": [
            "bpl_certificate",
            "residence_proof",
            "family_composition_certificate",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 12), "Record created"),
            _stage("documents_pending", _ts(2026, 5, 12), "Three documents missing"),
        ],
        "created_at": _ts(2026, 5, 12),
        "updated_at": _ts(2026, 5, 12),
    },
    {
        "application_ref": "APP-000006",
        "scheme_id": "SCH-000002",
        "applicant_alias": "Ramesh N.",
        "documents_provided": [
            "identity_proof",
            "ration_card",
            "bpl_certificate",
            "residence_proof",
            "family_composition_certificate",
        ],
        "missing_documents": [],
        "application_status": "under_review",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 14), "Record created"),
            _stage("ready_to_submit", _ts(2026, 5, 15), "All documents recorded"),
            _stage("submitted", _ts(2026, 5, 16), "Prototype submission recorded"),
            _stage("under_review", _ts(2026, 5, 20), "Prototype review stage"),
        ],
        "created_at": _ts(2026, 5, 14),
        "updated_at": _ts(2026, 5, 20),
    },
    {
        "application_ref": "APP-000007",
        "scheme_id": "SCH-000002",
        "applicant_alias": "Lakshmi P.",
        "documents_provided": [
            "identity_proof",
            "ration_card",
            "bpl_certificate",
        ],
        "missing_documents": [
            "residence_proof",
            "family_composition_certificate",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 1), "Record created"),
            _stage("documents_pending", _ts(2026, 6, 1), "Residence proof and family certificate missing"),
        ],
        "created_at": _ts(2026, 6, 1),
        "updated_at": _ts(2026, 6, 1),
    },
    {
        "application_ref": "APP-000008",
        "scheme_id": "SCH-000002",
        "applicant_alias": "Arun V.",
        "documents_provided": [
            "identity_proof",
            "ration_card",
            "bpl_certificate",
            "residence_proof",
            "family_composition_certificate",
        ],
        "missing_documents": [],
        "application_status": "approved",
        "stage_history": [
            _stage("preparation", _ts(2026, 4, 10), "Record created"),
            _stage("ready_to_submit", _ts(2026, 4, 11), "Documents complete"),
            _stage("submitted", _ts(2026, 4, 12), "Submitted"),
            _stage("under_review", _ts(2026, 4, 18), "Under review"),
            _stage("approved", _ts(2026, 5, 1), "Prototype approval recorded"),
        ],
        "created_at": _ts(2026, 4, 10),
        "updated_at": _ts(2026, 5, 1),
    },
    # --- SCH-000003 : Women Empowerment ---
    {
        "application_ref": "APP-000009",
        "scheme_id": "SCH-000003",
        "applicant_alias": "Meena J.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "residence_proof",
        ],
        "missing_documents": [
            "business_plan_document",
            "self_declaration_form",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 5), "Record created"),
            _stage("documents_pending", _ts(2026, 6, 5), "Business plan and self-declaration missing"),
        ],
        "created_at": _ts(2026, 6, 5),
        "updated_at": _ts(2026, 6, 5),
    },
    {
        "application_ref": "APP-000010",
        "scheme_id": "SCH-000003",
        "applicant_alias": "Radha G.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "residence_proof",
            "business_plan_document",
            "self_declaration_form",
        ],
        "missing_documents": [],
        "application_status": "ready_to_submit",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 10), "Record created"),
            _stage("ready_to_submit", _ts(2026, 6, 12), "All documents recorded"),
        ],
        "created_at": _ts(2026, 6, 10),
        "updated_at": _ts(2026, 6, 12),
    },
    {
        "application_ref": "APP-000011",
        "scheme_id": "SCH-000003",
        "applicant_alias": "Nirmala C.",
        "documents_provided": ["identity_proof"],
        "missing_documents": [
            "age_proof",
            "residence_proof",
            "business_plan_document",
            "self_declaration_form",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 1), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 1), "Most documents missing"),
        ],
        "created_at": _ts(2026, 7, 1),
        "updated_at": _ts(2026, 7, 1),
    },
    # --- SCH-000004 : Employment ---
    {
        "application_ref": "APP-000012",
        "scheme_id": "SCH-000004",
        "applicant_alias": "Suresh D.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "educational_qualification_certificate",
        ],
        "missing_documents": [
            "training_centre_enrolment_letter",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 15), "Record created"),
            _stage("documents_pending", _ts(2026, 6, 15), "Enrolment letter and bank passbook missing"),
        ],
        "created_at": _ts(2026, 6, 15),
        "updated_at": _ts(2026, 6, 15),
    },
    {
        "application_ref": "APP-000013",
        "scheme_id": "SCH-000004",
        "applicant_alias": "Kavya H.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "educational_qualification_certificate",
            "training_centre_enrolment_letter",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "submitted",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 20), "Record created"),
            _stage("ready_to_submit", _ts(2026, 6, 21), "All documents recorded"),
            _stage("submitted", _ts(2026, 6, 22), "Prototype submission"),
        ],
        "created_at": _ts(2026, 6, 20),
        "updated_at": _ts(2026, 6, 22),
    },
    {
        "application_ref": "APP-000014",
        "scheme_id": "SCH-000004",
        "applicant_alias": "Vijay R.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
        ],
        "missing_documents": [
            "educational_qualification_certificate",
            "training_centre_enrolment_letter",
            "bank_passbook_copy",
        ],
        "application_status": "preparation",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 5), "Record created"),
        ],
        "created_at": _ts(2026, 7, 5),
        "updated_at": _ts(2026, 7, 5),
    },
    # --- SCH-000005 : Agriculture ---
    {
        "application_ref": "APP-000015",
        "scheme_id": "SCH-000005",
        "applicant_alias": "Kisan A.",
        "documents_provided": [
            "identity_proof",
            "land_records",
            "bank_passbook_copy",
        ],
        "missing_documents": [
            "farmer_registration_certificate",
            "aadhaar_linked_mobile_proof",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 20), "Record created"),
            _stage("documents_pending", _ts(2026, 5, 20), "Registration cert and mobile proof missing"),
        ],
        "created_at": _ts(2026, 5, 20),
        "updated_at": _ts(2026, 5, 20),
    },
    {
        "application_ref": "APP-000016",
        "scheme_id": "SCH-000005",
        "applicant_alias": "Baldev S.",
        "documents_provided": [
            "identity_proof",
            "land_records",
            "bank_passbook_copy",
            "farmer_registration_certificate",
            "aadhaar_linked_mobile_proof",
        ],
        "missing_documents": [],
        "application_status": "approved",
        "stage_history": [
            _stage("preparation", _ts(2026, 4, 5), "Record created"),
            _stage("ready_to_submit", _ts(2026, 4, 6), "All documents recorded"),
            _stage("submitted", _ts(2026, 4, 7), "Submitted"),
            _stage("approved", _ts(2026, 4, 20), "Prototype approval"),
        ],
        "created_at": _ts(2026, 4, 5),
        "updated_at": _ts(2026, 4, 20),
    },
    {
        "application_ref": "APP-000017",
        "scheme_id": "SCH-000005",
        "applicant_alias": "Gopal M.",
        "documents_provided": ["identity_proof"],
        "missing_documents": [
            "land_records",
            "bank_passbook_copy",
            "farmer_registration_certificate",
            "aadhaar_linked_mobile_proof",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 18), "Record created"),
            _stage("documents_pending", _ts(2026, 6, 18), "Most documents missing"),
        ],
        "created_at": _ts(2026, 6, 18),
        "updated_at": _ts(2026, 6, 18),
    },
    {
        "application_ref": "APP-000018",
        "scheme_id": "SCH-000005",
        "applicant_alias": "Harpreet K.",
        "documents_provided": [
            "identity_proof",
            "land_records",
        ],
        "missing_documents": [
            "bank_passbook_copy",
            "farmer_registration_certificate",
            "aadhaar_linked_mobile_proof",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 2), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 2), "Bank passbook and mobile proof missing"),
        ],
        "created_at": _ts(2026, 7, 2),
        "updated_at": _ts(2026, 7, 2),
    },
    # --- SCH-000006 : Social Welfare ---
    {
        "application_ref": "APP-000019",
        "scheme_id": "SCH-000006",
        "applicant_alias": "Susheela R.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "income_affidavit",
        ],
        "missing_documents": [
            "residence_proof",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 25), "Record created"),
            _stage("documents_pending", _ts(2026, 5, 25), "Residence proof and bank passbook missing"),
        ],
        "created_at": _ts(2026, 5, 25),
        "updated_at": _ts(2026, 5, 25),
    },
    {
        "application_ref": "APP-000020",
        "scheme_id": "SCH-000006",
        "applicant_alias": "Shankar P.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "income_affidavit",
            "residence_proof",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "under_review",
        "stage_history": [
            _stage("preparation", _ts(2026, 5, 5), "Record created"),
            _stage("ready_to_submit", _ts(2026, 5, 6), "All documents recorded"),
            _stage("submitted", _ts(2026, 5, 7), "Submitted"),
            _stage("under_review", _ts(2026, 5, 15), "Under review"),
        ],
        "created_at": _ts(2026, 5, 5),
        "updated_at": _ts(2026, 5, 15),
    },
    {
        "application_ref": "APP-000021",
        "scheme_id": "SCH-000006",
        "applicant_alias": "Draupadi W.",
        "documents_provided": [
            "identity_proof",
            "age_proof",
        ],
        "missing_documents": [
            "income_affidavit",
            "residence_proof",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 10), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 10), "Multiple documents missing"),
        ],
        "created_at": _ts(2026, 7, 10),
        "updated_at": _ts(2026, 7, 10),
    },
    # --- SCH-000007 : Housing ---
    {
        "application_ref": "APP-000022",
        "scheme_id": "SCH-000007",
        "applicant_alias": "Dinesh F.",
        "documents_provided": [
            "identity_proof",
            "income_certificate",
            "residence_proof",
        ],
        "missing_documents": [
            "land_ownership_proof",
            "no_objection_certificate",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 22), "Record created"),
            _stage("documents_pending", _ts(2026, 6, 22), "Land proof, NOC and bank passbook missing"),
        ],
        "created_at": _ts(2026, 6, 22),
        "updated_at": _ts(2026, 6, 22),
    },
    {
        "application_ref": "APP-000023",
        "scheme_id": "SCH-000007",
        "applicant_alias": "Pooja E.",
        "documents_provided": [
            "identity_proof",
            "income_certificate",
            "residence_proof",
            "land_ownership_proof",
            "no_objection_certificate",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "submitted",
        "stage_history": [
            _stage("preparation", _ts(2026, 6, 25), "Record created"),
            _stage("ready_to_submit", _ts(2026, 6, 26), "All documents recorded"),
            _stage("submitted", _ts(2026, 6, 28), "Submitted"),
        ],
        "created_at": _ts(2026, 6, 25),
        "updated_at": _ts(2026, 6, 28),
    },
    {
        "application_ref": "APP-000024",
        "scheme_id": "SCH-000007",
        "applicant_alias": "Ramona L.",
        "documents_provided": [
            "identity_proof",
        ],
        "missing_documents": [
            "income_certificate",
            "residence_proof",
            "land_ownership_proof",
            "no_objection_certificate",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 12), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 12), "Most documents missing"),
        ],
        "created_at": _ts(2026, 7, 12),
        "updated_at": _ts(2026, 7, 12),
    },
    {
        "application_ref": "APP-000025",
        "scheme_id": "SCH-000007",
        "applicant_alias": "Rakesh Q.",
        "documents_provided": [
            "identity_proof",
            "income_certificate",
            "residence_proof",
            "land_ownership_proof",
        ],
        "missing_documents": [
            "no_objection_certificate",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 15), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 15), "NOC and bank passbook missing"),
        ],
        "created_at": _ts(2026, 7, 15),
        "updated_at": _ts(2026, 7, 15),
    },
    # Extra records for richer analytics
    {
        "application_ref": "APP-000026",
        "scheme_id": "SCH-000001",
        "applicant_alias": "Sample User",
        "documents_provided": [
            "identity_proof",
            "class_12_marksheet",
        ],
        "missing_documents": [
            "income_certificate",
            "enrolment_proof",
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 18), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 18), "Multiple missing"),
        ],
        "created_at": _ts(2026, 7, 18),
        "updated_at": _ts(2026, 7, 18),
    },
    {
        "application_ref": "APP-000027",
        "scheme_id": "SCH-000002",
        "applicant_alias": "Test User B",
        "documents_provided": [
            "identity_proof",
            "ration_card",
            "bpl_certificate",
            "residence_proof",
        ],
        "missing_documents": [
            "family_composition_certificate",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 7, 20), "Record created"),
            _stage("documents_pending", _ts(2026, 7, 20), "Family certificate missing"),
        ],
        "created_at": _ts(2026, 7, 20),
        "updated_at": _ts(2026, 7, 20),
    },
    {
        "application_ref": "APP-000028",
        "scheme_id": "SCH-000004",
        "applicant_alias": "Test User C",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "educational_qualification_certificate",
            "training_centre_enrolment_letter",
        ],
        "missing_documents": [
            "bank_passbook_copy",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 8, 1), "Record created"),
            _stage("documents_pending", _ts(2026, 8, 1), "Bank passbook missing"),
        ],
        "created_at": _ts(2026, 8, 1),
        "updated_at": _ts(2026, 8, 1),
    },
    {
        "application_ref": "APP-000029",
        "scheme_id": "SCH-000006",
        "applicant_alias": "Senior Citizen Demo",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "income_affidavit",
            "residence_proof",
            "bank_passbook_copy",
        ],
        "missing_documents": [],
        "application_status": "approved",
        "stage_history": [
            _stage("preparation", _ts(2026, 3, 20), "Record created"),
            _stage("ready_to_submit", _ts(2026, 3, 21), "Complete"),
            _stage("submitted", _ts(2026, 3, 22), "Submitted"),
            _stage("under_review", _ts(2026, 4, 1), "Reviewed"),
            _stage("approved", _ts(2026, 4, 10), "Approved"),
        ],
        "created_at": _ts(2026, 3, 20),
        "updated_at": _ts(2026, 4, 10),
    },
    {
        "application_ref": "APP-000030",
        "scheme_id": "SCH-000003",
        "applicant_alias": "Demo Applicant Z",
        "documents_provided": [
            "identity_proof",
            "age_proof",
            "residence_proof",
            "business_plan_document",
        ],
        "missing_documents": [
            "self_declaration_form",
        ],
        "application_status": "documents_pending",
        "stage_history": [
            _stage("preparation", _ts(2026, 8, 5), "Record created"),
            _stage("documents_pending", _ts(2026, 8, 5), "Self declaration missing"),
        ],
        "created_at": _ts(2026, 8, 5),
        "updated_at": _ts(2026, 8, 5),
    },
]


# ---------------------------------------------------------------------------
# Sample barrier reports (optional collection C)
# ---------------------------------------------------------------------------

BARRIER_REPORTS = [
    {
        "scheme_id": "SCH-000001",
        "barrier_category": "document_difficulty",
        "description": "Income certificate is difficult to obtain quickly from local offices (synthetic record).",
        "reported_at": _ts(2026, 5, 15),
        "record_type": "synthetic",
    },
    {
        "scheme_id": "SCH-000002",
        "barrier_category": "unclear_instructions",
        "description": "The list of accepted proof documents for BPL status is not clearly explained (synthetic).",
        "reported_at": _ts(2026, 5, 22),
        "record_type": "synthetic",
    },
    {
        "scheme_id": "SCH-000005",
        "barrier_category": "document_difficulty",
        "description": "Aadhaar-linked mobile registration causes delays for rural applicants (synthetic).",
        "reported_at": _ts(2026, 6, 5),
        "record_type": "synthetic",
    },
    {
        "scheme_id": "SCH-000007",
        "barrier_category": "application_process",
        "description": "No-objection certificate process involves multiple departments and causes delays (synthetic).",
        "reported_at": _ts(2026, 6, 20),
        "record_type": "synthetic",
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

def seed(db_name: str = DB_NAME) -> None:
    print(f"\n[SchemeReach] Seeding database: '{db_name}'\n")
    db = get_db(db_name)

    # --- schemes ---
    schemes_col = db[COL_SCHEMES]
    inserted_schemes = 0
    skipped_schemes = 0
    for scheme in SCHEMES:
        if schemes_col.find_one({"scheme_id": scheme["scheme_id"]}):
            skipped_schemes += 1
        else:
            schemes_col.insert_one(scheme)
            inserted_schemes += 1

    print(f"  Schemes  — inserted: {inserted_schemes}, skipped (already exist): {skipped_schemes}")

    # --- applications ---
    apps_col = db[COL_APPLICATIONS]
    inserted_apps = 0
    skipped_apps = 0
    for app in APPLICATIONS:
        if apps_col.find_one({"application_ref": app["application_ref"]}):
            skipped_apps += 1
        else:
            apps_col.insert_one(app)
            inserted_apps += 1

    print(f"  Applications — inserted: {inserted_apps}, skipped (already exist): {skipped_apps}")

    # --- barrier reports ---
    br_col = db[COL_BARRIER_REPORTS]
    existing_reports = br_col.count_documents({})
    inserted_reports = 0
    if existing_reports == 0:
        br_col.insert_many(BARRIER_REPORTS)
        inserted_reports = len(BARRIER_REPORTS)
    print(f"  Barrier Reports — inserted: {inserted_reports}, skipped: {existing_reports}")

    print("\n  Seeding complete.\n")


if __name__ == "__main__":
    # Ensure validators exist before seeding
    setup()
    seed()
