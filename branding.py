"""Active Heroes branded UI components and trust tier configuration."""

import html as _html
import streamlit as st

# ── Color Palette ─────────────────────────────────────────────────────────────
BRAND_BLUE = "#2ea3f2"
NAVY = "#1b3a5c"
DARK = "#333333"
BODY = "#666666"
PAGE_BG = "#f7f8fa"
OLIVE = "#4a5d23"
GOLD = "#c9a227"
GRAY_TIER = "#888888"

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
            "service_branch", "certification_date",
        ],
    },
    "third_party": {
        "label": "Contact Info",
        "color": BRAND_BLUE,
        "bg": "#e8f4fd",
        "weight": 2,
        "fields": [
            "phone", "email", "website",
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
    "certification_date": "Certification Date",
    "phone": "Phone",
    "email": "Email",
    "website": "Website",
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

# ── Source Icons ─────────────────────────────────────────────────────────────
_SOURCE_ICONS = {
    "official":      ("🛡️", "SAM.gov verified"),
    "verified":      ("📋", "Industry data"),
    "third_party":   ("🌐", "Web-discovered"),
    "web_discovery": ("📍", "Geocoded / web"),
}


# ── Branded CSS ───────────────────────────────────────────────────────────────
BRANDED_CSS = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Open Sans', sans-serif;
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
        border-bottom-color: #2ea3f2 !important;
        color: #2ea3f2 !important;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #333333; }
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

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #1b3a5c 0%, #2ea3f2 60%, #4a5d23 100%);
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
    h2 { color: #333333; }
    h3 { color: #4a5d23; }

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

    /* Links */
    a { color: #2ea3f2; }

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
    """Large confidence banner for the business detail page."""
    info = compute_confidence_score(biz)
    meter = confidence_meter_html(biz)
    # Wider meter for the banner
    wide_meter = meter.replace("max-width:120px", "max-width:300px")

    return (
        f'<div style="display:flex; align-items:center; gap:1.5rem; padding:1rem 1.5rem; '
        f'background:linear-gradient(135deg, {info["color"]}11, {info["color"]}22); '
        f'border:2px solid {info["color"]}44; border-radius:0.75rem; margin:0.75rem 0 1.25rem 0;">'
        f'<div style="font-size:2.5rem; font-weight:800; color:{info["color"]}; '
        f'line-height:1; min-width:50px; text-align:center;">{info["grade"]}</div>'
        f'<div style="flex:1;">'
        f'<div style="font-size:0.85rem; font-weight:600; color:{info["color"]}; '
        f'margin-bottom:2px;">{info["label"]} Data Quality</div>'
        f'<div style="font-size:1.4rem; font-weight:700; color:#333;">{info["score"]}%</div>'
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
