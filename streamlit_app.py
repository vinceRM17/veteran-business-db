import streamlit as st
from database import create_tables, get_stats, get_contact_stats

st.set_page_config(
    page_title="Veteran Business DB - Active Heroes",
    page_icon="🛡️",
    layout="wide",
)

create_tables()

# --- Auth state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🛡️ Veteran Business DB")
    st.caption("Active Heroes - Shepherdsville, KY")
    st.divider()

    if st.session_state.logged_in:
        st.success("Logged in as Admin")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        with st.expander("Admin Login"):
            pwd = st.text_input("Password", type="password", key="login_pwd")
            if st.button("Log In"):
                from config import ADMIN_PASSWORD
                if pwd == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password")

# --- Dashboard ---
st.title("Dashboard")
st.markdown("Veteran-owned businesses within **100 miles** of Active Heroes, Shepherdsville KY")

stats = get_stats()
contact_stats = get_contact_stats()

# Top stats
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Businesses", stats["total"])

vob_count = 0
sdvosb_count = 0
for t, c in stats.get("by_type", {}).items():
    if "Service Disabled" in (t or ""):
        sdvosb_count += c
    else:
        vob_count += c
col2.metric("VOB", vob_count)
col3.metric("SDVOSB", sdvosb_count)

if contact_stats["total"] > 0:
    pct = round(contact_stats["has_phone"] / contact_stats["total"] * 100)
    col4.metric("Have Phone", f"{pct}%")

if stats["total"] == 0:
    st.warning("Database is empty. Use the **Fetch Data** or **Import CSV** page to load businesses.")
    st.stop()

st.divider()

# Charts row
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("By State")
    if stats.get("by_state"):
        import pandas as pd
        df = pd.DataFrame(
            list(stats["by_state"].items()),
            columns=["State", "Count"]
        )
        st.bar_chart(df.set_index("State"))

with col_right:
    st.subheader("Contact Completeness")
    if contact_stats["total"] > 0:
        t = contact_stats["total"]
        st.progress(contact_stats["has_phone"] / t, text=f"Phone: {contact_stats['has_phone']}/{t}")
        st.progress(contact_stats["has_email"] / t, text=f"Email: {contact_stats['has_email']}/{t}")
        st.progress(contact_stats["has_website"] / t, text=f"Website: {contact_stats['has_website']}/{t}")

# Distance and source
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("By Distance")
    if stats.get("by_distance"):
        for bracket, count in stats["by_distance"].items():
            st.text(f"{bracket}: {count}")

with col_b:
    st.subheader("By Source")
    if stats.get("by_source"):
        for source, count in stats["by_source"].items():
            st.text(f"{source}: {count}")
