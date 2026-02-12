import streamlit as st
from datetime import datetime, timedelta

from database import create_tables, get_all_fetch_status, get_last_fetch, get_stats, get_contact_stats
from config import SAM_GOV_API_KEY, SOURCE_SAM_GOV, SOURCE_USASPENDING

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

st.title("🔄 Fetch Data")
st.caption("Pull veteran-owned business data from federal databases nationwide")

# --- Source status cards ---
st.subheader("Data Sources")

STALE_DAYS = 30


def _render_source_card(source_name, description, last_fetch):
    """Render a status card for a data source."""
    with st.container(border=True):
        col_info, col_status = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{source_name}**")
            st.caption(description)
        with col_status:
            if last_fetch:
                completed = last_fetch.get("completed_at", "")
                try:
                    fetch_dt = datetime.fromisoformat(completed)
                    days_ago = (datetime.now() - fetch_dt).days
                    if days_ago > STALE_DAYS:
                        st.warning(f"{days_ago}d ago")
                    else:
                        st.success(f"{days_ago}d ago")
                    st.caption(
                        f"{last_fetch.get('records_fetched', 0)} fetched | "
                        f"{last_fetch.get('records_new', 0)} new | "
                        f"{last_fetch.get('records_updated', 0)} updated"
                    )
                except (ValueError, TypeError):
                    st.info("Unknown")
            else:
                st.info("Never fetched")


sam_last = get_last_fetch(SOURCE_SAM_GOV)
usa_last = get_last_fetch(SOURCE_USASPENDING)

_render_source_card(
    "SAM.gov",
    "Entity Management API — veteran-owned business registrations from all 50 states + territories",
    sam_last,
)
_render_source_card(
    "USAspending.gov",
    "Federal contract awards to veteran-owned businesses (last 5 years)",
    usa_last,
)

st.divider()

# --- SAM.gov Fetch ---
st.subheader("SAM.gov — Federal Business Registrations")

if not SAM_GOV_API_KEY:
    st.error("No SAM.gov API key found in config.py. Get a free key at https://sam.gov/profile/details")
else:
    st.success("API key configured")

    sam_col1, sam_col2 = st.columns(2)
    with sam_col1:
        if st.button("Fetch All States", key="sam_fetch_all", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def sam_callback(msg, pct):
                status_text.text(msg)
                if pct is not None:
                    progress_bar.progress(min(pct, 1.0))

            try:
                from sam_gov import fetch_veteran_businesses
                result = fetch_veteran_businesses(callback=sam_callback)
                progress_bar.progress(1.0)
                st.success(
                    f"SAM.gov fetch complete! "
                    f"Fetched: {result['total_fetched']} | "
                    f"New: {result['new']} | "
                    f"Updated: {result['updated']} | "
                    f"States: {len(result['states_completed'])}"
                )
            except Exception as e:
                st.error(f"SAM.gov fetch error: {e}")

    with sam_col2:
        if sam_last and st.button("Resume Interrupted Fetch", key="sam_resume"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def sam_resume_cb(msg, pct):
                status_text.text(msg)
                if pct is not None:
                    progress_bar.progress(min(pct, 1.0))

            try:
                from sam_gov import fetch_veteran_businesses
                result = fetch_veteran_businesses(callback=sam_resume_cb, resume=True)
                progress_bar.progress(1.0)
                st.success(
                    f"Resume complete! "
                    f"Fetched: {result['total_fetched']} | "
                    f"New: {result['new']} | "
                    f"Updated: {result['updated']}"
                )
            except Exception as e:
                st.error(f"SAM.gov resume error: {e}")

st.divider()

# --- USAspending Fetch ---
st.subheader("USAspending.gov — Federal Contract Awards")
st.caption("No API key needed — free, open data")

if st.button("Fetch USAspending Data", key="usa_fetch", type="primary"):
    progress_bar = st.progress(0)
    status_text = st.empty()

    def usa_callback(msg, pct):
        status_text.text(msg)
        if pct is not None:
            progress_bar.progress(min(pct, 1.0))

    try:
        from usaspending import fetch_usaspending_veterans
        result = fetch_usaspending_veterans(callback=usa_callback)
        progress_bar.progress(1.0)
        st.success(
            f"USAspending fetch complete! "
            f"Unique recipients: {result['unique_recipients']} | "
            f"New: {result['new']} | "
            f"Updated: {result['updated']}"
        )
    except Exception as e:
        st.error(f"USAspending fetch error: {e}")

st.divider()

# --- Contact Enrichment ---
st.subheader("Contact Enrichment")
st.caption("Search the web for missing phone, email, and website info (DuckDuckGo + site scraping)")

contact_stats = get_contact_stats()
ct_col1, ct_col2, ct_col3, ct_col4 = st.columns(4)
ct_col1.metric("Have Phone", f"{contact_stats['has_phone']}/{contact_stats['total']}")
ct_col2.metric("Have Email", f"{contact_stats['has_email']}/{contact_stats['total']}")
ct_col3.metric("Have Website", f"{contact_stats['has_website']}/{contact_stats['total']}")
ct_col4.metric("Missing All Contact", contact_stats["missing_all"])

enrich_batch_size = st.slider("Batch size", min_value=10, max_value=200, value=50, step=10,
                              help="Number of businesses to enrich per run")

if st.button("Enrich Missing Contacts", key="enrich_contacts", type="primary"):
    progress_bar = st.progress(0)
    status_text = st.empty()

    def enrich_callback(msg, pct):
        status_text.text(msg)
        if pct is not None:
            progress_bar.progress(min(pct, 1.0))

    try:
        from enrich import run_enrichment_batch
        result = run_enrichment_batch(batch_size=enrich_batch_size, callback=enrich_callback)
        progress_bar.progress(1.0)
        st.success(
            f"Enrichment complete! "
            f"Processed: {result['total_processed']} | "
            f"Enriched: {result['enriched']} | "
            f"Skipped: {result['skipped']}"
        )
    except Exception as e:
        st.error(f"Enrichment error: {e}")

st.divider()

# --- Summary ---
st.subheader("Database Summary")
stats = get_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Total Businesses", stats["total"])
col2.metric("States Represented", len(stats.get("by_state", {})))
col3.metric("Data Sources", len(stats.get("by_source", {})))
