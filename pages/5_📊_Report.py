import streamlit as st
import pandas as pd
import io
from database import get_businesses_by_ids, create_tables
from geo import compute_distances_from_point
from branding import inject_branding, sidebar_brand, BRAND_BLUE

st.set_page_config(page_title="Report | Veteran Business Directory", page_icon="🎖️", layout="wide")
create_tables()
inject_branding()

with st.sidebar:
    sidebar_brand()

# Selection state
if "selected_businesses" not in st.session_state:
    st.session_state.selected_businesses = set()

st.title("Selected Business Report")

selected_ids = st.session_state.selected_businesses

if not selected_ids:
    st.info("No businesses selected. Use the **Search** page or **Dashboard map** to select businesses for your report.")
    st.stop()

businesses = get_businesses_by_ids(selected_ids)

if not businesses:
    st.warning("Selected businesses not found in database.")
    st.stop()

# --- Detect custom origin ---
custom_origin = st.session_state.get("report_custom_origin")
if custom_origin:
    businesses = compute_distances_from_point(
        custom_origin["lat"], custom_origin["lon"], businesses
    )
    distance_key = "custom_distance_miles"
    distance_col_label = f"Distance from {custom_origin['zip']} (mi)"
    st.info(f"Distances shown from custom location: zip code **{custom_origin['zip']}**. "
            "Turn off the custom location toggle on the Search page to revert to HQ distances.")
else:
    distance_key = "distance_miles"
    distance_col_label = "Distance from HQ (mi)"

# Action bar
action_cols = st.columns([2, 1, 1, 1])
action_cols[0].markdown(f"**{len(businesses)} business{'es' if len(businesses) != 1 else ''} in report**")

# CSV export
report_columns = [
    "legal_business_name", "dba_name", "business_type",
    "physical_address_line1", "city", "state", "zip_code",
    "phone", "email", "website", "naics_codes",
    distance_key, "registration_status", "source",
]
display_headers = [
    "Name", "DBA", "Type", "Address", "City", "State", "Zip",
    "Phone", "Email", "Website", "NAICS",
    distance_col_label, "Registration Status", "Source",
]

df = pd.DataFrame(businesses)[report_columns]
df.columns = display_headers

csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)

action_cols[1].download_button(
    label="Export CSV",
    data=csv_buffer.getvalue(),
    file_name="veteran_business_report.csv",
    mime="text/csv",
)

# Print button
if action_cols[2].button("Print Report"):
    # Build print-friendly HTML
    rows_html = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td style='padding:6px 8px;border:1px solid #dee2e6;font-size:12px;'>{v if pd.notna(v) else ''}</td>" for v in row)
        rows_html += f"<tr>{cells}</tr>"
    headers_html = "".join(f"<th style='padding:6px 8px;border:1px solid #dee2e6;background:#2ea3f2;color:white;font-size:12px;'>{h}</th>" for h in display_headers)

    print_html = f"""
    <html><head><title>Veteran Business Report</title></head>
    <body style="font-family:Arial,sans-serif;">
    <h2>Veteran Business Report - Active Heroes</h2>
    <p>{len(businesses)} businesses &bull; Generated {pd.Timestamp.now().strftime('%B %d, %Y')}</p>
    <table style="border-collapse:collapse;width:100%;">
    <thead><tr>{headers_html}</tr></thead>
    <tbody>{rows_html}</tbody>
    </table></body></html>
    """
    # Open print dialog via JS
    st.components.v1.html(
        f"""<script>
        var w = window.open('', '_blank');
        w.document.write(`{print_html.replace(chr(96), "'")}`);
        w.document.close();
        w.print();
        </script>""",
        height=0,
    )

# Clear all
if action_cols[3].button("Clear All"):
    st.session_state.selected_businesses = set()
    st.rerun()

st.divider()

# Full-detail table
for biz in businesses:
    bt = biz.get("business_type") or ""
    is_sdvosb = "Service Disabled" in bt
    border_color = BRAND_BLUE if is_sdvosb else "#27ae60" if bt else "#dee2e6"

    with st.container(border=True):
        st.markdown(
            f'<div style="border-top: 3px solid {border_color}; margin: -1rem -1rem 0.75rem -1rem;"></div>',
            unsafe_allow_html=True,
        )

        top_cols = st.columns([4, 1])
        name = biz["legal_business_name"]
        dba = f" (DBA: {biz['dba_name']})" if biz.get("dba_name") else ""
        type_label = ":blue[**SDVOSB**]" if is_sdvosb else ":green[**VOB**]" if bt else ""
        dist = biz.get(distance_key)
        dist_text = f" — {dist} mi" if dist is not None else ""

        top_cols[0].markdown(f"### {name}{dba} {type_label}{dist_text}")

        if top_cols[1].button("Remove", key=f"rm_{biz['id']}"):
            st.session_state.selected_businesses.discard(biz["id"])
            st.rerun()

        # Detail grid
        c1, c2, c3 = st.columns(3)
        address = biz.get("physical_address_line1", "")
        city_state_zip = f"{biz.get('city', '')}, {biz.get('state', '')} {biz.get('zip_code', '')}"
        c1.markdown(f"**Address:** {address}")
        c1.markdown(f"{city_state_zip}")

        c2.markdown(f"**Phone:** {biz.get('phone') or 'N/A'}")
        c2.markdown(f"**Email:** {biz.get('email') or 'N/A'}")
        c2.markdown(f"**Website:** {biz.get('website') or 'N/A'}")

        c3.markdown(f"**NAICS:** {biz.get('naics_codes') or 'N/A'}")
        c3.markdown(f"**Status:** {biz.get('registration_status') or 'N/A'}")
        c3.markdown(f"**Source:** {biz.get('source') or 'N/A'}")

# Also show as a data table for quick scanning
with st.expander("View as table"):
    st.dataframe(df, use_container_width=True, hide_index=True)
