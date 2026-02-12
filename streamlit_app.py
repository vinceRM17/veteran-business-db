import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from database import (
    create_tables, get_stats, get_contact_stats, get_map_data,
    get_all_businesses_with_coords, get_all_fetch_status,
    get_tier_completeness_stats, get_grade_distribution,
)
from geo import zip_to_coords, filter_by_custom_radius
from config import ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON
from branding import (
    inject_branding, sidebar_brand, render_tier_legend_html, BRAND_BLUE, NAVY,
    TRUST_TIERS, tier_has_data, confidence_badge_html,
    render_dashboard_tier_card, compute_confidence_score, CONFIDENCE_GRADES,
    assign_confidence_grade, grade_badge_html, metric_card, style_chart,
    GRADE_CRITERIA, GRADE_INFO, GRADE_OPTIONS, CHART_COLORS,
)

st.set_page_config(
    page_title="Veteran Business Directory | Active Heroes",
    page_icon="🎖️",
    layout="wide",
)

inject_branding()

create_tables()

# --- Auth state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Selection state (shared across pages) ---
if "selected_businesses" not in st.session_state:
    st.session_state.selected_businesses = set()

# --- Sidebar ---
with st.sidebar:
    sidebar_brand()
    st.divider()

    if st.session_state.logged_in:
        st.success("Logged in as Admin")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        with st.expander("Admin Login"):
            pwd = st.text_input("Password", type="password", key="login_pwd")
            if st.button("Log In"):
                from config import ADMIN_PASSWORD
                if pwd == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password")

    # Selection badge
    sel_count = len(st.session_state.selected_businesses)
    if sel_count > 0:
        st.divider()
        st.markdown(f"**{sel_count} business{'es' if sel_count != 1 else ''} selected**")
        if st.button("View Report", key="sidebar_report"):
            st.switch_page("pages/5_📊_Report.py")

    # --- Grade-based filter ---
    st.divider()
    grade_dist = get_grade_distribution()
    total_biz = sum(grade_dist.values())

    # Grade multiselect
    grade_filter = st.multiselect(
        "Filter by Data Quality Grade",
        options=GRADE_OPTIONS,
        default=[],
        key="dash_grade_filter",
    )
    _required_grades = [g.split(" - ")[0] for g in grade_filter]

    # Grade distribution summary
    if total_biz > 0:
        dist_parts = []
        for gc in GRADE_CRITERIA:
            g = gc["grade"]
            cnt = grade_dist.get(g, 0)
            dist_parts.append(f"**{g}**: {cnt:,}")
        st.markdown(
            f'<div style="font-size:0.78rem; line-height:1.6; color:#a0b8cf;">'
            + " &bull; ".join(dist_parts) + "</div>",
            unsafe_allow_html=True,
        )

    # Advanced: Tier filter + numeric confidence (in expander)
    with st.expander("Advanced Filters"):
        tier_options = {info["label"]: key for key, info in TRUST_TIERS.items()}
        required_tiers = st.multiselect(
            "Must have data from tier",
            options=list(tier_options.keys()),
            default=[],
            key="dash_tier_filter",
        )
        _required_tier_keys = [tier_options[label] for label in required_tiers]

    # Sidebar footer
    st.markdown(
        '<div style="text-align:center; padding-top:1.5rem; font-size:0.72rem; color:#5a7a96;">'
        'Built for Active Heroes<br>'
        'Shepherdsville, KY'
        '</div>',
        unsafe_allow_html=True,
    )

# --- Dashboard Header ---
stats = get_stats()
contact_stats = get_contact_stats()
tier_stats = get_tier_completeness_stats()

# Compute aggregate data quality grade from tier stats
_agg_score = 0
if tier_stats:
    _weights = {k: TRUST_TIERS[k]["weight"] for k in TRUST_TIERS}
    _total_w = sum(_weights.values())
    _agg_score = round(
        sum(tier_stats[k]["pct"] * _weights[k] for k in tier_stats) / _total_w
    ) if _total_w > 0 else 0

_agg_grade_info = CONFIDENCE_GRADES[-1]
for _g in CONFIDENCE_GRADES:
    if _agg_score >= _g["min"]:
        _agg_grade_info = _g
        break

_quality_badge = (
    f'<div style="display:inline-flex; align-items:center; gap:8px; '
    f'background:rgba(255,255,255,0.15); backdrop-filter:blur(8px); '
    f'border:1px solid rgba(255,255,255,0.25); border-radius:12px; '
    f'padding:6px 16px; margin-top:0.75rem;">'
    f'<span style="font-size:1.3rem; font-weight:800; color:white;">'
    f'{_agg_grade_info["grade"]}</span>'
    f'<span style="color:#d4e8f0; font-size:0.85rem;">'
    f'Data Quality: {_agg_score}%</span>'
    f'</div>'
) if tier_stats else ""

st.markdown(f"""
<div class="hero-header">
    <h1>Veteran Business Directory</h1>
    <p>Built for Active Heroes &bull; Connecting veteran-owned businesses near Shepherdsville, KY</p>
    {_quality_badge}
</div>
""", unsafe_allow_html=True)

if stats["total"] == 0:
    st.warning("Database is empty. Use the **Fetch Data** or **Import CSV** page to load businesses.")
    st.stop()

# --- KPI Metric Cards ---
vob_count = 0
sdvosb_count = 0
for t, c in stats.get("by_type", {}).items():
    if "Service Disabled" in (t or ""):
        sdvosb_count += c
    else:
        vob_count += c

has_any_contact = 0
contact_pct = 0
if contact_stats["total"] > 0:
    has_any_contact = max(contact_stats["has_phone"], contact_stats["has_email"], contact_stats["has_website"])
    contact_pct = round(has_any_contact / contact_stats["total"] * 100)

# Grade A count
grade_a_count = grade_dist.get("A", 0)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(metric_card("Total Businesses", f"{stats['total']:,}", "🏢", NAVY), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("VOB", f"{vob_count:,}", "🎖️", "#2F855A"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("SDVOSB", f"{sdvosb_count:,}", "🏅", "#2C5282"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("Have Contact Info", f"{contact_pct}%", "📞", "#D69E2E"), unsafe_allow_html=True)
with col5:
    st.markdown(metric_card("Grade A (Verified)", f"{grade_a_count:,}", "✅", "#2F855A"), unsafe_allow_html=True)

# --- Data Quality Overview ---
st.subheader("Data Quality Overview")
st.markdown(render_tier_legend_html(), unsafe_allow_html=True)

if tier_stats:
    dq_cols = st.columns(4)
    for i, (tier_key, tier_info) in enumerate(TRUST_TIERS.items()):
        with dq_cols[i]:
            st.markdown(
                render_dashboard_tier_card(tier_key, tier_stats[tier_key]),
                unsafe_allow_html=True,
            )

# --- Grade Distribution Chart ---
if total_biz > 0:
    st.subheader("Confidence Grade Distribution")
    grade_df = pd.DataFrame([
        {"Grade": f"{g} - {GRADE_INFO[g]['label']}", "Count": grade_dist.get(g, 0), "Color": GRADE_INFO[g]["color"]}
        for g in ("A", "B", "C", "D", "F")
    ])
    fig_grade = px.bar(
        grade_df, x="Grade", y="Count",
        color="Grade",
        color_discrete_map={
            f"{g} - {GRADE_INFO[g]['label']}": GRADE_INFO[g]["color"]
            for g in ("A", "B", "C", "D", "F")
        },
        title="Businesses by Data Quality Grade",
    )
    fig_grade.update_layout(showlegend=False)
    style_chart(fig_grade, height=300)
    st.plotly_chart(fig_grade, use_container_width=True)

# --- Map Hero Section ---
st.subheader("Business Locations")

# Default HQ-based distance filter
dist_filter = st.select_slider(
    "Distance from HQ",
    options=[25, 50, 75, 100],
    value=100,
    format_func=lambda x: f"{x} miles",
)

# Custom location toggle for map
map_custom_location = st.toggle("Search from a different location", key="map_custom_location")

map_center_lat = ACTIVE_HEROES_LAT
map_center_lon = ACTIVE_HEROES_LON
map_custom_zip = None
distance_key = "distance_miles"
distance_from_label = "HQ"
using_custom = False

if map_custom_location:
    mc_col1, mc_col2 = st.columns([1, 2])
    with mc_col1:
        map_custom_zip = st.text_input("Zip Code", max_chars=5, placeholder="e.g. 40202", key="map_zip")
    with mc_col2:
        map_custom_radius = st.slider("Radius (miles)", min_value=10, max_value=250, value=50, step=5, key="map_radius")

    if map_custom_zip and len(map_custom_zip) == 5 and map_custom_zip.isdigit():
        clat, clon = zip_to_coords(map_custom_zip)
        if clat is not None:
            map_center_lat = clat
            map_center_lon = clon
            using_custom = True
            distance_key = "custom_distance_miles"
            distance_from_label = map_custom_zip
        else:
            st.warning(f"Could not find coordinates for zip code {map_custom_zip}.")
    elif map_custom_zip:
        st.warning("Please enter a valid 5-digit zip code.")

# Fetch data based on mode
if using_custom:
    all_biz = get_all_businesses_with_coords()
    data = filter_by_custom_radius(map_center_lat, map_center_lon, all_biz, map_custom_radius)
else:
    data = get_map_data(max_distance=dist_filter)

# Apply tier filter
if _required_tier_keys:
    data = [b for b in data if all(tier_has_data(b, tk) for tk in _required_tier_keys)]

# Apply grade filter
if _required_grades:
    data = [b for b in data if assign_confidence_grade(b)["grade"] in _required_grades]

if data:
    m = folium.Map(
        location=[map_center_lat, map_center_lon],
        zoom_start=8,
        tiles="CartoDB positron",
    )

    # Custom location marker (when searching from a different location)
    if using_custom:
        folium.Marker(
            location=[map_center_lat, map_center_lon],
            popup=folium.Popup(
                f"<div style='font-family: Inter, sans-serif;'>"
                f"<b style='font-size: 14px;'>Search Location</b><br>"
                f"<span style='color: #5a6c7d;'>Zip: {map_custom_zip}</span>"
                f"</div>",
                max_width=250,
            ),
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        ).add_to(m)

    # Active Heroes HQ marker
    folium.Marker(
        location=[ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON],
        popup=folium.Popup(
            "<div style='font-family: Inter, sans-serif;'>"
            "<b style='font-size: 14px;'>Active Heroes HQ</b><br>"
            "<span style='color: #5a6c7d;'>Shepherdsville, KY</span>"
            "</div>",
            max_width=250,
        ),
        icon=folium.Icon(color="darkred", icon="star", prefix="fa"),
    ).add_to(m)

    # Business markers — build coordinate lookup for click handling
    coord_to_id = {}
    for biz in data:
        bt = biz.get("business_type") or ""
        is_sdvosb = "Service Disabled" in bt
        color = "#2C5282" if is_sdvosb else "#2F855A"
        type_label = "SDVOSB" if is_sdvosb else "VOB"

        name = biz["legal_business_name"]
        city_state = f"{biz.get('city', '')}, {biz.get('state', '')}"
        dist = biz.get(distance_key)
        lat, lng = biz["latitude"], biz["longitude"]

        # Grade badge for popup
        biz_grade = assign_confidence_grade(biz)
        grade_html = (
            f'<span style="background:{biz_grade["color"]}; color:white; '
            f'padding:2px 8px; border-radius:8px; font-size:11px; font-weight:700;">'
            f'{biz_grade["grade"]}</span>'
        )

        # Store mapping for click detection
        coord_to_id[(round(lat, 5), round(lng, 5))] = biz["id"]

        popup_lines = [
            "<div style='font-family: Inter, sans-serif; line-height: 1.5;'>",
            f"<b style='font-size: 14px;'>{name}</b>",
        ]
        if biz.get("dba_name"):
            popup_lines.append(f"<i style='color: #7a8a99;'>DBA: {biz['dba_name']}</i>")
        popup_lines.append(f"<span style='color: #5a6c7d;'>{city_state}</span>")
        popup_lines.append(
            f"<span style='background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;'>{type_label}</span>"
            f" {grade_html}"
        )
        if dist is not None:
            popup_lines.append(f"<span style='color: #7a8a99;'>{dist} mi from {distance_from_label}</span>")
        if biz.get("phone"):
            popup_lines.append(f"📞 {biz['phone']}")
        if biz.get("email"):
            popup_lines.append(f"✉️ {biz['email']}")
        if biz.get("website"):
            popup_lines.append(f'🌐 <a href="{biz["website"]}" target="_blank" style="color: #3182CE;">{biz["website"]}</a>')
        popup_lines.append("<br><b style='color: #3182CE; cursor: pointer;'>Click marker again to view full details →</b>")
        popup_lines.append("</div>")

        popup_html = "<br>".join(popup_lines)

        folium.CircleMarker(
            location=[lat, lng],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name,
        ).add_to(m)

    map_data = st_folium(m, use_container_width=True, height=500)

    sel_count = len(st.session_state.selected_businesses)
    caption = f"Showing {len(data)} businesses  |  🟢 VOB  |  🔵 SDVOSB  |  ⭐ Active Heroes HQ"
    if using_custom:
        caption += f"  |  🏠 Search from {map_custom_zip}"
    if sel_count > 0:
        caption += f"  |  **{sel_count} selected for report**"
    st.caption(caption)

    # Handle marker click — show action panel
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        clicked_key = (round(clicked["lat"], 5), round(clicked["lng"], 5))
        if clicked_key in coord_to_id:
            clicked_id = coord_to_id[clicked_key]
            clicked_biz = next((b for b in data if b["id"] == clicked_id), None)
            if clicked_biz:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.markdown(f"**{clicked_biz['legal_business_name']}** — {clicked_biz.get('city', '')}, {clicked_biz.get('state', '')}")
                    if c2.button("View Details", key="map_detail"):
                        st.session_state.selected_business_id = clicked_id
                        st.switch_page("pages/_Business_Detail.py")
                    if clicked_id in st.session_state.selected_businesses:
                        if c3.button("Remove from Report", key="map_remove"):
                            st.session_state.selected_businesses.discard(clicked_id)
                            st.rerun()
                    else:
                        if c3.button("Add to Report", key="map_add"):
                            st.session_state.selected_businesses.add(clicked_id)
                            st.rerun()
else:
    st.info("No businesses with coordinates to display on map.")

st.divider()

# --- Charts (styled with navy palette) ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("By State")
    if stats.get("by_state"):
        df_state = pd.DataFrame(
            list(stats["by_state"].items()),
            columns=["State", "Count"],
        ).head(20)
        fig_state = px.bar(
            df_state, x="State", y="Count",
            title="Top States by Business Count",
        )
        style_chart(fig_state, height=350)
        st.plotly_chart(fig_state, use_container_width=True)

with col_right:
    st.subheader("Contact Completeness")
    if contact_stats["total"] > 0:
        t = contact_stats["total"]
        contact_df = pd.DataFrame([
            {"Field": "Phone", "Has Data": contact_stats["has_phone"], "Missing": t - contact_stats["has_phone"]},
            {"Field": "Email", "Has Data": contact_stats["has_email"], "Missing": t - contact_stats["has_email"]},
            {"Field": "Website", "Has Data": contact_stats["has_website"], "Missing": t - contact_stats["has_website"]},
        ])
        fig_contact = px.bar(
            contact_df, x="Field", y=["Has Data", "Missing"],
            title="Contact Data Coverage",
            barmode="stack",
            color_discrete_map={"Has Data": "#2F855A", "Missing": "#E2E8F0"},
        )
        style_chart(fig_contact, height=350)
        st.plotly_chart(fig_contact, use_container_width=True)

# Distance and source
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("By Distance from HQ")
    if stats.get("by_distance"):
        dist_df = pd.DataFrame(
            list(stats["by_distance"].items()),
            columns=["Bracket", "Count"],
        )
        fig_dist = px.bar(
            dist_df, x="Bracket", y="Count",
            title="Business Distribution by Distance",
        )
        style_chart(fig_dist, height=300)
        st.plotly_chart(fig_dist, use_container_width=True)
    # Show count of businesses without distance data
    total_with_dist = sum(stats.get("by_distance", {}).values())
    no_dist = stats["total"] - total_with_dist
    if no_dist > 0:
        st.caption(f"{no_dist:,} businesses without distance data")

with col_b:
    st.subheader("Data Sources")
    if stats.get("by_source"):
        source_df = pd.DataFrame(
            list(stats["by_source"].items()),
            columns=["Source", "Count"],
        )
        fig_source = px.pie(
            source_df, names="Source", values="Count",
            title="Records by Data Source",
        )
        style_chart(fig_source, height=300)
        st.plotly_chart(fig_source, use_container_width=True)

    # Data freshness
    fetch_statuses = get_all_fetch_status()
    if fetch_statuses:
        st.caption("Last updated:")
        from datetime import datetime
        for fs in fetch_statuses:
            completed = fs.get("completed_at", "")
            try:
                dt = datetime.fromisoformat(completed)
                days_ago = (datetime.now() - dt).days
                st.caption(f"  {fs['source']}: {days_ago}d ago")
            except (ValueError, TypeError):
                st.caption(f"  {fs['source']}: unknown")
