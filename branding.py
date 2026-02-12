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
        "fields": [
            "uei", "cage_code", "legal_business_name", "business_type",
            "registration_status", "registration_expiration", "entity_start_date",
        ],
    },
    "verified": {
        "label": "Industry Data",
        "color": GOLD,
        "bg": "#fdf8e8",
        "fields": [
            "naics_codes", "naics_descriptions", "dba_name",
            "service_branch", "certification_date",
        ],
    },
    "third_party": {
        "label": "Contact Info",
        "color": BRAND_BLUE,
        "bg": "#e8f4fd",
        "fields": [
            "phone", "email", "website",
        ],
    },
    "web_discovery": {
        "label": "Location Data",
        "color": GRAY_TIER,
        "bg": "#f5f5f5",
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
    }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #2ea3f2 0%, #1b3a5c 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
    }
    .hero-header h1 {
        color: #ffffff !important;
        margin-bottom: 0.25rem;
        font-size: 2rem;
    }
    .hero-header p { color: #d4e8f0; margin: 0; font-size: 1.05rem; }

    /* Headers */
    h1, h2, h3 { color: #333333; }

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
    pct = round(filled / total * 100) if total > 0 else 0

    rows_html = ""
    for field in fields:
        value = biz.get(field)
        label = FIELD_LABELS.get(field, field.replace("_", " ").title())
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
                f'letter-spacing: 0.5px;">{label}</div>'
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
        f'border-radius: 0 0.5rem 0.5rem 0; padding: 1rem 1.25rem; margin-bottom: 1rem;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; '
        f'margin-bottom: 0.75rem;">'
        f'<span style="background: {tier["color"]}; color: white; '
        f'padding: 3px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">'
        f'{tier["label"]}</span>'
        f'<span style="color: #888; font-size: 0.85rem;">{filled}/{total} fields ({pct}%)</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); '
        f'gap: 0.5rem 1.5rem;">'
        f'{rows_html}'
        f'</div>'
        f'</div>'
    )


def render_tier_legend_html():
    """Render the trust tier legend with badges and descriptions."""
    descriptions = {
        "official": "Government registration data from SAM.gov",
        "verified": "NAICS codes &amp; industry classifications",
        "third_party": "Phone, email, &amp; website data",
        "web_discovery": "Address &amp; geographic coordinates",
    }
    items = ""
    for tier_key, tier_info in TRUST_TIERS.items():
        css_class = f"tier-{tier_key.replace('_', '-')}"
        items += (
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span class="tier-badge {css_class}">{tier_info["label"]}</span>'
            f'<span style="color: #666; font-size: 0.85rem;">{descriptions[tier_key]}</span>'
            f'</div>'
        )
    return (
        f'<div style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 0.5rem 0 1rem 0;">'
        f'{items}'
        f'</div>'
    )
