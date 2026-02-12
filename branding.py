"""Active Heroes branded UI components and trust tier configuration."""

import html as _html
import json
import streamlit as st

# ── Color Palette ─────────────────────────────────────────────────────────────
BRAND_BLUE = "#2ea3f2"
NAVY = "#1b3a5c"
DARK = "#2D3748"
BODY = "#666666"
PAGE_BG = "#F7FAFC"
OLIVE = "#4a5d23"
GOLD = "#c9a227"
GRAY_TIER = "#888888"
RED_ACCENT = "#C53030"
GREEN = "#2F855A"
AMBER = "#D69E2E"

# ── Navy Chart Color Sequence ────────────────────────────────────────────────
CHART_COLORS = [
    "#1B3A5C", "#2C5282", "#3182CE", "#63B3ED",
    "#C53030", "#FC8181", "#2F855A", "#68D391",
]

# ── Trust Tiers ───────────────────────────────────────────────────────────────
TRUST_TIERS = {
    "official": {
        "label": "SAM.gov Registration",
        "color": OLIVE,
        "bg": "#f0f4e8",
        "weight": 4,
        "fields": [
            "uei", "cage_code", "legal_business_name", "business_type",
            "registration_status", "registration_expiration", "entity_start_date",
        ],
    },
    "verified": {
        "label": "Industry Data",
        "color": GOLD,
        "bg": "#fdf8e8",
        "weight": 3,
        "fields": [
            "naics_codes", "naics_descriptions", "dba_name",
            "service_branch", "owner_name", "certification_date",
        ],
    },
    "third_party": {
        "label": "Contact Info",
        "color": BRAND_BLUE,
        "bg": "#e8f4fd",
        "weight": 2,
        "fields": [
            "phone", "email", "website", "linkedin_url",
        ],
    },
    "web_discovery": {
        "label": "Location Data",
        "color": GRAY_TIER,
        "bg": "#f5f5f5",
        "weight": 1,
        "fields": [
            "physical_address_line1", "physical_address_line2",
            "city", "state", "zip_code", "country",
            "latitude", "longitude", "distance_miles",
        ],
    },
}

FIELD_LABELS = {
    "uei": "UEI",
    "cage_code": "CAGE Code",
    "legal_business_name": "Legal Name",
    "business_type": "Business Type",
    "registration_status": "Reg. Status",
    "registration_expiration": "Reg. Expiration",
    "entity_start_date": "Entity Start",
    "naics_codes": "NAICS Codes",
    "naics_descriptions": "Industry",
    "dba_name": "DBA Name",
    "service_branch": "Service Branch",
    "owner_name": "Owner / Founder",
    "certification_date": "Certification Date",
    "phone": "Phone",
    "email": "Email",
    "website": "Website",
    "linkedin_url": "LinkedIn",
    "physical_address_line1": "Address Line 1",
    "physical_address_line2": "Address Line 2",
    "city": "City",
    "state": "State",
    "zip_code": "Zip Code",
    "country": "Country",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "distance_miles": "Distance (mi)",
}

FIELD_TO_TIER = {}
for _tk, _ti in TRUST_TIERS.items():
    for _f in _ti["fields"]:
        FIELD_TO_TIER[_f] = _tk

# ── Confidence Grades ────────────────────────────────────────────────────────
CONFIDENCE_GRADES = [
    {"min": 40, "grade": "A", "label": "Well Documented", "color": "#2e7d32"},
    {"min": 25, "grade": "B", "label": "Good Coverage",   "color": "#558b2f"},
    {"min": 15, "grade": "C", "label": "Core Data",       "color": "#2979b9"},
    {"min": 5,  "grade": "D", "label": "Basic Info",      "color": "#ef6c00"},
    {"min": 0,  "grade": "F", "label": "Needs Data",      "color": "#c62828"},
]

# ── Field Groups (for confidence breakdown) ──────────────────────────────────
FIELD_GROUPS = {
    "identity": {
        "label": "Identity",
        "icon": "🏢",
        "fields": ["legal_business_name", "dba_name", "business_type"],
        "source_hint": "SAM.gov",
    },
    "registration": {
        "label": "Registration",
        "icon": "🛡️",
        "fields": ["uei", "cage_code", "registration_status", "registration_expiration", "entity_start_date"],
        "source_hint": "SAM.gov",
    },
    "location": {
        "label": "Location",
        "icon": "📍",
        "fields": ["physical_address_line1", "city", "state", "zip_code"],
        "source_hint": "SAM.gov",
    },
    "industry": {
        "label": "Industry",
        "icon": "📋",
        "fields": ["naics_codes", "naics_descriptions"],
        "source_hint": "SAM.gov",
    },
    "service": {
        "label": "Service Info",
        "icon": "🎖️",
        "fields": ["service_branch", "certification_date"],
        "source_hint": "SAM.gov / Manual",
    },
    "contact": {
        "label": "Contact",
        "icon": "📞",
        "fields": ["phone", "email", "website"],
        "source_hint": "Web Enrichment",
    },
    "geography": {
        "label": "Geography",
        "icon": "🌍",
        "fields": ["latitude", "longitude", "distance_miles"],
        "source_hint": "Geocoded",
    },
}


# ── Confidence Grade Criteria (rule-based, top-down) ────────────────────────
#
# A (Comprehensive): Address + Contact + Industry
# B (Strong):        Address + (Contact or Industry)
# C (Core Data):     Name + City + State
# D (Partial):       Name + (State or City)
# F (Sparse):        Else
#
GRADE_CRITERIA = [
    {
        "grade": "A", "label": "Comprehensive", "color": "#2F855A",
        "description": "Has address, contact info, and industry data",
    },
    {
        "grade": "B", "label": "Strong", "color": "#2C5282",
        "description": "Has address plus contact or industry data",
    },
    {
        "grade": "C", "label": "Core Data", "color": "#D69E2E",
        "description": "Has name, city, and state",
    },
    {
        "grade": "D", "label": "Partial", "color": "#DD6B20",
        "description": "Has name plus state or city",
    },
    {
        "grade": "F", "label": "Sparse", "color": "#C53030",
        "description": "Missing most key fields",
    },
]

GRADE_INFO = {g["grade"]: g for g in GRADE_CRITERIA}
GRADE_OPTIONS = [f"{g['grade']} - {g['label']}" for g in GRADE_CRITERIA]


# ── Source Icons ─────────────────────────────────────────────────────────────
_SOURCE_ICONS = {
    "official":      ("🛡️", "SAM.gov verified"),
    "verified":      ("📋", "Industry data"),
    "third_party":   ("🌐", "Web-discovered"),
    "web_discovery": ("📍", "Geocoded / web"),
}


# ── Branded CSS ───────────────────────────────────────────────────────────────
BRANDED_CSS = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', 'Open Sans', sans-serif;
    }

    /* Navy sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b3a5c 0%, #15304d 100%) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #d0dbe6 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #a0b8cf !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
    }
    section[data-testid="stSidebar"] label {
        color: #d0dbe6 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        color: #d0dbe6 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background: rgba(46,163,242,0.15) !important;
        color: #ffffff !important;
        border-color: rgba(46,163,242,0.4) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        background: #2ea3f2 !important;
        color: white !important;
        border: none !important;
    }
    section[data-testid="stSidebar"] a {
        color: #a0b8cf !important;
    }
    section[data-testid="stSidebar"] a:hover {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {
        color: #d0dbe6 !important;
    }

    /* Brand blue active tab underline */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #1B3A5C !important;
        color: #1B3A5C !important;
    }

    /* Default metric cards (fallback) */
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #2D3748; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; color: #666666; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e0e4e8;
        border-radius: 0.75rem;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }

    /* Custom metric card */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        text-align: left;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }
    .metric-card .mc-icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .metric-card .mc-value { font-size: 1.8rem; font-weight: 800; color: #2D3748; line-height: 1.2; }
    .metric-card .mc-label { font-size: 0.85rem; color: #718096; margin-top: 0.15rem; }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #1b3a5c 0%, #2C5282 50%, #3182CE 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -40px;
        right: -40px;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: rgba(255,255,255,0.06);
        pointer-events: none;
    }
    .hero-header::after {
        content: '';
        position: absolute;
        bottom: -30px;
        left: 30%;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: rgba(255,255,255,0.04);
        pointer-events: none;
    }
    .hero-header h1 {
        color: #ffffff !important;
        margin-bottom: 0.25rem;
        font-size: 2rem;
        position: relative;
    }
    .hero-header p { color: #d4e8f0; margin: 0; font-size: 1.05rem; position: relative; }

    /* Headers */
    h1 { color: #1b3a5c; }
    h2 { color: #2D3748; }
    h3 { color: #2C5282; }

    /* Tier badge styles */
    .tier-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
        white-space: nowrap;
    }
    .tier-official { background: #4a5d23; }
    .tier-verified { background: #c9a227; }
    .tier-third-party { background: #2ea3f2; }
    .tier-web-discovery { background: #888888; }

    /* Grade badge styles */
    .grade-badge {
        display: inline-block;
        padding: 3px 14px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 700;
        color: white;
        white-space: nowrap;
        letter-spacing: 0.3px;
    }
    .grade-A { background: #2F855A; }
    .grade-B { background: #2C5282; }
    .grade-C { background: #D69E2E; }
    .grade-D { background: #DD6B20; }
    .grade-F { background: #C53030; }

    /* Source tags */
    .source-tag {
        display: inline-block;
        background: #EDF2F7;
        color: #4A5568;
        border: 1px solid #E2E8F0;
        padding: 1px 8px;
        border-radius: 8px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 3px;
    }

    /* Confidence breakdown grid */
    .conf-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.75rem;
        margin: 0.75rem 0;
    }
    .conf-group-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 0.5rem;
        padding: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .conf-group-card .cg-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.35rem;
    }
    .conf-group-card .cg-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #2D3748;
    }
    .conf-group-card .cg-count {
        font-size: 0.72rem;
        color: #718096;
    }
    .conf-group-card .cg-bar {
        height: 6px;
        background: #EDF2F7;
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 0.25rem;
    }
    .conf-group-card .cg-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    /* Links */
    a { color: #3182CE; }

    /* Smooth transitions on interactive elements */
    button, [role="button"], .stButton > button {
        transition: background 0.15s ease, transform 0.1s ease;
    }
</style>"""


# ── Helper Functions ──────────────────────────────────────────────────────────

def inject_branding():
    """Inject the branded CSS into the current page."""
    st.markdown(BRANDED_CSS, unsafe_allow_html=True)


def sidebar_brand():
    """Render the branded sidebar header."""
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0 1rem 0;">'
        '<h2 style="margin-bottom: 0;">&#127894; Veteran Business<br>Directory</h2>'
        '<p style="font-size: 0.85rem;">Active Heroes &bull; Shepherdsville, KY</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def tier_summary(biz):
    """Return a string summarizing which tiers have data for this business."""
    present = []
    for tier_info in TRUST_TIERS.values():
        if any(biz.get(f) for f in tier_info["fields"]):
            present.append(tier_info["label"])
    return " + ".join(present) if present else "No data"


def tier_has_data(biz, tier_key):
    """Check if a business has any data for a given tier."""
    return any(biz.get(f) for f in TRUST_TIERS[tier_key]["fields"])


# ── Confidence Scoring ───────────────────────────────────────────────────────

def compute_confidence_score(biz):
    """Compute a confidence score (0-100) with grade, label, and color.

    Weights: Official x4, Verified x3, Third Party x2, Web Discovery x1.
    Each tier contribution = (filled / total fields) * weight.
    Score = sum of contributions / max possible * 100.
    """
    total_weighted = 0.0
    max_weighted = 0.0
    tier_details = {}

    for tier_key, tier_info in TRUST_TIERS.items():
        fields = tier_info["fields"]
        weight = tier_info["weight"]
        filled = sum(1 for f in fields if biz.get(f))
        total = len(fields)
        contribution = (filled / total * weight) if total > 0 else 0
        total_weighted += contribution
        max_weighted += weight
        tier_details[tier_key] = {
            "filled": filled,
            "total": total,
            "weight": weight,
            "pct": round(filled / total * 100) if total > 0 else 0,
        }

    score = round(total_weighted / max_weighted * 100) if max_weighted > 0 else 0

    grade_info = CONFIDENCE_GRADES[-1]
    for g in CONFIDENCE_GRADES:
        if score >= g["min"]:
            grade_info = g
            break

    return {
        "score": score,
        "grade": grade_info["grade"],
        "label": grade_info["label"],
        "color": grade_info["color"],
        "tiers": tier_details,
    }


def confidence_badge_html(biz):
    """Compact colored pill: 'B (68%)'."""
    info = compute_confidence_score(biz)
    return (
        f'<span style="display:inline-block; background:{info["color"]}; color:white; '
        f'padding:2px 10px; border-radius:10px; font-size:0.78rem; font-weight:700; '
        f'white-space:nowrap;">'
        f'{info["grade"]} ({info["score"]}%)</span>'
    )


def confidence_meter_html(biz):
    """Small 4-segment horizontal bar; each segment = tier, width proportional to weight."""
    info = compute_confidence_score(biz)
    total_weight = sum(t["weight"] for t in TRUST_TIERS.values())
    segments = ""
    for tier_key, tier_info in TRUST_TIERS.items():
        td = info["tiers"][tier_key]
        width_pct = round(td["weight"] / total_weight * 100)
        fill_color = tier_info["color"] if td["filled"] > 0 else "#e0e0e0"
        opacity = max(0.3, td["pct"] / 100) if td["filled"] > 0 else 1.0
        segments += (
            f'<div style="width:{width_pct}%; height:8px; background:{fill_color}; '
            f'opacity:{opacity}; border-radius:2px;" '
            f'title="{tier_info["label"]}: {td["filled"]}/{td["total"]}"></div>'
        )
    return (
        f'<div style="display:flex; gap:2px; width:100%; max-width:120px; align-items:center;">'
        f'{segments}</div>'
    )


# ── Rule-Based Grade Assignment ──────────────────────────────────────────────

def assign_confidence_grade(biz):
    """Assign a letter grade A-F based on what field groups are present.

    Returns dict with grade, label, color, description.
    """
    has_name = bool(biz.get("legal_business_name"))
    has_city = bool(biz.get("city"))
    has_state = bool(biz.get("state"))
    has_address = has_city and has_state and bool(biz.get("physical_address_line1"))
    has_industry = bool(biz.get("naics_codes")) or bool(biz.get("naics_descriptions"))
    has_contact = bool(biz.get("phone")) or bool(biz.get("email")) or bool(biz.get("website"))

    if has_address and has_contact and has_industry:
        grade = "A"
    elif has_address and (has_contact or has_industry):
        grade = "B"
    elif has_name and has_city and has_state:
        grade = "C"
    elif has_name and (has_state or has_city):
        grade = "D"
    else:
        grade = "F"

    info = GRADE_INFO[grade]
    return {
        "grade": info["grade"],
        "label": info["label"],
        "color": info["color"],
        "description": info["description"],
    }


_COMPLETENESS_FIELDS = [
    "legal_business_name", "dba_name", "business_type",
    "physical_address_line1", "city", "state", "zip_code",
    "phone", "email", "website",
    "naics_codes", "naics_descriptions",
    "uei", "cage_code",
    "registration_status", "owner_name", "service_branch",
]


def compute_completeness_pct(biz):
    """Return 0-100 completeness percentage based on 17 scored fields."""
    filled = sum(1 for f in _COMPLETENESS_FIELDS if biz.get(f))
    return round(filled / len(_COMPLETENESS_FIELDS) * 100)


def completeness_bar_html(biz):
    """Horizontal bar with percentage and small grade badge."""
    pct = compute_completeness_pct(biz)
    grade_info = assign_confidence_grade(biz)
    bar_color = grade_info["color"]
    return (
        f'<div style="display:flex; align-items:center; gap:10px;">'
        f'<div style="flex:1; height:10px; background:#E2E8F0; border-radius:5px; overflow:hidden;">'
        f'<div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:5px;"></div>'
        f'</div>'
        f'<span style="font-size:0.9rem; font-weight:700; color:#333; min-width:40px;">{pct}%</span>'
        f'<span class="grade-badge grade-{grade_info["grade"]}" '
        f'style="font-size:0.7rem; padding:2px 8px;">{grade_info["grade"]}</span>'
        f'</div>'
    )


def calculate_confidence_detail(biz):
    """Compute per-field-group breakdown for a business.

    Returns dict with: grade info + groups dict (group_key -> filled/total/source/fields).
    """
    grade_info = assign_confidence_grade(biz)
    groups = {}

    for group_key, group_def in FIELD_GROUPS.items():
        fields = group_def["fields"]
        field_status = {}
        filled = 0
        for f in fields:
            has_value = bool(biz.get(f))
            field_status[f] = has_value
            if has_value:
                filled += 1
        groups[group_key] = {
            "label": group_def["label"],
            "icon": group_def["icon"],
            "filled": filled,
            "total": len(fields),
            "source": group_def["source_hint"],
            "fields": field_status,
        }

    return {
        "grade": grade_info["grade"],
        "label": grade_info["label"],
        "color": grade_info["color"],
        "groups": groups,
    }


# ── Grade Badge HTML ─────────────────────────────────────────────────────────

def grade_badge_html(grade, show_label=True):
    """Return a colored pill badge for a letter grade."""
    info = GRADE_INFO.get(grade, GRADE_INFO["F"])
    label_text = f" {info['label']}" if show_label else ""
    return (
        f'<span class="grade-badge grade-{grade}">'
        f'{grade}{label_text}</span>'
    )


def grade_badge_with_score_html(biz):
    """Return grade badge + confidence score percentage."""
    conf = compute_confidence_score(biz)
    grade_info = assign_confidence_grade(biz)
    return (
        f'<span class="grade-badge grade-{grade_info["grade"]}">'
        f'{grade_info["grade"]} ({conf["score"]}%)</span>'
    )


# ── Confidence Breakdown Renderer ────────────────────────────────────────────

def render_confidence_breakdown(biz):
    """Render a 3-column grid of field-group cards with progress bars."""
    detail = calculate_confidence_detail(biz)
    cards = ""

    for group_key, group in detail["groups"].items():
        filled = group["filled"]
        total = group["total"]
        pct = round(filled / total * 100) if total > 0 else 0
        bar_color = "#2F855A" if pct >= 80 else "#3182CE" if pct >= 40 else "#D69E2E" if pct > 0 else "#E2E8F0"

        cards += (
            f'<div class="conf-group-card">'
            f'<div class="cg-header">'
            f'<span class="cg-label">{group["icon"]} {group["label"]}</span>'
            f'<span class="cg-count">{filled}/{total}</span>'
            f'</div>'
            f'<div class="cg-bar"><div class="cg-bar-fill" '
            f'style="width:{pct}%; background:{bar_color};"></div></div>'
            f'<span class="source-tag">{group["source"]}</span>'
            f'</div>'
        )

    return (
        f'<div class="conf-grid">{cards}</div>'
    )


# ── Metric Card Helper ───────────────────────────────────────────────────────

def metric_card(label, value, icon="", border_color=NAVY):
    """Return HTML for a styled KPI card with icon, value, and label."""
    return (
        f'<div class="metric-card" style="border-top: 3px solid {border_color};">'
        f'<div class="mc-icon">{icon}</div>'
        f'<div class="mc-value">{value}</div>'
        f'<div class="mc-label">{label}</div>'
        f'</div>'
    )


# ── Chart Style Helper ───────────────────────────────────────────────────────

def style_chart(fig, height=400):
    """Apply consistent Plotly theming with navy color sequence."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", color="#2D3748"),
        colorway=CHART_COLORS,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


# ── Per-Field Source Indicators ──────────────────────────────────────────────

def infer_field_source(biz, field_name):
    """Return (icon, tooltip) for a field based on its tier."""
    tier_key = FIELD_TO_TIER.get(field_name)
    if not tier_key:
        return ("", "")
    icon, tooltip = _SOURCE_ICONS.get(tier_key, ("", ""))
    return (icon, tooltip)


def _source_icon_html(biz, field_name):
    """Small inline HTML icon with tooltip for a field's source."""
    icon, tooltip = infer_field_source(biz, field_name)
    if not icon:
        return ""
    return (
        f'<span title="{_html.escape(tooltip)}" '
        f'style="font-size:0.7rem; cursor:help; margin-left:4px;">{icon}</span>'
    )


# ── Render Functions ─────────────────────────────────────────────────────────

def render_tier_badges_html(biz):
    """Render inline tier badges showing which tiers have data."""
    badges = []
    for tier_key, tier_info in TRUST_TIERS.items():
        has = any(biz.get(f) for f in tier_info["fields"])
        css_class = f"tier-{tier_key.replace('_', '-')}"
        if has:
            badges.append(
                f'<span class="tier-badge {css_class}">{tier_info["label"]}</span>'
            )
        else:
            badges.append(
                f'<span class="tier-badge" style="background: #ddd; color: #999;">'
                f'{tier_info["label"]}</span>'
            )
    return " ".join(badges)


def render_tier_card_html(biz, tier_key):
    """Render an HTML card for one trust tier showing its fields."""
    tier = TRUST_TIERS[tier_key]
    fields = tier["fields"]
    filled = sum(1 for f in fields if biz.get(f))
    total = len(fields)

    # Segmented mini progress bar (one segment per field)
    progress_segments = ""
    for f in fields:
        seg_color = tier["color"] if biz.get(f) else "#e0e0e0"
        progress_segments += (
            f'<div style="flex:1; height:6px; background:{seg_color}; border-radius:3px;"></div>'
        )
    progress_bar = (
        f'<div style="display:flex; gap:2px; margin-top:2px;">{progress_segments}</div>'
    )

    rows_html = ""
    for field in fields:
        value = biz.get(field)
        label = FIELD_LABELS.get(field, field.replace("_", " ").title())
        src_icon = _source_icon_html(biz, field)
        if value:
            display = _html.escape(str(value))
            if field == "website":
                url = display if display.startswith("http") else f"https://{display}"
                display = (
                    f'<a href="{url}" target="_blank" '
                    f'style="color: {tier["color"]}; text-decoration: none;">{display}</a>'
                )
            elif field == "email" and "@" in display:
                display = (
                    f'<a href="mailto:{display}" '
                    f'style="color: {tier["color"]}; text-decoration: none;">{display}</a>'
                )
            elif field == "linkedin_url":
                url = display if display.startswith("http") else f"https://{display}"
                display = (
                    f'<a href="{url}" target="_blank" '
                    f'style="color: {tier["color"]}; text-decoration: none;">'
                    f'&#x1F517; {display}</a>'
                )
            elif field == "registration_status":
                display = "Active" if display == "A" else display
            rows_html += (
                f'<div style="padding: 4px 0;">'
                f'<div style="font-size: 0.7rem; color: #999; text-transform: uppercase; '
                f'letter-spacing: 0.5px;">{label}{src_icon}</div>'
                f'<div style="font-size: 0.9rem; color: #333;">{display}</div>'
                f'</div>'
            )
        else:
            rows_html += (
                f'<div style="padding: 4px 0;">'
                f'<div style="font-size: 0.7rem; color: #ccc; text-transform: uppercase; '
                f'letter-spacing: 0.5px;">{label}</div>'
                f'<div style="font-size: 0.9rem; color: #ccc;">&mdash;</div>'
                f'</div>'
            )

    return (
        f'<div style="border-left: 4px solid {tier["color"]}; background: {tier["bg"]}; '
        f'border-radius: 0 0.75rem 0.75rem 0; padding: 1rem 1.25rem; margin-bottom: 1rem; '
        f'box-shadow: 0 2px 8px rgba(0,0,0,0.05);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; '
        f'margin-bottom: 0.5rem;">'
        f'<span style="background: {tier["color"]}; color: white; '
        f'padding: 3px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">'
        f'{tier["label"]}</span>'
        f'<span style="color: #888; font-size: 0.85rem;">{filled}/{total}</span>'
        f'</div>'
        f'{progress_bar}'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); '
        f'gap: 0.5rem 1.5rem; margin-top: 0.75rem;">'
        f'{rows_html}'
        f'</div>'
        f'</div>'
    )


def render_tier_legend_html():
    """Render the trust tier legend with trust weight dots."""
    descriptions = {
        "official": "Government registration data from SAM.gov",
        "verified": "NAICS codes &amp; industry classifications",
        "third_party": "Phone, email, &amp; website data",
        "web_discovery": "Address &amp; geographic coordinates",
    }
    items = ""
    for tier_key, tier_info in TRUST_TIERS.items():
        css_class = f"tier-{tier_key.replace('_', '-')}"
        weight = tier_info["weight"]
        dots = ""
        for i in range(4):
            dot_color = tier_info["color"] if i < weight else "#ddd"
            dots += (
                f'<span style="display:inline-block; width:8px; height:8px; '
                f'border-radius:50%; background:{dot_color}; margin-right:2px;"></span>'
            )
        items += (
            f'<div style="display:flex; align-items:center; gap:8px; '
            f'padding:6px 12px; background:white; border-radius:8px; '
            f'border:1px solid #e8ecf0;">'
            f'<span class="tier-badge {css_class}" style="font-size:0.75rem;">'
            f'{tier_info["label"]}</span>'
            f'<span style="display:flex; align-items:center; gap:0;">{dots}</span>'
            f'<span style="color:#666; font-size:0.8rem;">{descriptions[tier_key]}</span>'
            f'</div>'
        )
    return (
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin:0.5rem 0 1rem 0;">'
        f'{items}'
        f'</div>'
    )


def render_confidence_banner_html(biz):
    """Large confidence banner for the business detail page.

    Leads with completeness %, grade as secondary badge, labelled
    "Data Completeness".
    """
    pct = compute_completeness_pct(biz)
    grade_info = assign_confidence_grade(biz)
    color = grade_info["color"]
    meter = confidence_meter_html(biz)
    wide_meter = meter.replace("max-width:120px", "max-width:300px")

    return (
        f'<div style="display:flex; align-items:center; gap:1.5rem; padding:1rem 1.5rem; '
        f'background:linear-gradient(135deg, {color}11, {color}22); '
        f'border:2px solid {color}44; border-radius:0.75rem; margin:0.75rem 0 1.25rem 0;">'
        f'<div style="font-size:2.5rem; font-weight:800; color:{color}; '
        f'line-height:1; min-width:50px; text-align:center;">{pct}%</div>'
        f'<div style="flex:1;">'
        f'<div style="font-size:0.85rem; font-weight:600; color:{color}; '
        f'margin-bottom:2px;">Data Completeness</div>'
        f'<div style="display:flex; align-items:center; gap:8px;">'
        f'<span class="grade-badge grade-{grade_info["grade"]}">'
        f'{grade_info["grade"]} {grade_info["label"]}</span>'
        f'</div>'
        f'{wide_meter}'
        f'</div>'
        f'</div>'
    )


def render_dashboard_tier_card(tier_key, stats):
    """Render a mini data-quality card for the dashboard.

    stats: dict with keys for each field -> True/False or count values
           OR a dict with 'filled' and 'total' keys.
    """
    tier = TRUST_TIERS[tier_key]
    filled = stats.get("filled", 0)
    total = stats.get("total", 1)
    pct = round(filled / total * 100) if total > 0 else 0

    # Per-field progress segments
    field_segments = ""
    field_stats = stats.get("fields", {})
    for f in tier["fields"]:
        f_pct = field_stats.get(f, 0)
        seg_color = tier["color"] if f_pct > 0 else "#e0e0e0"
        opacity = max(0.35, f_pct / 100) if f_pct > 0 else 1.0
        label = FIELD_LABELS.get(f, f)
        field_segments += (
            f'<div style="display:flex; align-items:center; gap:6px; margin:3px 0;">'
            f'<div style="flex:1; height:5px; background:#e8ecf0; border-radius:3px; overflow:hidden;">'
            f'<div style="width:{f_pct}%; height:100%; background:{tier["color"]}; '
            f'opacity:{opacity}; border-radius:3px;"></div></div>'
            f'<span style="font-size:0.7rem; color:#888; min-width:80px;">{label}</span>'
            f'<span style="font-size:0.7rem; color:#666; min-width:30px; text-align:right;">'
            f'{f_pct}%</span>'
            f'</div>'
        )

    return (
        f'<div style="background:white; border:1px solid #e8ecf0; border-radius:0.75rem; '
        f'padding:1rem 1.25rem; box-shadow:0 2px 8px rgba(0,0,0,0.05);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; '
        f'margin-bottom:0.5rem;">'
        f'<span style="background:{tier["color"]}; color:white; padding:3px 10px; '
        f'border-radius:10px; font-size:0.75rem; font-weight:600;">{tier["label"]}</span>'
        f'<span style="font-size:1.1rem; font-weight:700; color:{tier["color"]};">{pct}%</span>'
        f'</div>'
        f'<div style="height:4px; background:#e8ecf0; border-radius:2px; overflow:hidden; '
        f'margin-bottom:0.75rem;">'
        f'<div style="width:{pct}%; height:100%; background:{tier["color"]}; '
        f'border-radius:2px;"></div></div>'
        f'{field_segments}'
        f'</div>'
    )


def yelp_stars_html(biz):
    """Render Yelp star rating with review count and link."""
    rating = biz.get("yelp_rating")
    if rating is None:
        return ""
    review_count = biz.get("yelp_review_count", 0)
    url = biz.get("yelp_url", "")

    # Build star display
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    stars = "★" * full_stars
    if half_star:
        stars += "½"

    # Yelp red color
    yelp_color = "#D32323"
    link_open = f'<a href="{_html.escape(url)}" target="_blank" style="text-decoration:none;">' if url else ""
    link_close = "</a>" if url else ""

    return (
        f'{link_open}'
        f'<span style="color:{yelp_color}; font-size:0.85rem; font-weight:700;">'
        f'{stars}</span> '
        f'<span style="font-size:0.82rem; font-weight:600; color:#333;">{rating}</span> '
        f'<span style="font-size:0.75rem; color:#718096;">({review_count:,} reviews)</span>'
        f'{link_close}'
    )


def render_source_badge_html(source_text):
    """Render a colored source badge for metadata display."""
    if not source_text:
        return '<span style="color:#999;">Unknown</span>'
    colors = {
        "sam.gov": OLIVE,
        "sam": OLIVE,
        "web": BRAND_BLUE,
        "google": BRAND_BLUE,
        "manual": GOLD,
        "csv": GRAY_TIER,
        "import": GRAY_TIER,
    }
    badge_color = GRAY_TIER
    lower = source_text.lower()
    for key, color in colors.items():
        if key in lower:
            badge_color = color
            break

    parts = [s.strip() for s in source_text.split(",")]
    badges = ""
    for part in parts:
        c = GRAY_TIER
        pl = part.lower()
        for key, color in colors.items():
            if key in pl:
                c = color
                break
        badges += (
            f'<span style="display:inline-block; background:{c}18; color:{c}; '
            f'border:1px solid {c}44; padding:1px 8px; border-radius:8px; '
            f'font-size:0.75rem; font-weight:600; margin-right:4px;">'
            f'{_html.escape(part)}</span>'
        )
    return badges
