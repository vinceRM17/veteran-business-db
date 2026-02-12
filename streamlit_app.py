import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from database import create_tables, get_stats, get_contact_stats, get_map_data, get_all_businesses_with_coords, get_all_fetch_status
from geo import zip_to_coords, filter_by_custom_radius
from config import ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON

st.set_page_config(
    page_title="Veteran Business Directory | Active Heroes",
    page_icon="🎖️",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; color: #5a6c7d; }
    .hero-header {
        background: linear-gradient(135deg, #2e86ab 0%, #1b4965 100%);
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
    .sidebar-brand h2 { color: #2e86ab; margin-bottom: 0; }
    .sidebar-brand p { color: #7a8a99; font-size: 0.85rem; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e8e0d4;
        border-radius: 0.75rem;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

create_tables()

# --- Auth state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Selection state (shared across pages) ---
if "selected_businesses" not in st.session_state:
    st.session_state.selected_businesses = set()

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div class='sidebar-brand' style='text-align:center; padding: 0.5rem 0 1rem 0;'>
        <h2>🎖️ Veteran Business Directory</h2>
        <p>Active Heroes &bull; Shepherdsville, KY</p>
    </div>
    """, unsafe_allow_html=True)
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

# --- Dashboard Header ---
st.markdown("""
<div class="hero-header">
    <h1>Veteran Business Directory</h1>
    <p>Connecting veteran-owned businesses near Active Heroes, Shepherdsville KY</p>
</div>
""", unsafe_allow_html=True)

stats = get_stats()
contact_stats = get_contact_stats()

if stats["total"] == 0:
    st.warning("Database is empty. Use the **Fetch Data** or **Import CSV** page to load businesses.")
    st.stop()

# --- Stats ---
vob_count = 0
sdvosb_count = 0
for t, c in stats.get("by_type", {}).items():
    if "Service Disabled" in (t or ""):
        sdvosb_count += c
    else:
        vob_count += c

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Businesses", stats["total"])
col2.metric("VOB", vob_count)
col3.metric("SDVOSB", sdvosb_count)

if contact_stats["total"] > 0:
    pct = round(contact_stats["has_phone"] / contact_stats["total"] * 100)
    col4.metric("Have Phone", f"{pct}%")

st.markdown("")  # spacer

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
                f"<div style='font-family: sans-serif;'>"
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
            "<div style='font-family: sans-serif;'>"
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
        bt = biz.get("business_type", "")
        is_sdvosb = "Service Disabled" in bt
        color = "#2e86ab" if is_sdvosb else "#27ae60"
        type_label = "SDVOSB" if is_sdvosb else "VOB"

        name = biz["legal_business_name"]
        city_state = f"{biz.get('city', '')}, {biz.get('state', '')}"
        dist = biz.get(distance_key)
        lat, lng = biz["latitude"], biz["longitude"]

        # Store mapping for click detection
        coord_to_id[(round(lat, 5), round(lng, 5))] = biz["id"]

        popup_lines = [
            "<div style='font-family: sans-serif; line-height: 1.5;'>",
            f"<b style='font-size: 14px;'>{name}</b>",
        ]
        if biz.get("dba_name"):
            popup_lines.append(f"<i style='color: #7a8a99;'>DBA: {biz['dba_name']}</i>")
        popup_lines.append(f"<span style='color: #5a6c7d;'>{city_state}</span>")
        popup_lines.append(f"<span style='background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;'>{type_label}</span>")
        if dist is not None:
            popup_lines.append(f"<span style='color: #7a8a99;'>{dist} mi from {distance_from_label}</span>")
        if biz.get("phone"):
            popup_lines.append(f"📞 {biz['phone']}")
        if biz.get("email"):
            popup_lines.append(f"✉️ {biz['email']}")
        if biz.get("website"):
            popup_lines.append(f'🌐 <a href="{biz["website"]}" target="_blank" style="color: #2e86ab;">{biz["website"]}</a>')
        popup_lines.append("<br><b style='color: #2e86ab; cursor: pointer;'>Click marker again to view full details →</b>")
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

# --- Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("By State")
    if stats.get("by_state"):
        df_state = pd.DataFrame(
            list(stats["by_state"].items()),
            columns=["State", "Count"],
        )
        st.bar_chart(df_state.set_index("State"))

with col_right:
    st.subheader("Contact Completeness")
    if contact_stats["total"] > 0:
        t = contact_stats["total"]
        st.progress(contact_stats["has_phone"] / t, text=f"Phone: {contact_stats['has_phone']}/{t}")
        st.progress(contact_stats["has_email"] / t, text=f"Email: {contact_stats['has_email']}/{t}")
        st.progress(contact_stats["has_website"] / t, text=f"Website: {contact_stats['has_website']}/{t}")

# Distance and source
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("By Distance from HQ")
    if stats.get("by_distance"):
        for bracket, count in stats["by_distance"].items():
            st.text(f"{bracket}: {count}")
    # Show count of businesses without distance data
    total_with_dist = sum(stats.get("by_distance", {}).values())
    no_dist = stats["total"] - total_with_dist
    if no_dist > 0:
        st.caption(f"{no_dist} businesses without distance data")

with col_b:
    st.subheader("Data Sources")
    if stats.get("by_source"):
        for source, count in stats["by_source"].items():
            st.text(f"{source}: {count}")

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
