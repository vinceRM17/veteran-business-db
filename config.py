"""
Configuration for Veteran-Owned Business Database Pipeline.

Update SAM_GOV_API_KEY with your free key from https://sam.gov/profile/details
"""

# --- SAM.gov API ---
SAM_GOV_API_KEY = "SAM-23614dcb-ca88-4815-906c-8833cc26472a"
SAM_GOV_BASE_URL = "https://api.sam.gov/entity-information/v3/entities"

# --- Active Heroes Location ---
ACTIVE_HEROES_ADDRESS = "1022 Ridgeview Dr, Shepherdsville, KY 40165"
ACTIVE_HEROES_ZIP = "40165"
ACTIVE_HEROES_LAT = 37.9884
ACTIVE_HEROES_LON = -85.7138
SEARCH_RADIUS_MILES = 100

# --- States that fall within ~100mi of Shepherdsville, KY ---
# Covers Louisville, Lexington, Bowling Green, Cincinnati, Indianapolis, etc.
SEARCH_STATES = ["KY", "IN", "OH", "TN", "WV"]

# --- Database ---
DB_PATH = "veteran_businesses.db"

# --- Admin Login ---
ADMIN_PASSWORD = "ActiveHeroes2026"  # Change this to your own password

# --- SAM.gov SBA Business Type Descriptions for Veterans ---
VETERAN_BUSINESS_TYPES = [
    "Veteran Owned Small Business",
    "Service Disabled Veteran Owned Small Business",
]
