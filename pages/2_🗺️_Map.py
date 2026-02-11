import streamlit as st
import pandas as pd
from database import get_map_data, create_tables
from config import ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON

st.set_page_config(page_title="Map - Veteran Business DB", layout="wide")
create_tables()

st.title("🗺️ Map View")

dist_filter = st.select_slider(
    "Max Distance",
    options=[25, 50, 75, 100],
    value=100,
    format_func=lambda x: f"{x} miles",
)

data = get_map_data(max_distance=dist_filter)

if not data:
    st.warning("No businesses with coordinates to display.")
    st.stop()

st.caption(f"{len(data)} businesses on map")

# Build dataframe for the map
rows = []
# Add Active Heroes marker
rows.append({
    "lat": ACTIVE_HEROES_LAT,
    "lon": ACTIVE_HEROES_LON,
    "name": "Active Heroes HQ",
    "size": 800,
    "color": "#c59a3e",
})

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

st.caption("🟢 VOB  |  🔵 SDVOSB  |  🟡 Active Heroes")
