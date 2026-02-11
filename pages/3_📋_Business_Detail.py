import streamlit as st
from database import get_business_by_id, update_business_fields, update_business_notes, delete_business, create_tables

st.set_page_config(page_title="Business Detail - Veteran Business DB", layout="wide")
create_tables()

# Get business ID from query params
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

# Header
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title(biz["legal_business_name"])
    if biz.get("dba_name"):
        st.caption(f"DBA: {biz['dba_name']}")
with col_badge:
    bt = biz.get("business_type", "")
    if "Service Disabled" in (bt or ""):
        st.markdown(":blue[**SDVOSB**]")
    elif bt:
        st.markdown(":green[**VOB**]")

st.divider()

# Contact info
st.subheader("Contact Information")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Phone**")
    if biz.get("phone"):
        st.markdown(biz["phone"])
    else:
        st.caption("Not listed")
with c2:
    st.markdown("**Email**")
    if biz.get("email"):
        st.markdown(biz["email"])
    else:
        st.caption("Not listed")
with c3:
    st.markdown("**Website**")
    if biz.get("website"):
        st.markdown(f"[{biz['website']}]({biz['website']})")
    else:
        st.caption("Not listed")

st.divider()

# Location and details
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Location")
    addr = biz.get("physical_address_line1") or ""
    if biz.get("physical_address_line2"):
        addr += f"\n{biz['physical_address_line2']}"
    city_state = f"{biz.get('city', '')}, {biz.get('state', '')} {biz.get('zip_code', '')}"
    st.text(addr)
    st.text(city_state)

    dist = biz.get("distance_miles")
    if dist is not None:
        st.metric("Distance from Active Heroes", f"{dist} mi")

with col_right:
    st.subheader("Registration Details")
    if biz.get("uei"):
        st.text(f"UEI: {biz['uei']}")
    if biz.get("cage_code"):
        st.text(f"CAGE Code: {biz['cage_code']}")
    if biz.get("registration_status"):
        status = "Active" if biz["registration_status"] == "A" else biz["registration_status"]
        st.text(f"Status: {status}")
    if biz.get("registration_expiration"):
        st.text(f"Expires: {biz['registration_expiration']}")
    if biz.get("entity_start_date"):
        st.text(f"Entity Start: {biz['entity_start_date']}")
    if biz.get("service_branch"):
        st.text(f"Service Branch: {biz['service_branch']}")
    st.text(f"Source: {biz.get('source') or 'Unknown'}")

# NAICS
if biz.get("naics_codes") or biz.get("naics_descriptions"):
    st.divider()
    st.subheader("Industry / NAICS Codes")
    if biz.get("naics_descriptions"):
        st.text(biz["naics_descriptions"])
    if biz.get("naics_codes"):
        st.caption(f"NAICS: {biz['naics_codes']}")

# Notes (admin only)
if is_logged_in:
    st.divider()
    st.subheader("Notes")
    notes = st.text_area("Notes", value=biz.get("notes") or "", key="notes_area")
    if st.button("Save Notes"):
        update_business_notes(int(biz_id), notes)
        st.success("Notes saved.")
        st.rerun()

# Edit section (admin only)
if is_logged_in:
    st.divider()
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
            state = ea2.text_input("State", value=biz.get("state") or "", max_chars=2)
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
                    "state": state.strip().upper(),
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
            st.success("Business removed.")
            st.switch_page("pages/1_🔍_Search.py")
        if dc2.button("Cancel"):
            st.session_state.pop("confirm_delete", None)
            st.rerun()
