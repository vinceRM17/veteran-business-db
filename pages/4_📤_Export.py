import streamlit as st
import pandas as pd
from database import export_search_to_csv, create_tables
from branding import inject_branding, sidebar_brand, tier_summary

st.set_page_config(page_title="Export | Veteran Business Directory", page_icon="🎖️", layout="wide")
create_tables()
inject_branding()

with st.sidebar:
    sidebar_brand()

st.title("📤 Export Data")

st.markdown("Download all businesses as a CSV file with data source tier info.")

if st.button("Generate CSV"):
    rows = export_search_to_csv()
    for row in rows:
        row["data_sources"] = tier_summary(row)

    df = pd.DataFrame(rows)
    export_cols = [
        c for c in [
            "legal_business_name", "dba_name", "business_type",
            "owner_name", "service_branch", "linkedin_url",
            "physical_address_line1", "city", "state", "zip_code",
            "phone", "email", "website",
            "naics_codes", "naics_descriptions",
            "distance_miles", "source", "data_sources", "notes",
        ] if c in df.columns
    ]
    csv_data = df[export_cols].to_csv(index=False)

    st.download_button(
        label=f"Download CSV ({len(rows)} businesses)",
        data=csv_data,
        file_name="veteran_businesses_export.csv",
        mime="text/csv",
    )
