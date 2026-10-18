"""
app.py
------
myScheme — Government Scheme Access & Gap Analyzer (SchemeReach)
Modeled directly after the Official Indian Government Portal: myScheme (myScheme.gov.in)
Digital India | Ministry of Electronics and Information Technology (MeitY)
CSE494 – Intelligent NoSQL Databases Academic Prototype
"""

from __future__ import annotations

import datetime
from datetime import timezone
import json
import random
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db import get_db, check_connection
from config import (
    DB_NAME,
    COL_SCHEMES,
    COL_APPLICATIONS,
    COL_BARRIER_REPORTS,
    VALID_STATUSES,
)
from services.scheme_service import (
    create_scheme,
    get_scheme_by_id,
    list_active_schemes,
    search_schemes_by_name,
    filter_schemes,
    update_scheme,
    delete_scheme,
    get_all_categories,
    get_all_departments,
)
from services.application_service import (
    create_application,
    get_application,
    list_applications,
    update_documents,
    update_status,
    delete_application,
    get_checklist_summary,
    readiness_pct,
)
from services.analytics_service import (
    dashboard_metrics,
    missing_documents_frequency,
    applications_by_status,
    incomplete_applications_by_scheme,
    incomplete_apps_with_scheme_names,
    stage_duration_analysis,
)

# ---------------------------------------------------------------------------
# 1. Page Configuration & Official Government Design System (CSS)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="myScheme — Government Scheme Access Gap Analyzer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injected Official myScheme.gov.in CSS Style System
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&family=Noto+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #f8fafc !important;
        color: #1e293b;
    }

    /* Indian Tricolor Top Ribbon */
    .gov-tricolor {
        height: 4px;
        background: linear-gradient(90deg, #FF9933 0%, #FF9933 33.3%, #FFFFFF 33.3%, #FFFFFF 66.6%, #138808 66.6%, #138808 100%);
        width: 100%;
        margin-bottom: 8px;
    }

    /* Official Top Bar */
    .gov-top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 12px;
        background-color: #f1f5f9;
        font-size: 11.5px;
        color: #475569;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }

    /* Official Header Navbar */
    .gov-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .gov-brand {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .myscheme-logo {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #0f172a;
    }
    .myscheme-logo span {
        color: #15803d;
    }

    /* Realistic Government Buttons */
    .gov-btn-signin {
        background-color: #15803d;
        color: #ffffff;
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        border: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .gov-btn-lang {
        background-color: #ecfdf5;
        color: #065f46;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #a7f3d0;
    }

    /* Search Bar with Green Action Button (myScheme style) */
    .search-container {
        position: relative;
        margin-bottom: 6px;
    }
    .search-hint {
        font-size: 12px;
        color: #64748b;
        margin-top: 4px;
        margin-bottom: 16px;
    }

    /* Scheme Card - Exact Replica of myScheme */
    .scheme-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .scheme-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }
    .scheme-card-title {
        font-size: 19px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .scheme-card-ministry {
        font-size: 13.5px;
        font-weight: 500;
        color: #64748b;
        margin-bottom: 12px;
    }
    .scheme-card-desc {
        font-size: 13.5px;
        line-height: 1.6;
        color: #334155;
        margin-bottom: 16px;
    }
    .scheme-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding-top: 12px;
        border-top: 1px dashed #f1f5f9;
    }

    /* Green Pill Tags (as seen in myScheme screenshot) */
    .gov-pill {
        display: inline-block;
        background-color: #ffffff;
        color: #15803d;
        border: 1px solid #16a34a;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .gov-pill.missing {
        color: #b91c1c;
        border-color: #ef4444;
        background-color: #fef2f2;
    }
    .gov-pill.provided {
        color: #047857;
        border-color: #10b981;
        background-color: #ecfdf5;
    }

    /* Filter Sidebar Accordions */
    .filter-header {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .filter-reset {
        font-size: 13px;
        color: #15803d;
        font-weight: 600;
        text-decoration: none;
        cursor: pointer;
    }

    /* Tab Indicator (Active Green Underline) */
    .scheme-tab-active {
        font-weight: 700;
        color: #15803d;
        border-bottom: 3px solid #15803d;
        padding-bottom: 6px;
        margin-right: 20px;
        display: inline-block;
    }
    .scheme-tab-inactive {
        font-weight: 500;
        color: #64748b;
        margin-right: 20px;
        display: inline-block;
        cursor: pointer;
    }

    /* Status Badges */
    .gov-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11.5px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .gov-badge-approved { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .gov-badge-pending { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .gov-badge-submitted { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    .gov-badge-rejected { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

    /* Timeline Stepper */
    .gov-timeline-item {
        position: relative;
        padding-left: 24px;
        margin-bottom: 16px;
        border-left: 2px solid #cbd5e1;
    }
    .gov-timeline-item:last-child {
        border-left: 2px solid transparent;
    }
    .gov-timeline-dot {
        position: absolute;
        left: -6px;
        top: 2px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #15803d;
        border: 2px solid #ffffff;
    }
    .gov-timeline-title {
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
    }
    .gov-timeline-sub {
        font-size: 11px;
        color: #64748b;
    }

    /* Floating Chatbot Widget */
    .chatbot-fab {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 52px;
        height: 52px;
        background-color: #15803d;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 12px rgba(21, 128, 61, 0.4);
        z-index: 999;
        cursor: pointer;
    }

    /* Streamlit Widget Polishing */
    div[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    div[data-testid="stSidebar"] .stRadio label {
        font-weight: 600;
        color: #334155;
    }
    button[kind="primary"] {
        background-color: #15803d !important;
        border-color: #15803d !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 2. Database Connection & Caching
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_db():
    return get_db(DB_NAME)

def _db():
    return _get_db()

# Navigation State Setup
NAV_PAGES = [
    "📋 Schemes Directory",
    "🏠 Dashboard & Analytics",
    "✅ Check Eligibility / Readiness",
    "🔍 Track Application Status",
    "⚙️ Scheme & Application Manager",
    "🗄️ Database & Schema Inspector",
]

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = NAV_PAGES[0]

# ---------------------------------------------------------------------------
# 3. Top Indian Government Banner (Official Header)
# ---------------------------------------------------------------------------

# National Tricolor Ribbon
st.markdown("<div class='gov-tricolor'></div>", unsafe_allow_html=True)

# Top Bar with Government Credentials & Accessibility
st.markdown(
    """
    <div class="gov-top-bar">
        <div>
            <b>भारत सरकार | Government of India</b> &nbsp;|&nbsp; 
            Ministry of Electronics & IT (MeitY) &nbsp;|&nbsp; 
            <span style="color:#15803d;font-weight:600;">CSE494 Academic Demonstration</span>
        </div>
        <div>
            <span style="cursor:pointer;margin-right:12px;">Skip to Main Content</span>
            <span style="cursor:pointer;margin-right:12px;">A- &nbsp; <b>A</b> &nbsp; A+</span>
            <span style="cursor:pointer;font-weight:600;">हिन्दी | English</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navbar Header exactly matching the myScheme Screenshot
st.markdown(
    """
    <div class="gov-navbar">
        <div class="gov-brand">
            <!-- State Emblem of India Lion Capital SVG -->
            <svg width="34" height="42" viewBox="0 0 100 120" fill="#1e293b" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="98" r="14" fill="none" stroke="#1e293b" stroke-width="4"/>
                <path d="M50 84 L50 112 M36 98 L64 98 M40 88 L60 108 M40 108 L60 88" stroke="#1e293b" stroke-width="2"/>
                <rect x="20" y="112" width="60" height="6" rx="2" fill="#1e293b"/>
                <path d="M50 15 C40 15 35 25 35 38 C35 55 45 68 50 78 C55 68 65 55 65 38 C65 25 60 15 50 15 Z" fill="#1e293b"/>
                <path d="M30 25 C24 25 20 32 20 42 C20 56 30 68 35 76 C32 60 30 45 30 25 Z" fill="#1e293b"/>
                <path d="M70 25 C76 25 80 32 80 42 C80 56 70 68 65 76 C68 60 70 45 70 25 Z" fill="#1e293b"/>
                <circle cx="50" cy="22" r="5" fill="#f8fafc"/>
            </svg>
            <div style="border-left: 1px solid #cbd5e1; height: 38px; margin: 0 4px;"></div>
            <div>
                <div class="myscheme-logo">my<span>scheme</span> <span style="font-size:12px;background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:12px;font-weight:600;vertical-align:middle;">SchemeReach</span></div>
                <div style="font-size:10px;font-weight:600;color:#64748b;letter-spacing:0.5px;">ONE-STOP SEARCH AND DISCOVERY OF GOVT SCHEMES</div>
            </div>
            <!-- Digital India Logo Representation -->
            <div style="margin-left: 14px; padding-left: 14px; border-left: 1px solid #e2e8f0; display:flex; align-items:center; gap:6px;">
                <span style="font-size:20px;">🇮🇳</span>
                <span style="font-weight:800;font-size:12px;color:#0f172a;line-height:1.1;">Digital India<br><span style="font-size:9px;color:#64748b;font-weight:500;">Power To Empower</span></span>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <div class="gov-btn-signin">Sign In &rarr;</div>
            <div class="gov-btn-lang">🌐 Aअ English ▾</div>
            <div style="background:#f1f5f9;padding:6px 10px;border-radius:6px;font-size:14px;cursor:pointer;">☀️</div>
            <div style="background:#7c3aed;color:white;width:30px;height:30px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold;">♿</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 4. Sidebar: Navigation & Database Connectivity Status
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🏛️ Portal Navigation")
    selected_nav = st.radio(
        "Menu",
        NAV_PAGES,
        index=NAV_PAGES.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in NAV_PAGES else 0,
        label_visibility="collapsed",
    )
    if selected_nav != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_nav

    st.markdown("<hr style='margin:16px 0 12px 0;'>", unsafe_allow_html=True)

    # Database Live Connection Pill
    ok, conn_msg = check_connection()
    if ok:
        clean_v = conn_msg.replace("Connected  — ", "")
        st.markdown(
            f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 12px;display:flex;align-items:center;gap:10px;">
                <span style="height:10px;width:10px;background:#16a34a;border-radius:50%;display:inline-block;"></span>
                <div>
                    <div style="font-size:12px;font-weight:700;color:#166534;">MongoDB Database Active</div>
                    <div style="font-size:11px;color:#15803d;">{clean_v}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.error(f"🔴 DB Offline: {conn_msg}")

    st.markdown(
        """
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px;margin-top:14px;font-size:11px;color:#92400e;line-height:1.4;">
            <b>Academic Notice:</b> CSE494 Intelligent NoSQL Databases Project. Data is synthetic and simulated for demonstration purposes.
        </div>
        """,
        unsafe_allow_html=True,
    )

page = st.session_state["nav_page"]

# Helper: Status badge
def _badge_html(status: str) -> str:
    s_clean = status.lower().replace(" ", "_")
    disp = status.replace("_", " ").title()
    if s_clean in ["approved", "ready_to_submit"]:
        return f'<span class="gov-badge gov-badge-approved">● {disp}</span>'
    elif s_clean in ["submitted", "under_review"]:
        return f'<span class="gov-badge gov-badge-submitted">● {disp}</span>'
    elif s_clean in ["rejected"]:
        return f'<span class="gov-badge gov-badge-rejected">● {disp}</span>'
    else:
        return f'<span class="gov-badge gov-badge-pending">● {disp}</span>'

# Helper: Green outline pills (exact match to myScheme)
def _pill_tags_html(tags: list[str], pill_class: str = "") -> str:
    if not tags:
        return ""
    pills = [f'<span class="gov-pill {pill_class}">{t.replace("_", " ").title()}</span>' for t in tags]
    return "".join(pills)


# ===========================================================================
# VIEW 1: 📋 SCHEMES DIRECTORY (EXACT REPLICA OF USER'S MYSCHEME SCREENSHOT)
# ===========================================================================

if page == NAV_PAGES[0]:
    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()

    # Layout: Left Filters Column (30%) + Right Schemes List (70%)
    col_filters, col_results = st.columns([1, 2.7], gap="large")

    # -----------------------------------------------------------------------
    # LEFT COLUMN: FILTER BY (As shown in screenshot)
    # -----------------------------------------------------------------------
    with col_filters:
        st.markdown(
            """
            <div class="filter-header">
                <span>Filter By</span>
                <span class="filter-reset">Reset Filters</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 1. State / UT
        st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:4px;color:#334155;'>State/UT</div>", unsafe_allow_html=True)
        f_state = st.selectbox(
            "State/UT",
            ["All India", "Maharashtra", "Uttar Pradesh", "Karnataka", "Tamil Nadu", "Delhi", "Gujarat", "Rajasthan"],
            label_visibility="collapsed",
        )

        # 2. Scheme Category
        with st.expander("Scheme Category", expanded=True):
            all_cats = get_all_categories(db)
            f_cat = st.radio("Category", ["All Categories"] + all_cats, label_visibility="collapsed")

        # 3. Gender
        with st.expander("Gender", expanded=False):
            f_gender = st.selectbox("Gender", ["All", "Male", "Female", "Transgender"], label_visibility="collapsed")

        # 4. Age
        st.markdown("<div style='font-size:13px;font-weight:600;margin-top:10px;margin-bottom:4px;color:#334155;'>Age Group</div>", unsafe_allow_html=True)
        f_age = st.selectbox("Age", ["All Ages", "Below 18", "18 - 35 Years", "36 - 60 Years", "Senior Citizen (60+)"], label_visibility="collapsed")

        # 5. Caste / Social Category
        with st.expander("Caste", expanded=False):
            f_caste = st.selectbox("Caste", ["All", "General", "OBC", "SC", "ST", "Minority"], label_visibility="collapsed")

        # 6. Department / Ministry Name
        st.markdown("<div style='font-size:13px;font-weight:600;margin-top:10px;margin-bottom:4px;color:#334155;'>Department Name</div>", unsafe_allow_html=True)
        all_depts = ["All Departments"] + get_all_departments(db)
        f_dept = st.selectbox("Department Name", all_depts, label_visibility="collapsed")

        # 7. Benefit Type
        with st.expander("Benefit Type", expanded=False):
            f_benefit = st.selectbox("Benefit Type", ["All", "Financial Assistance", "Subsidized Goods", "Scholarship", "Training"], label_visibility="collapsed")

        # 8. Residence
        with st.expander("Residence", expanded=False):
            f_residence = st.selectbox("Residence", ["All", "Rural", "Urban"], label_visibility="collapsed")

    # -----------------------------------------------------------------------
    # RIGHT COLUMN: SEARCH, TABS, SORT & SCHEME CARDS
    # -----------------------------------------------------------------------
    with col_results:
        # Top Search Bar with Green Action Button
        search_query = st.text_input(
            "Search",
            placeholder="Search by scheme name, keywords or ministry...",
            label_visibility="collapsed",
        )
        st.markdown(
            """
            <div class="search-hint">
                ⓘ For an exact match, put the words in quotes. For example: "Kisan", "Housing", "Fellowship".
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tab Navigation (All Schemes | State/UT Schemes | Central Schemes)
        tab_col1, tab_col2, tab_col3 = st.columns([1.2, 1.4, 1.4])
        with tab_col1:
            st.markdown("<div class='scheme-tab-active'>All Schemes</div>", unsafe_allow_html=True)
        with tab_col2:
            st.markdown("<div class='scheme-tab-inactive'>State/UT Schemes</div>", unsafe_allow_html=True)
        with tab_col3:
            st.markdown("<div class='scheme-tab-inactive'>Central Schemes</div>", unsafe_allow_html=True)

        st.markdown("<div style='border-bottom: 1px solid #e2e8f0; margin-bottom: 14px;'></div>", unsafe_allow_html=True)

        # Fetch Schemes from Database
        if search_query.strip():
            schemes = search_schemes_by_name(db, search_query.strip())
            if f_cat != "All Categories":
                schemes = [s for s in schemes if s.get("category") == f_cat]
            if f_dept != "All Departments":
                schemes = [s for s in schemes if s.get("department") == f_dept]
        else:
            schemes = filter_schemes(
                db,
                category="" if f_cat == "All Categories" else f_cat,
                department="" if f_dept == "All Departments" else f_dept,
            )

        # Results Count & Sort Bar (as shown in screenshot)
        count_col, sort_col = st.columns([2, 1])
        with count_col:
            st.markdown(f"<div style='font-size:14px;color:#475569;'>Total <b style='color:#0f172a;font-size:16px;'>{len(schemes)}</b> schemes available</div>", unsafe_allow_html=True)
        with sort_col:
            st.markdown("<div style='text-align:right;font-size:13px;color:#475569;'>Sort : <b>Relevance ⌵</b></div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        if not schemes:
            st.info("No welfare schemes matched your query. Try selecting 'All Categories' or clearing the search bar.")
        else:
            for s in schemes:
                sid = s["scheme_id"]
                docs = s.get("required_documents", [])
                cat_tag = s.get("category", "")
                dept_tag = s.get("department", "Ministry of Social Justice")
                
                # Tag Pills (e.g., Category, Ministry keyword, and top required documents)
                tag_list = [cat_tag] + docs[:4]

                # Render Official Scheme Card (Exact visual structure from screenshot)
                st.markdown(
                    f"""
                    <div class="scheme-card">
                        <div class="scheme-card-title">{s['name']}</div>
                        <div class="scheme-card-ministry">{dept_tag}</div>
                        <div class="scheme-card-desc">{s.get('description', 'Government program designed to provide financial, educational, or welfare support to eligible citizens.')}</div>
                        <div style="margin-bottom: 14px;">
                            {_pill_tags_html(tag_list)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Card Actions Bar
                act_col1, act_col2 = st.columns([1, 1])
                with act_col1:
                    with st.expander(f"📑 View Details & Documents for {s['name']}"):
                        st.markdown(f"**💰 Benefits:** {s.get('benefits_description', '—')}")
                        st.markdown("**Eligibility Criteria:**")
                        for crit in s.get("eligibility_criteria", []):
                            st.markdown(f"• {crit}")
                        st.markdown("**Required Supporting Documents:**")
                        st.markdown(_pill_tags_html(docs))
                        if s.get("official_url"):
                            st.markdown(f"<br>[🌐 Official Portal Link]({s['official_url']})", unsafe_allow_html=True)
                with act_col2:
                    if st.button(f"🚀 Apply / Check Readiness →", key=f"btn_apply_{sid}", use_container_width=True):
                        st.session_state["selected_scheme_id"] = sid
                        st.session_state["nav_page"] = NAV_PAGES[2]
                        st.rerun()


# ===========================================================================
# VIEW 2: 🏠 DASHBOARD & ANALYTICS (NATIONAL GAP ANALYZER)
# ===========================================================================

elif page == NAV_PAGES[1]:
    st.markdown("### 📊 National Scheme Access & Document Gap Dashboard")
    st.caption("Aggregated analytics across citizens, schemes, and documentation bottlenecks from MongoDB aggregation pipelines.")

    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()
    metrics = dashboard_metrics(db)

    # Top KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Active Schemes", metrics["total_schemes"], help="Verified schemes in catalogue")
    with k2:
        st.metric("Applications Tracked", metrics["total_applications"], help="Simulated citizen records")
    with k3:
        st.metric("Stalled Records", metrics["applications_with_missing_docs"], delta="Document Gaps", delta_color="inverse")
    with k4:
        pct_gap = (metrics["applications_with_missing_docs"] / metrics["total_applications"] * 100) if metrics["total_applications"] else 0
        st.metric("Deficit Frequency", f"{pct_gap:.1f}%", help="Percentage of applications lacking paperwork")

    st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)

    # High Impact Visualizations
    vcol1, vcol2 = st.columns(2)

    with vcol1:
        st.markdown("#### ⚠️ Top Document Bottlenecks (Pipeline 1)")
        p1 = missing_documents_frequency(db)
        if p1:
            df1 = pd.DataFrame(p1).head(6)
            df1["Document Name"] = df1["document_type"].apply(lambda x: x.replace("_", " ").title())
            fig1 = px.bar(
                df1,
                x="count",
                y="Document Name",
                orientation="h",
                text="count",
                color="count",
                color_continuous_scale="Tealgrn",
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=10, b=10),
                height=280,
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No document gap data available.")

    with vcol2:
        st.markdown("#### 📈 Application Status Lifecycle (Pipeline 2)")
        p2 = applications_by_status(db)
        if p2:
            df2 = pd.DataFrame(p2)
            df2["Status"] = df2["status"].apply(lambda x: x.replace("_", " ").title())
            fig2 = px.pie(
                df2,
                names="Status",
                values="count",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=280,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No applications status data.")

    # Cross-Collection $lookup Analysis
    st.markdown("#### 🏢 Scheme-wise Document Deficits with Joined Names ($lookup Pipeline 4)")
    p4 = incomplete_apps_with_scheme_names(db)
    if p4:
        df4 = pd.DataFrame(p4)
        fig4 = px.bar(
            df4,
            x="scheme_name",
            y="incomplete_count",
            color="category",
            text="incomplete_count",
            title="Incomplete Records by Scheme Name",
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
        )
        st.plotly_chart(fig4, use_container_width=True)


# ===========================================================================
# VIEW 3: ✅ CHECK ELIGIBILITY / READINESS SIMULATOR
# ===========================================================================

elif page == NAV_PAGES[2]:
    st.markdown("### ✅ Application Readiness & Document Audit Simulator")
    st.caption("Citizen self-service portal to verify paperwork completeness before visiting local government service centres.")

    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()
    active_schemes = list_active_schemes(db)
    if not active_schemes:
        st.warning("No active schemes in database.")
        st.stop()

    scheme_ids = [s["scheme_id"] for s in active_schemes]
    names_map = {s["scheme_id"]: s["name"] for s in active_schemes}

    pre_id = st.session_state.get("selected_scheme_id", scheme_ids[0])
    pre_idx = scheme_ids.index(pre_id) if pre_id in scheme_ids else 0

    col_sim_form, col_sim_audit = st.columns([3, 2], gap="large")

    with col_sim_form:
        st.markdown("#### 1. Select Scheme")
        target_scheme_id = st.selectbox(
            "Select Welfare Scheme",
            options=scheme_ids,
            index=pre_idx,
            format_func=lambda sid: f"{sid} — {names_map.get(sid, '')}",
        )
        target_scheme = next((s for s in active_schemes if s["scheme_id"] == target_scheme_id), None)

        st.markdown("#### 2. Applicant Identification (Pseudonym)")
        c_alias, c_gen = st.columns([3, 1])
        with c_alias:
            alias = st.text_input("Applicant Alias", value=st.session_state.get("sim_alias", "Farmer_Ramesh"))
        with c_gen:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🎲 Random"):
                st.session_state["sim_alias"] = random.choice(["Farmer_Gopal", "Student_Ananya", "Artisan_Manish", "Scholar_Deepa"])
                st.rerun()

        st.markdown("#### 3. Mark Prepared Supporting Documents")
        req_docs = target_scheme.get("required_documents", []) if target_scheme else []

        if req_docs:
            provided = st.multiselect(
                "Documents Currently Obtained by Applicant",
                options=req_docs,
                default=req_docs[:1] if req_docs else [],
                format_func=lambda d: d.replace("_", " ").title(),
            )
        else:
            provided = []
            st.info("No documents are required for this scheme.")

        missing = [d for d in req_docs if d not in provided]
        score = readiness_pct(req_docs, provided)

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)

        if st.button("🚀 Register Simulated Application Record", type="primary", use_container_width=True):
            res = create_application(
                db,
                {
                    "scheme_id": target_scheme_id,
                    "applicant_alias": alias or "Anonymous",
                    "documents_provided": provided,
                },
            )
            if res["success"]:
                ref = res["application_ref"]
                st.balloons()
                st.success(f"🎉 Application record successfully generated: **`{ref}`**")
                st.session_state["track_app_ref"] = ref
                st.session_state["nav_page"] = NAV_PAGES[3]
                st.rerun()
            else:
                st.error(f"Error: {res['error']}")

    with col_sim_audit:
        st.markdown("#### 📊 Real-Time Readiness Score")
        if target_scheme:
            st.markdown(
                f"""
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:14px;">
                    <div style="font-size:11px;font-weight:700;color:#15803d;">SELECTED PROGRAM</div>
                    <div style="font-weight:700;font-size:15px;color:#0f172a;">{target_scheme['name']}</div>
                    <div style="font-size:12px;color:#64748b;">{target_scheme.get('department')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Readiness Gauge
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={"suffix": "%"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#15803d" if score >= 80 else ("#f59e0b" if score >= 50 else "#dc2626")},
                        "steps": [
                            {"range": [0, 50], "color": "#fee2e2"},
                            {"range": [50, 80], "color": "#fef3c7"},
                            {"range": [80, 100], "color": "#dcfce7"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(height=170, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("**Documents Prepared:**")
            st.markdown(_pill_tags_html(provided, "provided") or "None", unsafe_allow_html=True)

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            st.markdown("**Pending / Deficit Documents:**")
            st.markdown(_pill_tags_html(missing, "missing") or "None (100% Ready!)", unsafe_allow_html=True)


# ===========================================================================
# VIEW 4: 🔍 TRACK APPLICATION STATUS (OFFICIAL DOSSIER)
# ===========================================================================

elif page == NAV_PAGES[3]:
    st.markdown("### 🔍 Track Government Application Status")
    st.caption("Citizen and Officer audit portal: track stage transitions, missing paperwork, and resolution history.")

    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()
    all_apps = list_applications(db)
    all_refs = [a["application_ref"] for a in all_apps]

    current_ref = st.session_state.get("track_app_ref", all_refs[0] if all_refs else "")

    col_srch, col_pick = st.columns([2, 3])
    with col_srch:
        input_ref = st.text_input("Enter Application Reference Number", value=current_ref, placeholder="e.g. APP-000001")
    with col_pick:
        if all_refs:
            picked_ref = st.selectbox(
                "Or Select from Active Records",
                options=[""] + all_refs,
                index=(all_refs.index(current_ref) + 1) if current_ref in all_refs else 0,
                format_func=lambda r: f"{r} — {next((a.get('applicant_alias', '') for a in all_apps if a['application_ref'] == r), '')}" if r else "Select…",
            )
            if picked_ref and picked_ref != input_ref:
                input_ref = picked_ref
                st.session_state["track_app_ref"] = picked_ref

    if not input_ref.strip():
        st.info("Enter or select an application reference number.")
        st.stop()

    ref = input_ref.strip().upper()
    summary = get_checklist_summary(db, ref)

    if not summary:
        st.error(f"Application reference '{ref}' not found in MongoDB.")
        st.stop()

    app = summary["application"]
    scheme = summary["scheme"]
    score = summary["readiness_pct"]

    # Official Record Dossier Card
    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <span style="font-family:'JetBrains Mono';font-size:13px;font-weight:700;color:#15803d;">REF: {app['application_ref']}</span>
                    <h2 style="margin:4px 0;font-size:20px;color:#0f172a;">Applicant: {app.get('applicant_alias', 'Anonymous')}</h2>
                    <div style="font-size:13px;color:#64748b;">Target Scheme: <b>{scheme.get('name')}</b> ({app['scheme_id']})</div>
                </div>
                <div style="text-align:right;">
                    {_badge_html(app['application_status'])}
                    <div style="font-size:11px;color:#94a3b8;margin-top:6px;">Last updated: {app.get('updated_at', datetime.datetime.now(timezone.utc)).strftime('%d %b %Y, %H:%M UTC')}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_t_audit, col_t_docs, col_t_action = st.columns([3, 3, 4], gap="medium")

    with col_t_audit:
        st.markdown("#### 📜 Audit Stage Stepper")
        for h in reversed(app.get("stage_history", [])):
            ts = h.get("timestamp")
            t_str = ts.strftime("%d %b %Y, %H:%M") if ts else "—"
            st.markdown(
                f"""
                <div class="gov-timeline-item">
                    <div class="gov-timeline-dot"></div>
                    <div class="gov-timeline-title">{h.get('stage', '').replace('_', ' ').title()}</div>
                    <div class="gov-timeline-sub">{t_str}</div>
                    <div style="font-size:12px;color:#475569;margin-top:2px;">“{h.get('note', '')}”</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_t_docs:
        st.markdown("#### 📑 Verification Status")
        st.metric("Document Readiness", f"{score:.1f}%")
        st.markdown("**Required Paperwork:**")
        st.markdown(_pill_tags_html(summary["required_documents"]), unsafe_allow_html=True)
        st.markdown("**Verified Documents:**")
        st.markdown(_pill_tags_html(summary["documents_provided"], "provided") or "None", unsafe_allow_html=True)
        st.markdown("**Deficit Documents:**")
        st.markdown(_pill_tags_html(summary["missing_documents"], "missing") or "None (Ready)", unsafe_allow_html=True)

    with col_t_action:
        st.markdown("#### ⚙️ Official Actions")
        tab_rec_docs, tab_rec_stat = st.tabs(["Update Paperwork", "Transition Stage"])

        with tab_rec_docs:
            req_d = summary["required_documents"]
            cur_p = summary["documents_provided"]
            if req_d:
                new_p = st.multiselect("Mark Verified Documents", options=req_d, default=cur_p, format_func=lambda x: x.replace("_", " ").title())
                if st.button("Save Document Revisions", type="primary", key="save_docs_track"):
                    res = update_documents(db, ref, new_p)
                    if res["success"]:
                        st.success("Revisions saved successfully.")
                        st.rerun()
                    else:
                        st.error(res["error"])
            else:
                st.info("No documents configured.")

        with tab_rec_stat:
            cur_st = app["application_status"]
            new_st = st.selectbox("Assign New Status", VALID_STATUSES, index=VALID_STATUSES.index(cur_st) if cur_st in VALID_STATUSES else 0)
            note = st.text_input("Reviewer Audit Note", placeholder="e.g. Identity verified via biometric")
            if st.button("Record Stage Transition", key="save_stat_track"):
                res = update_status(db, ref, new_st, note)
                if res["success"]:
                    st.success("Status updated.")
                    st.rerun()
                else:
                    st.error(res["error"])


# ===========================================================================
# VIEW 5: ⚙️ SCHEME & APPLICATION MANAGER (FULL CRUD)
# ===========================================================================

elif page == NAV_PAGES[4]:
    st.markdown("### ⚙️ Master Administration & CRUD Console")
    st.caption("Manage scheme definitions, configure validation parameters, and manage citizen application records.")

    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()

    tab_m_schemes, tab_m_apps = st.tabs(["🏛️ Scheme Catalog Management", "📑 Application Records Management"])

    with tab_m_schemes:
        sub_add, sub_list = st.tabs(["Add New Scheme", "Browse & Edit Existing Schemes"])
        with sub_add:
            with st.form("admin_new_scheme"):
                c1, c2 = st.columns(2)
                with c1:
                    n_name = st.text_input("Scheme Name *", placeholder="e.g. National Apprenticeship Promotion Scheme")
                    n_cat = st.text_input("Category *", placeholder="e.g. Skills & Employment")
                    n_dept = st.text_input("Department / Ministry *", placeholder="e.g. Ministry of Skill Development")
                with c2:
                    n_url = st.text_input("Official Portal URL", placeholder="https://apprenticeshipindia.gov.in")
                    n_ver = st.checkbox("Verified from Official Source", value=True)
                    n_act = st.checkbox("Active Status", value=True)

                n_desc = st.text_area("Description")
                n_ben = st.text_area("Benefits")
                n_crit = st.text_area("Eligibility Criteria (one per line)", value="Must be aged 18 to 35 years\nMust have completed 10th Standard")
                n_docs = st.text_area("Required Documents (one per line)", value="identity_proof\neducational_certificate\nbank_passbook")

                if st.form_submit_button("Publish Scheme to Database", type="primary"):
                    if not n_name or not n_cat or not n_dept:
                        st.error("Name, Category, and Department are required.")
                    else:
                        res = create_scheme(
                            db,
                            {
                                "name": n_name,
                                "category": n_cat,
                                "department": n_dept,
                                "description": n_desc,
                                "benefits_description": n_ben,
                                "eligibility_criteria": [c.strip() for c in n_crit.splitlines() if c.strip()],
                                "required_documents": [d.strip() for d in n_docs.splitlines() if d.strip()],
                                "official_url": n_url.strip() or None,
                                "source_verified": n_ver,
                                "active": n_act,
                            },
                        )
                        if res["success"]:
                            st.success(f"Published Scheme ID: **`{res['scheme_id']}`**")
                            st.rerun()
                        else:
                            st.error(res["error"])

        with sub_list:
            s_list = list(db[COL_SCHEMES].find({}, {"_id": 0}).sort("name", 1))
            for sc in s_list:
                sid = sc["scheme_id"]
                ref_count = db[COL_APPLICATIONS].count_documents({"scheme_id": sid})
                with st.expander(f"{sid} — {sc['name']} ({ref_count} applications)"):
                    ed_desc = st.text_area("Description", value=sc.get("description", ""), key=f"ad_desc_{sid}")
                    ed_ben = st.text_area("Benefits", value=sc.get("benefits_description", ""), key=f"ad_ben_{sid}")
                    ed_act = st.checkbox("Active", value=sc.get("active", True), key=f"ad_act_{sid}")

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Save Changes", key=f"btn_save_{sid}"):
                            res = update_scheme(db, sid, {"description": ed_desc, "benefits_description": ed_ben, "active": ed_act})
                            if res["success"]:
                                st.success("Updated.")
                                st.rerun()
                    with b2:
                        if st.button("Delete Scheme", key=f"btn_del_{sid}"):
                            res = delete_scheme(db, sid)
                            if res["success"]:
                                st.success("Deleted.")
                                st.rerun()
                            else:
                                st.error(res["error"])

    with tab_m_apps:
        all_apps = list_applications(db)
        st.markdown(f"**Found {len(all_apps)} application records:**")
        for ap in all_apps[:20]:
            aref = ap["application_ref"]
            with st.expander(f"{aref} | {ap.get('applicant_alias', 'Anonymous')} | {ap['application_status'].upper()}"):
                st.markdown(f"**Scheme:** `{ap['scheme_id']}`")
                st.markdown(f"**Provided:** {_pill_tags_html(ap.get('documents_provided', []), 'provided')}", unsafe_allow_html=True)
                st.markdown(f"**Missing:** {_pill_tags_html(ap.get('missing_documents', []), 'missing')}", unsafe_allow_html=True)
                if st.button(f"🗑️ Delete Record {aref}", key=f"del_rec_{aref}"):
                    delete_application(db, aref)
                    st.success("Record deleted.")
                    st.rerun()


# ===========================================================================
# VIEW 6: 🗄️ DATABASE & SCHEMA INSPECTOR (VIVA & NOSQL LAB)
# ===========================================================================

elif page == NAV_PAGES[5]:
    st.markdown("### 🗄️ MongoDB Architecture & Schema Enforcement Lab")
    st.caption("Demonstrate JSON Schema Validation enforcement, BSON structure inspection, and indexing for CSE494 viva.")

    if not ok:
        st.error(conn_msg)
        st.stop()

    db = _db()

    # System Diagnostics
    c1, c2, c3 = st.columns(3)
    c1.metric("Database Name", DB_NAME)
    c2.metric("Total Collections", len(db.list_collection_names()))
    c3.metric("Total Records", sum(db[c].count_documents({}) for c in [COL_SCHEMES, COL_APPLICATIONS, COL_BARRIER_REPORTS]))

    st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)

    # Validation Sandbox
    st.markdown("#### 🧪 Live Schema Validation Sandbox")
    st.caption("MongoDB executes validation rules directly in the database engine before persisting records:")

    v1, v2 = st.columns(2)
    with v1:
        st.markdown("**Test A: Valid Document Insert**")
        if st.button("Insert Valid Scheme Document", type="primary"):
            from pymongo.errors import WriteError
            v_doc = {
                "scheme_id": "SCH-TEST-OK",
                "name": "Validation Compliant Scheme",
                "category": "Testing",
                "department": "CSE494 Lab",
                "active": True,
                "created_at": datetime.datetime.now(timezone.utc),
                "updated_at": datetime.datetime.now(timezone.utc),
            }
            db[COL_SCHEMES].delete_one({"scheme_id": "SCH-TEST-OK"})
            try:
                db[COL_SCHEMES].insert_one(v_doc)
                st.success("✅ Accepted by MongoDB JSON Schema Engine!")
                db[COL_SCHEMES].delete_one({"scheme_id": "SCH-TEST-OK"})
            except WriteError as exc:
                st.error(f"Error: {exc}")

    with v2:
        st.markdown("**Test B: Reject Corrupt Document**")
        if st.button("Attempt Corrupt Document Insert"):
            from pymongo.errors import WriteError
            bad_doc = {
                "name": "",  # Fails minLength: 2
                "category": "Test",
                "department": "Test",
                "active": True,
                # Missing required timestamps
            }
            try:
                db[COL_SCHEMES].insert_one(bad_doc)
                st.error("Document was accepted when it should have been rejected.")
            except WriteError as exc:
                errmsg = exc.details.get("errmsg", str(exc)) if hasattr(exc, "details") else str(exc)
                st.error(f"🛡️ Correctly REJECTED by MongoDB JSON Schema:\n`{errmsg[:200]}`")

    # Index Inspector
    st.markdown("---")
    st.markdown("#### ⚡ Active Database Indexes")
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f"**`{COL_SCHEMES}` Indexes:**")
        for idx in db[COL_SCHEMES].list_indexes():
            st.code(f"Index: {idx['name']} | Keys: {dict(idx['key'])}")
    with i2:
        st.markdown(f"**`{COL_APPLICATIONS}` Indexes:**")
        for idx in db[COL_APPLICATIONS].list_indexes():
            st.code(f"Index: {idx['name']} | Keys: {dict(idx['key'])}")

# ---------------------------------------------------------------------------
# 5. Floating Chatbot Icon (As shown in screenshot bottom-right)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="chatbot-fab" title="myScheme Saathi / Assistant">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2"></rect>
            <circle cx="12" cy="5" r="2"></circle>
            <path d="M12 7v4"></path>
            <line x1="8" y1="16" x2="8" y2="16"></line>
            <line x1="16" y1="16" x2="16" y2="16"></line>
        </svg>
    </div>
    """,
    unsafe_allow_html=True,
)
