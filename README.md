# SchemeReach — Government Scheme Access Gap Analyzer

> **Academic Prototype** | CSE494 – Intelligent NoSQL Databases  
> This is a fictional demonstration system. It does not submit applications to any government authority, determine official eligibility, or represent any government department.

---

## Quick Start (Summary)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env

# 4. Set up MongoDB validators and indexes
python setup_validators.py

# 5. Load sample data
python seed_data.py

# 6. Run automated tests
pytest tests/ -v

# 7. Launch the application
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

---

## Table of Contents

1. [Prerequisites](#step-1-prerequisites)
2. [Open the Project](#step-2-open-the-project)
3. [Create a Virtual Environment](#step-3-create-a-virtual-environment)
4. [Install Dependencies](#step-4-install-dependencies)
5. [Configure the Database](#step-5-configure-the-database)
6. [Configure Environment Variables](#step-6-configure-environment-variables)
7. [Initialize the Database](#step-7-initialize-the-database)
8. [Load Sample Data](#step-8-load-sample-data)
9. [Test Database Operations](#step-9-test-database-operations)
10. [Run Automated Tests](#step-10-run-automated-tests)
11. [Launch the Application](#step-11-launch-the-application)
12. [Verify Everything](#step-12-verify-everything)
13. [MongoDB Compass Guide](#mongodb-compass-guide)
14. [Project Structure](#project-structure)
15. [Troubleshooting](#troubleshooting)

---

## Step 1: Prerequisites

Verify the following are installed on your Windows 11 machine.

### Python 3.10+

```powershell
python --version
# Expected: Python 3.10.x or later
```

Download from: https://www.python.org/downloads/

### MongoDB Community Server 6.0+

```powershell
mongod --version
# Expected: db version v6.x.x or v7.x.x
```

Download from: https://www.mongodb.com/try/download/community  
During installation, check **"Install MongoDB as a Service"** so it starts automatically.

### MongoDB Compass (GUI)

Download the installer that comes bundled with Community Server, or from:
https://www.mongodb.com/try/download/compass

### VS Code

Download from: https://code.visualstudio.com/  
Recommended extensions: Python (Microsoft), MongoDB for VS Code (MongoDB).

---

## Step 2: Open the Project

1. Open VS Code.
2. **File → Open Folder** → select the `SchemeSathi` folder.
3. Open the integrated terminal: **View → Terminal** or `` Ctrl+` ``.

---

## Step 3: Create a Virtual Environment

In the VS Code terminal (PowerShell):

```powershell
python -m venv .venv
```

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your prompt.

### If PowerShell blocks script activation

Run this command to allow scripts for the current user only (does not disable system-wide security):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry `.\.venv\Scripts\Activate.ps1`.

Alternatively, use Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

---

## Step 4: Install Dependencies

With the virtual environment active:

```powershell
pip install -r requirements.txt
```

Expected packages installed:
- `pymongo==4.6.1`
- `streamlit==1.32.0`
- `python-dotenv==1.0.1`
- `pytest==8.1.1`

---

## Step 5: Configure the Database

### Start the MongoDB service

**Option A — Services Manager:**
1. Press `Win + R` → type `services.msc` → press Enter.
2. Find **MongoDB** in the list.
3. Right-click → **Start**.

**Option B — PowerShell (as Administrator):**

```powershell
net start MongoDB
```

Expected output: `The MongoDB service was started successfully.`

### Verify MongoDB is running

```powershell
mongosh --eval "db.adminCommand('ping')"
# Expected: { ok: 1 }
```

Or open MongoDB Compass and connect to `mongodb://localhost:27017/`.

---

## Step 6: Configure Environment Variables

```powershell
copy .env.example .env
```

Open `.env` in VS Code. The default contents are correct for a local installation with no authentication:

```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=scheme_reach
TEST_DB_NAME=scheme_reach_test
```

> **Security:** `.env` is listed in `.gitignore` and will not be committed to Git.  
> Never share this file or commit it to a public repository.

---

## Step 7: Initialize the Database

Creates the three collections with JSON Schema validators and indexes:

```powershell
python setup_validators.py
```

Expected output:

```
[SchemeReach] Setting up database: 'scheme_reach'

  [+] Created collection 'schemes' with validator.
  [+] Created collection 'applications' with validator.
  [+] Created collection 'barrier_reports' with validator.
  [+] Indexes created / verified.

  Setup complete.
```

Safe to rerun — existing data is preserved and validators are updated in place.

---

## Step 8: Load Sample Data

```powershell
python seed_data.py
```

Expected output:

```
[SchemeReach] Setting up database: 'scheme_reach'
  ...

[SchemeReach] Seeding database: 'scheme_reach'

  Schemes      — inserted: 7, skipped (already exist): 0
  Applications — inserted: 30, skipped (already exist): 0
  Barrier Reports — inserted: 4, skipped: 0

  Seeding complete.
```

**Idempotent:** Running it again skips already-existing records.

---

## Step 9: Test Database Operations

### Run the CRUD demonstration

```powershell
python queries/crud_operations.py
```

This script creates a test scheme, creates a test application, updates it, changes the status, verifies stage history, deletes the application, attempts to delete a referenced scheme (should fail), and attempts an invalid insert (should be rejected).

### Run the aggregation pipeline demonstration

```powershell
python queries/aggregation_queries.py
```

This script runs all five pipelines and prints formatted results to the terminal.

---

## Step 10: Run Automated Tests

```powershell
pytest tests/ -v
```

Expected output (all tests should pass when MongoDB is running):

```
tests/test_validation.py::TestConnection::test_T01_database_connection PASSED
tests/test_validation.py::TestSchemeValidation::test_T02_valid_scheme_accepted PASSED
tests/test_validation.py::TestSchemeValidation::test_T03_invalid_scheme_empty_name_rejected PASSED
tests/test_validation.py::TestSchemeValidation::test_T04_invalid_scheme_missing_required_fields PASSED
tests/test_validation.py::TestApplicationValidation::test_T05_valid_application_accepted PASSED
tests/test_validation.py::TestApplicationValidation::test_T06_invalid_application_status_rejected PASSED
tests/test_validation.py::TestApplicationValidation::test_T07_invalid_application_missing_fields PASSED
tests/test_validation.py::TestSchemeValidation::test_T15_scheme_no_required_documents PASSED
tests/test_crud.py::TestCRUD::test_T08_read_and_filter_records PASSED
tests/test_crud.py::TestCRUD::test_T09_update_documents_recalculates_missing PASSED
tests/test_crud.py::TestCRUD::test_T10_update_status_appends_stage_history PASSED
tests/test_crud.py::TestCRUD::test_T11_delete_test_application PASSED
tests/test_crud.py::TestCRUD::test_T12_prevent_delete_referenced_scheme PASSED
...
tests/test_aggregation.py::TestAggregations::test_T13_missing_documents_frequency PASSED
tests/test_aggregation.py::TestAggregations::test_T14_applications_by_status PASSED
tests/test_aggregation.py::TestAggregations::test_T16_incomplete_apps_with_scheme_names PASSED
tests/test_aggregation.py::TestAggregations::test_T17_empty_collection_does_not_crash PASSED
```

> **Note:** Tests use the `scheme_reach_test` database, which is created and dropped automatically.  
> Do NOT run tests if MongoDB is not running — tests will fail with a connection error.

---

## Step 11: Launch the Application

```powershell
streamlit run app.py
```

Streamlit will print:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open **http://localhost:8501** in your browser.

Navigate using the sidebar:
- 🏠 Home Dashboard
- 📋 Browse Schemes
- ✅ Application Checklist
- 🔍 Track Applications
- ⚙️ Application Management
- 📊 Analytics & Reports
- 🗄️ DB & Validation Demo

---

## Step 12: Verify Everything

Use this checklist to confirm the project is working correctly.

- [ ] `python setup_validators.py` completes without errors.
- [ ] `python seed_data.py` reports inserted records.
- [ ] MongoDB Compass connects to `localhost:27017`.
- [ ] `scheme_reach` database contains `schemes` (7 docs), `applications` (30 docs), `barrier_reports` (4 docs).
- [ ] `pytest tests/ -v` shows all tests passing.
- [ ] `python queries/crud_operations.py` completes the full CRUD cycle.
- [ ] `python queries/aggregation_queries.py` prints results for all four pipelines.
- [ ] `streamlit run app.py` opens at `http://localhost:8501`.
- [ ] Home Dashboard shows correct counts (7 schemes, 30 applications).
- [ ] Browse Schemes shows 7 scheme records.
- [ ] Application Checklist creates a new record with a valid `APP-NNNNNN` reference.
- [ ] Track Applications finds the created record.
- [ ] Analytics page shows bar charts and tables from real database queries.
- [ ] DB Demo page — valid insert button shows success; invalid insert button shows rejection.

---

## MongoDB Compass Guide

### Connect

1. Open MongoDB Compass.
2. Use connection string: `mongodb://localhost:27017/`
3. Click **Connect**.

### Inspect collections

1. In the left panel, click `scheme_reach`.
2. Click `schemes` to see all 7 scheme documents.
3. Click `applications` to see all 30 application records.
4. Expand a document to see nested arrays (`required_documents`, `stage_history`).

### Run aggregation in Compass

1. Open the `applications` collection.
2. Click the **Aggregations** tab.
3. Click **Add Stage**.
4. Copy and paste each stage from `queries/mongodb_queries.js`.
5. Click **Run** after adding all stages.

### View validators

1. Open a collection.
2. Click the **Schema** tab to see field types.
3. Go to **Collection → Validation** (or use the `collMod` command in mongosh) to inspect JSON Schema rules.

---

## Project Structure

```
SchemeSathi/
├── app.py                    ← Streamlit interface (7 pages)
├── config.py                 ← Environment config and constants
├── db.py                     ← PyMongo client and connection helpers
├── setup_validators.py       ← Creates collections, validators, indexes
├── seed_data.py              ← Loads 7 schemes + 30 applications
├── requirements.txt          ← Python package versions
├── .env.example              ← Environment variable template
├── .gitignore
├── README.md                 ← This file
├── queries/
│   ├── crud_operations.py    ← CRUD demonstration script
│   ├── aggregation_queries.py ← Aggregation pipeline demonstration
│   └── mongodb_queries.js    ← Equivalent MongoDB shell queries
├── services/
│   ├── scheme_service.py     ← CRUD operations for schemes
│   ├── application_service.py ← CRUD operations for applications
│   └── analytics_service.py  ← All 5 aggregation pipelines
├── tests/
│   ├── conftest.py           ← Shared fixtures and test helpers
│   ├── test_validation.py    ← Validator tests (T01–T07, T15)
│   ├── test_crud.py          ← CRUD tests (T08–T12)
│   └── test_aggregation.py   ← Aggregation tests (T13, T14, T16, T17)
├── report/
│   ├── project_report.md     ← Full project report
│   └── viva_questions.md     ← 25 Q&A for viva preparation
├── presentation/
│   └── presentation_outline.md ← 10-slide presentation guide
└── screenshots/
    └── README.md             ← Screenshot capture checklist
```

---

## Troubleshooting

### "Cannot connect to MongoDB"

```powershell
# Check if service is running
Get-Service MongoDB

# Start the service
net start MongoDB
```

### "ModuleNotFoundError"

```powershell
# Ensure virtual environment is active
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### "WriteError: Document failed validation"

This is expected when testing invalid inserts. If a valid document is rejected:
- Run `python setup_validators.py` again to ensure validators are applied.
- Check that all required fields are present and have the correct types.

### Duplicate key error on re-seeding

The seed script checks for existing records by `scheme_id` / `application_ref` and skips duplicates automatically.

### Streamlit "Address already in use"

```powershell
streamlit run app.py --server.port 8502
```

### pytest "connection refused"

MongoDB must be running before tests execute. Start the service and retry.

---

## Academic Disclaimer

This project is an individual academic submission for CSE494 – Intelligent NoSQL Databases. All scheme and application data is synthetic. The system does not:
- Submit applications to any government portal.
- Determine official eligibility for any scheme.
- Guarantee any benefit or outcome.
- Represent any government department.

Scheme names are labelled as fictional examples. Official government scheme information should always be verified at the relevant ministry or department's official website.
