import streamlit as st
from database import create_tables
from config import SAM_GOV_API_KEY

st.set_page_config(page_title="Fetch Data | Veteran Business Directory", page_icon="🎖️", layout="wide")
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

st.title("🔄 Fetch Data from SAM.gov")

if SAM_GOV_API_KEY:
    st.success("SAM.gov API key is configured.")
else:
    st.error("No SAM.gov API key found in config.py. Get a free key at https://sam.gov/profile/details")
    st.stop()

st.markdown("""
This will query the SAM.gov Entity Management API for veteran-owned businesses
in KY, IN, OH, TN, and WV, then filter to businesses within 100 miles of
Active Heroes (Shepherdsville, KY).

**Note:** The free API tier has daily rate limits. If you get throttled, try again tomorrow.
""")

if st.button("Fetch from SAM.gov"):
    with st.spinner("Fetching data from SAM.gov... This may take a few minutes."):
        try:
            from sam_gov import fetch_veteran_businesses
            total = fetch_veteran_businesses()
            st.success(f"Fetched and saved {total} veteran-owned businesses.")
        except Exception as e:
            st.error(f"Fetch error: {e}")

st.divider()
st.subheader("Other Data Sources")
st.markdown("""
- [VeteranOwnedBusiness.com](https://www.veteranownedbusiness.com) - Directory with advanced search
- [VetBiz Portal](https://vetbiz.va.gov) - VA verification database
- [Kentucky SBC](https://app.sbc.ky.gov) - Kentucky small business directory
""")
