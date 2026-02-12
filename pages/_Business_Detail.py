import streamlit as st
from database import get_business_by_id, update_business_fields, update_business_notes, delete_business, create_tables
from branding import (
    inject_branding, sidebar_brand, render_tier_badges_html,
    render_tier_card_html, TRUST_TIERS, BRAND_BLUE,
    render_confidence_banner_html, render_source_badge_html,
    assign_confidence_grade, grade_badge_html,
    render_confidence_breakdown, GRADE_INFO, yelp_stars_html,
)

st.set_page_config(page_title="Business Detail | Veteran Business Directory", page_icon="🎖️", layout="wide")
create_tables()
inject_branding()

# Sidebar branding
with st.sidebar:
    sidebar_brand()

# Get business ID - session state first, then query params
biz_id = st.session_state.get("selected_business_id")
if not biz_id:
    params = st.query_params
    biz_id = params.get("id")

if not biz_id:
    st.warning("No business selected. Go to Search to find a business.")
    st.stop()

biz = get_business_by_id(int(biz_id))
if not biz:
    st.error("Business not found.")
    st.stop()

is_logged_in = st.session_state.get("logged_in", False)

# Back button
if st.button("← Back to Search"):
    st.switch_page("pages/1_🔍_Search.py")

# --- Header with Grade Badge ---
grade_info = assign_confidence_grade(biz)

col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown(
        f'<h1 style="margin-bottom:0.25rem;">{biz["legal_business_name"]}</h1>',
        unsafe_allow_html=True,
    )
    if biz.get("dba_name"):
        st.caption(f"DBA: {biz['dba_name']}")
with col_badge:
    bt = biz.get("business_type", "")
    badge_parts = []
    if "Service Disabled" in (bt or ""):
        badge_parts.append(
            '<span style="background:#2C5282; color:white; padding:4px 12px; '
            'border-radius:10px; font-size:0.82rem; font-weight:700;">SDVOSB</span>'
        )
    elif bt:
        badge_parts.append(
            '<span style="background:#2F855A; color:white; padding:4px 12px; '
            'border-radius:10px; font-size:0.82rem; font-weight:700;">VOB</span>'
        )
    badge_parts.append(grade_badge_html(grade_info["grade"]))
    st.markdown(" ".join(badge_parts), unsafe_allow_html=True)

    dist = biz.get("distance_miles")
    if dist is not None:
        st.metric("Distance", f"{dist} mi")

# --- Tier Badges Bar ---
st.markdown(render_tier_badges_html(biz), unsafe_allow_html=True)

# --- Confidence Banner ---
st.markdown(render_confidence_banner_html(biz), unsafe_allow_html=True)

# --- Yelp Rating (if available) ---
_yelp_html = yelp_stars_html(biz)
if _yelp_html:
    st.markdown(f"##### Yelp Rating")
    st.markdown(_yelp_html, unsafe_allow_html=True)

# --- Confidence Breakdown Grid (per field group) ---
st.markdown("##### Data Completeness by Category")
st.markdown(render_confidence_breakdown(biz), unsafe_allow_html=True)

# --- Tier Cards ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown(render_tier_card_html(biz, "official"), unsafe_allow_html=True)
    st.markdown(render_tier_card_html(biz, "third_party"), unsafe_allow_html=True)

with col_right:
    st.markdown(render_tier_card_html(biz, "verified"), unsafe_allow_html=True)
    st.markdown(render_tier_card_html(biz, "web_discovery"), unsafe_allow_html=True)

# --- Record Metadata ---
st.divider()
meta_cols = st.columns(4)
meta_cols[0].markdown(
    f'<div style="font-size:0.85rem;"><strong>Source:</strong> '
    f'{render_source_badge_html(biz.get("source"))}</div>',
    unsafe_allow_html=True,
)
meta_cols[1].caption(f"**Added:** {biz.get('date_added', '—')}")
meta_cols[2].caption(f"**Updated:** {biz.get('date_updated', '—')}")
if biz.get("notes"):
    meta_cols[3].caption(f"**Notes:** {biz['notes'][:80]}...")

# --- Admin Section (login required) ---
if is_logged_in:
    st.divider()

    # Notes
    st.subheader("Notes")
    notes = st.text_area("Notes", value=biz.get("notes") or "", key="notes_area")
    if st.button("Save Notes"):
        update_business_notes(int(biz_id), notes)
        st.success("Notes saved.")
        st.rerun()

    st.divider()

    # Edit
    with st.expander("Edit Business"):
        with st.form("edit_form"):
            st.markdown("**Contact Information**")
            ec1, ec2, ec3 = st.columns(3)
            phone = ec1.text_input("Phone", value=biz.get("phone") or "")
            email = ec2.text_input("Email", value=biz.get("email") or "")
            website = ec3.text_input("Website", value=biz.get("website") or "")

            st.markdown("**Business Details**")
            ed1, ed2 = st.columns(2)
            legal_name = ed1.text_input("Legal Business Name", value=biz.get("legal_business_name") or "")
            dba_name = ed2.text_input("DBA Name", value=biz.get("dba_name") or "")

            ed3, ed4 = st.columns(2)
            biz_type = ed3.selectbox(
                "Business Type",
                ["", "Veteran Owned Small Business", "Service Disabled Veteran Owned Small Business"],
                index=(
                    2 if biz.get("business_type") and "Service Disabled" in biz["business_type"]
                    else 1 if biz.get("business_type") else 0
                ),
            )
            branch = ed4.selectbox(
                "Service Branch",
                ["", "Army", "Navy", "Air Force", "Marine Corps", "Coast Guard", "Space Force", "National Guard"],
                index=(
                    ["", "Army", "Navy", "Air Force", "Marine Corps", "Coast Guard", "Space Force", "National Guard"]
                    .index(biz["service_branch"]) if biz.get("service_branch") in
                    ["Army", "Navy", "Air Force", "Marine Corps", "Coast Guard", "Space Force", "National Guard"]
                    else 0
                ),
            )

            st.markdown("**Address**")
            addr1 = st.text_input("Address Line 1", value=biz.get("physical_address_line1") or "")
            addr2 = st.text_input("Address Line 2", value=biz.get("physical_address_line2") or "")
            ea1, ea2, ea3 = st.columns([2, 1, 1])
            city = ea1.text_input("City", value=biz.get("city") or "")
            state_val = ea2.text_input("State", value=biz.get("state") or "", max_chars=2)
            zip_code = ea3.text_input("Zip Code", value=biz.get("zip_code") or "")

            edit_notes = st.text_area("Notes", value=biz.get("notes") or "", key="edit_notes")

            if st.form_submit_button("Save Changes"):
                fields = {
                    "legal_business_name": legal_name.strip(),
                    "dba_name": dba_name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "website": website.strip(),
                    "business_type": biz_type,
                    "service_branch": branch,
                    "physical_address_line1": addr1.strip(),
                    "physical_address_line2": addr2.strip(),
                    "city": city.strip(),
                    "state": state_val.strip().upper(),
                    "zip_code": zip_code.strip(),
                    "notes": edit_notes.strip(),
                }
                update_business_fields(int(biz_id), fields)
                st.success("Business updated.")
                st.rerun()

    # Delete
    st.markdown("---")
    if st.button("Delete Business", type="secondary"):
        st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        st.warning("Are you sure you want to remove this business from the database?")
        dc1, dc2 = st.columns(2)
        if dc1.button("Yes, delete"):
            delete_business(int(biz_id))
            st.session_state.pop("confirm_delete", None)
            st.session_state.pop("selected_business_id", None)
            st.success("Business removed.")
            st.switch_page("pages/1_🔍_Search.py")
        if dc2.button("Cancel"):
            st.session_state.pop("confirm_delete", None)
            st.rerun()
