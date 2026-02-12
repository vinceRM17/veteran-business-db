import streamlit as st
import tempfile
import os
from database import import_from_csv, create_tables

st.set_page_config(page_title="Import CSV | Veteran Business Directory", page_icon="🎖️", layout="wide")
create_tables()

# Sidebar branding
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
        <h2 style='color: #2e86ab; margin-bottom: 0;'>🎖️ Veteran Business Directory</h2>
        <p style='color: #6c757d; font-size: 0.85rem;'>Active Heroes &bull; Shepherdsville, KY</p>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Dashboard sidebar to access this page.")
    st.stop()

st.title("📥 Import CSV")

st.markdown("""
Upload a CSV file to import veteran-owned businesses into the database.

**Expected columns** (flexible naming):
- `legal_business_name` or `Business Name` or `Name`
- `city` / `City`
- `state` / `State`
- `zip_code` / `Zip` / `Zip Code`
- `phone` / `Phone`
- `email` / `Email`
- `website` / `Website` / `URL`
- `business_type` / `Type`
- `dba_name` / `DBA`
- `physical_address_line1` / `Address`
- `naics_codes` / `NAICS`
- `notes` / `Notes`
""")

source = st.text_input("Source Label", value="Manual Import", help="Tag these records with a source name")

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded and st.button("Import"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    try:
        count = import_from_csv(tmp_path, source)
        st.success(f"Successfully imported {count} businesses.")
    except Exception as e:
        st.error(f"Import error: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
