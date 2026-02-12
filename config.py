"""
Configuration for Veteran-Owned Business Database Pipeline.

Update SAM_GOV_API_KEY with your free key from https://sam.gov/profile/details
"""

import os


def _get_secret(key):
    """Read from Streamlit secrets (if running in Streamlit) or env vars."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.environ.get(key)

# --- SAM.gov API ---
SAM_GOV_API_KEY = "SAM-23614dcb-ca88-4815-906c-8833cc26472a"
SAM_GOV_BASE_URL = "https://api.sam.gov/entity-information/v3/entities"

# --- Active Heroes Location ---
ACTIVE_HEROES_ADDRESS = "1022 Ridgeview Dr, Shepherdsville, KY 40165"
ACTIVE_HEROES_ZIP = "40165"
ACTIVE_HEROES_LAT = 37.9884
ACTIVE_HEROES_LON = -85.7138
SEARCH_RADIUS_MILES = 100

# --- States that fall within ~100mi of Shepherdsville, KY (legacy) ---
SEARCH_STATES = ["KY", "IN", "OH", "TN", "WV"]

# --- All US states + DC + territories for nationwide pull ---
ALL_US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "VI", "WA",
    "WV", "WI", "WY",
]

# --- USAspending.gov API ---
USASPENDING_BASE_URL = "https://api.usaspending.gov/api/v2"

# --- Data source constants ---
SOURCE_SAM_GOV = "SAM.gov"
SOURCE_USASPENDING = "USAspending.gov"
SOURCE_CSV_IMPORT = "CSV Import"

# --- Database ---
DB_PATH = "veteran_businesses.db"

# --- Turso Cloud Database (optional, for Streamlit Cloud deployment) ---
TURSO_URL = _get_secret("TURSO_CONNECTION_URL")
TURSO_AUTH_TOKEN = _get_secret("TURSO_AUTH_TOKEN")

# --- Admin Login ---
ADMIN_PASSWORD = "ActiveHeroes2026"  # Change this to your own password

# --- SAM.gov SBA Business Type Descriptions for Veterans ---
VETERAN_BUSINESS_TYPES = [
    "Veteran Owned Small Business",
    "Service Disabled Veteran Owned Small Business",
]
