import streamlit as st
from database import search_businesses, get_all_states, get_all_business_types, get_all_businesses_with_coords, create_tables
from geo import zip_to_coords, filter_by_custom_radius

st.set_page_config(page_title="Search | Veteran Business Directory", page_icon="🎖️", layout="wide")
create_tables()

# Sidebar branding
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
        <h2 style='color: #2e86ab; margin-bottom: 0;'>🎖️ Veteran Business Directory</h2>
        <p style='color: #6c757d; font-size: 0.85rem;'>Active Heroes &bull; Shepherdsville, KY</p>
    </div>
    """, unsafe_allow_html=True)

# --- Selection state (shared across pages) ---
if "selected_businesses" not in st.session_state:
    st.session_state.selected_businesses = set()


def _toggle_selection(biz_id):
    """Callback: runs before rerun so count is accurate."""
    if st.session_state.get(f"sel_{biz_id}"):
        st.session_state.selected_businesses.add(biz_id)
    else:
        st.session_state.selected_businesses.discard(biz_id)


st.title("🔍 Search Businesses")

# Selection bar
sel_count = len(st.session_state.selected_businesses)
if sel_count > 0:
    bar_cols = st.columns([3, 1, 1])
    bar_cols[0].markdown(f"**{sel_count} business{'es' if sel_count != 1 else ''} selected**")
    if bar_cols[1].button("View Report", key="search_view_report"):
        st.switch_page("pages/5_📊_Report.py")
    if bar_cols[2].button("Clear Selection", key="search_clear_sel"):
        st.session_state.selected_businesses = set()
        st.rerun()

# Filters
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
with col1:
    query = st.text_input("Search", placeholder="Business name, industry, city...")
with col2:
    states = [""] + get_all_states()
    state = st.selectbox("State", states, format_func=lambda x: "All States" if x == "" else x)
with col3:
    types = [""] + get_all_business_types()
    biz_type = st.selectbox("Type", types, format_func=lambda x: "All Types" if x == "" else (
        "SDVOSB" if "Service Disabled" in x else "VOB" if x else x
    ))
with col4:
    dist_options = {"100 miles": 100, "25 miles": 25, "50 miles": 50, "75 miles": 75, "Any Distance": None}
    dist_label = st.selectbox("Distance from HQ", list(dist_options.keys()))
    max_distance = dist_options[dist_label]

# --- Custom location toggle ---
def _on_custom_toggle_change():
    st.session_state.search_page = 1
    if not st.session_state.get("custom_location_search"):
        st.session_state.pop("report_custom_origin", None)

custom_location = st.toggle(
    "Search from a different location",
    key="custom_location_search",
    on_change=_on_custom_toggle_change,
)

custom_origin_lat = None
custom_origin_lon = None
custom_zip = None

if custom_location:
    cl_col1, cl_col2 = st.columns([1, 2])
    with cl_col1:
        custom_zip = st.text_input("Zip Code", max_chars=5, placeholder="e.g. 40202")
    with cl_col2:
        custom_radius = st.slider("Radius (miles)", min_value=10, max_value=250, value=50, step=5)

    if custom_zip and len(custom_zip) == 5 and custom_zip.isdigit():
        custom_origin_lat, custom_origin_lon = zip_to_coords(custom_zip)
        if custom_origin_lat is None:
            st.warning(f"Could not find coordinates for zip code {custom_zip}. Check the zip and try again.")
    elif custom_zip:
        st.warning("Please enter a valid 5-digit zip code.")

# Pagination
if "search_page" not in st.session_state:
    st.session_state.search_page = 1

PER_PAGE = 25

# --- Branching search logic ---
if custom_location and custom_origin_lat is not None:
    # Custom location mode: fetch all, filter in Python
    all_businesses = get_all_businesses_with_coords()

    # Apply text/state/type filters in Python
    filtered = all_businesses
    if query:
        q_lower = query.lower()
        filtered = [b for b in filtered if
                    q_lower in (b.get("legal_business_name") or "").lower() or
                    q_lower in (b.get("dba_name") or "").lower() or
                    q_lower in (b.get("naics_descriptions") or "").lower() or
                    q_lower in (b.get("city") or "").lower()]
    if state:
        filtered = [b for b in filtered if b.get("state") == state]
    if biz_type:
        filtered = [b for b in filtered if b.get("business_type") == biz_type]

    # Apply custom radius filter
    filtered = filter_by_custom_radius(custom_origin_lat, custom_origin_lon, filtered, custom_radius)

    total = len(filtered)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(st.session_state.search_page, total_pages)
    offset = (page - 1) * PER_PAGE
    page_businesses = filtered[offset:offset + PER_PAGE]

    distance_key = "custom_distance_miles"
    distance_label = f"mi from {custom_zip}"

    # Store custom origin for Report page
    st.session_state.report_custom_origin = {
        "zip": custom_zip,
        "lat": custom_origin_lat,
        "lon": custom_origin_lon,
    }

    results = {
        "businesses": page_businesses,
        "total": total,
        "page": page,
        "per_page": PER_PAGE,
        "total_pages": total_pages,
    }
else:
    # Default HQ-based mode
    results = search_businesses(
        query=query, state=state, business_type=biz_type,
        max_distance=max_distance, page=st.session_state.search_page,
    )
    distance_key = "distance_miles"
    distance_label = "mi"

    # Clear custom origin when toggle is off
    if not custom_location:
        st.session_state.pop("report_custom_origin", None)

st.caption(f"{results['total']} businesses found")

# Results
for biz in results["businesses"]:
    bt = biz.get("business_type", "")
    is_sdvosb = "Service Disabled" in bt
    border_color = "#2e86ab" if is_sdvosb else "#27ae60" if bt else "#dee2e6"

    with st.container(border=True):
        # Colored accent bar
        st.markdown(
            f'<div style="border-top: 3px solid {border_color}; margin: -1rem -1rem 0.75rem -1rem;"></div>',
            unsafe_allow_html=True,
        )

        cols = st.columns([0.3, 0.5, 3, 2, 1, 1.5])

        # Checkbox for selection (on_change fires before rerun so count stays accurate)
        is_selected = biz["id"] in st.session_state.selected_businesses
        cols[0].checkbox(
            "", value=is_selected, key=f"sel_{biz['id']}",
            label_visibility="collapsed",
            on_change=_toggle_selection, args=(biz["id"],),
        )

        dist = biz.get(distance_key)
        cols[1].markdown(f"**{dist} {distance_label}**" if dist is not None else "—")

        # Clickable business name using button + session state
        name = biz["legal_business_name"]
        if cols[2].button(name, key=f"biz_{biz['id']}"):
            st.session_state.selected_business_id = biz["id"]
            st.switch_page("pages/_Business_Detail.py")
        if biz.get("dba_name"):
            cols[2].caption(f"DBA: {biz['dba_name']}")

        location = f"{biz.get('city', '')}, {biz.get('state', '')} {biz.get('zip_code', '')}"
        cols[3].text(location)

        if is_sdvosb:
            cols[4].markdown(":blue[**SDVOSB**]")
        elif bt:
            cols[4].markdown(":green[**VOB**]")

        # Contact info - show phone if available
        contact_parts = []
        if biz.get("phone"):
            contact_parts.append(f"📞 {biz['phone']}")
        if biz.get("email"):
            contact_parts.append("✉️")
        if biz.get("website"):
            contact_parts.append("🌐")
        cols[5].markdown(" ".join(contact_parts) if contact_parts else "⚠️ No contact")

# Pagination controls
if results["total_pages"] > 1:
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Previous", disabled=st.session_state.search_page <= 1):
            st.session_state.search_page -= 1
            st.rerun()
    with col_info:
        st.caption(f"Page {results['page']} of {results['total_pages']}")
    with col_next:
        if st.button("Next →", disabled=st.session_state.search_page >= results["total_pages"]):
            st.session_state.search_page += 1
            st.rerun()
