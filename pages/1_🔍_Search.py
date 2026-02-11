import streamlit as st
from database import search_businesses, get_all_states, get_all_business_types, create_tables

st.set_page_config(page_title="Search - Veteran Business DB", layout="wide")
create_tables()

# Sidebar branding
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
        <h2 style='color: #c59a3e; margin-bottom: 0;'>🛡️ Veteran Business DB</h2>
        <p style='color: #6c757d; font-size: 0.85rem;'>Active Heroes &bull; Shepherdsville, KY</p>
    </div>
    """, unsafe_allow_html=True)

st.title("🔍 Search Businesses")

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
    dist_options = {"Any Distance": None, "25 miles": 25, "50 miles": 50, "75 miles": 75, "100 miles": 100}
    dist_label = st.selectbox("Distance", list(dist_options.keys()))
    max_distance = dist_options[dist_label]

# Pagination
if "search_page" not in st.session_state:
    st.session_state.search_page = 1

results = search_businesses(
    query=query, state=state, business_type=biz_type,
    max_distance=max_distance, page=st.session_state.search_page,
)

st.caption(f"{results['total']} businesses found")

# Results
for biz in results["businesses"]:
    bt = biz.get("business_type", "")
    is_sdvosb = "Service Disabled" in bt
    border_color = "#1565c0" if is_sdvosb else "#2e7d32" if bt else "#dee2e6"

    with st.container(border=True):
        # Colored accent bar
        st.markdown(
            f'<div style="border-top: 3px solid {border_color}; margin: -1rem -1rem 0.75rem -1rem;"></div>',
            unsafe_allow_html=True,
        )

        cols = st.columns([0.5, 3, 2, 1, 1.5])

        dist = biz.get("distance_miles")
        cols[0].markdown(f"**{dist} mi**" if dist is not None else "—")

        # Clickable business name using button + session state
        name = biz["legal_business_name"]
        if cols[1].button(name, key=f"biz_{biz['id']}"):
            st.session_state.selected_business_id = biz["id"]
            st.switch_page("pages/2_📋_Business_Detail.py")
        if biz.get("dba_name"):
            cols[1].caption(f"DBA: {biz['dba_name']}")

        location = f"{biz.get('city', '')}, {biz.get('state', '')} {biz.get('zip_code', '')}"
        cols[2].text(location)

        if is_sdvosb:
            cols[3].markdown(":blue[**SDVOSB**]")
        elif bt:
            cols[3].markdown(":green[**VOB**]")

        # Contact info - show phone if available
        contact_parts = []
        if biz.get("phone"):
            contact_parts.append(f"📞 {biz['phone']}")
        if biz.get("email"):
            contact_parts.append("✉️")
        if biz.get("website"):
            contact_parts.append("🌐")
        cols[4].markdown(" ".join(contact_parts) if contact_parts else "⚠️ No contact")

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
