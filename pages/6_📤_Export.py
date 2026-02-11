import streamlit as st
from database import export_to_csv, create_tables

st.set_page_config(page_title="Export - Veteran Business DB", layout="wide")
create_tables()

st.title("📤 Export Data")

st.markdown("Download all businesses as a CSV file.")

if st.button("Generate CSV"):
    export_path = "/tmp/veteran_businesses_export.csv"
    count = export_to_csv(export_path)

    with open(export_path, "rb") as f:
        st.download_button(
            label=f"Download CSV ({count} businesses)",
            data=f,
            file_name="veteran_businesses_export.csv",
            mime="text/csv",
        )
