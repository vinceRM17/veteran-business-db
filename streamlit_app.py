import streamlit as st
import pandas as pd
from database import create_tables, get_stats, get_contact_stats, get_map_data
from config import ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON

st.set_page_config(
    page_title="Veteran Business DB - Active Heroes",
    page_icon="🛡️",
    layout="wide",
)

# Custom CSS for branding and card styling
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .hero-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }
    .hero-header h1 { color: #c59a3e !important; margin-bottom: 0.25rem; }
    .hero-header p { color: #adb5bd; margin: 0; }
</style>
""", unsafe_allow_html=True)

create_tables()

# --- Auth state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
        <h2 style='color: #c59a3e; margin-bottom: 0;'>🛡️ Veteran Business DB</h2>
        <p style='color: #6c757d; font-size: 0.85rem;'>Active Heroes &bull; Shepherdsville, KY</p>
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

# --- Dashboard Header ---
st.markdown("""
<div class="hero-header">
    <h1>Dashboard</h1>
    <p>Veteran-owned businesses near Active Heroes, Shepherdsville KY</p>
</div>
""", unsafe_allow_html=True)

stats = get_stats()
contact_stats = get_contact_stats()

if stats["total"] == 0:
    st.warning("Database is empty. Use the **Fetch Data** or **Import CSV** page to load businesses.")
    st.stop()

# --- Map Hero Section ---
st.subheader("🗺️ Business Locations")
dist_filter = st.select_slider(
    "Distance Filter",
    options=[25, 50, 75, 100],
    value=100,
    format_func=lambda x: f"{x} miles",
)

data = get_map_data(max_distance=dist_filter)

if data:
    rows = [{
        "lat": ACTIVE_HEROES_LAT,
        "lon": ACTIVE_HEROES_LON,
        "name": "Active Heroes HQ",
        "size": 800,
        "color": "#c59a3e",
    }]
    for biz in data:
        bt = biz.get("business_type", "")
        color = "#1565c0" if "Service Disabled" in bt else "#2e7d32"
        rows.append({
            "lat": biz["latitude"],
            "lon": biz["longitude"],
            "name": biz["legal_business_name"],
            "size": 200,
            "color": color,
        })
    df = pd.DataFrame(rows)
    st.map(df, latitude="lat", longitude="lon", size="size", color="color")
    st.caption(f"Showing {len(data)} businesses  |  🟢 VOB  |  🔵 SDVOSB  |  🟡 Active Heroes HQ")
else:
    st.info("No businesses with coordinates to display on map.")

st.divider()

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
    st.subheader("By Distance")
    if stats.get("by_distance"):
        for bracket, count in stats["by_distance"].items():
            st.text(f"{bracket}: {count}")

with col_b:
    st.subheader("By Source")
    if stats.get("by_source"):
        for source, count in stats["by_source"].items():
            st.text(f"{source}: {count}")
