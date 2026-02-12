"""
USAspending.gov API client.
Fetches veteran-owned businesses that have received federal contracts.
No API key required — free, open data.
"""

import time
import requests
from datetime import datetime, timedelta

from config import USASPENDING_BASE_URL, SOURCE_USASPENDING
from geo import geocode_business
from database import (
    upsert_business_cross_source, start_fetch_log, complete_fetch_log,
)

# USAspending recipient type codes for veteran-owned businesses
VETERAN_RECIPIENT_TYPES = [
    "veteran_owned_business",
    "service_disabled_veterans_small_business",
]

# Contract award type codes
CONTRACT_AWARD_TYPES = ["A", "B", "C", "D"]  # Various contract types

# Map USAspending recipient types to our business_type field
_TYPE_MAP = {
    "veteran_owned_business": "Veteran Owned Small Business",
    "service_disabled_veterans_small_business": "Service Disabled Veteran Owned Small Business",
}

# Max pages per recipient type to avoid infinite loops
MAX_PAGES = 500


def fetch_usaspending_veterans(callback=None):
    """Fetch veteran-owned businesses from USAspending.gov contract awards.

    Args:
        callback: Optional callable(message, progress_pct) for UI updates.

    Returns:
        dict with total_fetched, new, updated, unique_recipients.
    """
    log_id = start_fetch_log(SOURCE_USASPENDING)

    result = {"total_fetched": 0, "new": 0, "updated": 0, "unique_recipients": 0}

    # Deduplicate by (normalized_name, state) across pages
    seen_recipients = {}  # key: (name_lower, state) -> aggregated award total

    try:
        five_years_ago = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        for vet_type in VETERAN_RECIPIENT_TYPES:
            type_label = _TYPE_MAP.get(vet_type, vet_type)
            if callback:
                callback(f"Fetching {type_label}...", None)
            else:
                print(f"\nFetching {type_label}...")

            page = 1
            has_next = True

            while has_next and page <= MAX_PAGES:
                payload = {
                    "filters": {
                        "recipient_type_names": [vet_type],
                        "award_type_codes": CONTRACT_AWARD_TYPES,
                        "time_period": [
                            {"start_date": five_years_ago, "end_date": today}
                        ],
                    },
                    "fields": [
                        "Recipient Name",
                        "Award Amount",
                        "Place of Performance State Code",
                        "Place of Performance Zip5",
                    ],
                    "page": page,
                    "limit": 100,
                    "sort": "Award Amount",
                    "order": "desc",
                }

                try:
                    resp = requests.post(
                        f"{USASPENDING_BASE_URL}/search/spending_by_award/",
                        json=payload,
                        timeout=60,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except requests.exceptions.HTTPError:
                    if resp.status_code == 429:
                        msg = "USAspending rate limited, waiting 30s..."
                        if callback:
                            callback(msg, None)
                        else:
                            print(f"  {msg}")
                        time.sleep(30)
                        continue
                    if callback:
                        callback(f"API error: HTTP {resp.status_code}", None)
                    else:
                        print(f"  API error: HTTP {resp.status_code}")
                    break
                except Exception as e:
                    if callback:
                        callback(f"Request error: {e}", None)
                    else:
                        print(f"  Request error: {e}")
                    break

                awards = data.get("results", [])
                if not awards:
                    has_next = False
                    break

                page_meta = data.get("page_metadata", {})
                has_next = page_meta.get("hasNext", False)

                if callback:
                    callback(f"Fetching {type_label}: page {page} ({len(seen_recipients)} unique so far)", None)
                elif page % 10 == 0:
                    print(f"  Page {page}, {len(seen_recipients)} unique recipients so far")

                for award in awards:
                    name = (award.get("Recipient Name") or "").strip()
                    state = (award.get("Place of Performance State Code") or "").strip()
                    if not name:
                        continue

                    key = (name.lower(), state)
                    amount = award.get("Award Amount") or 0

                    if key in seen_recipients:
                        seen_recipients[key]["total_awards"] += float(amount) if amount else 0
                        seen_recipients[key]["award_count"] += 1
                        continue

                    seen_recipients[key] = {
                        "name": name,
                        "state": state,
                        "zip_code": (award.get("Place of Performance Zip5") or "").strip(),
                        "biz_type": _TYPE_MAP.get(vet_type, "Veteran Owned Small Business"),
                        "total_awards": float(amount) if amount else 0,
                        "award_count": 1,
                    }

                page += 1
                time.sleep(0.5)

        # Now upsert all unique recipients
        total_recipients = len(seen_recipients)
        result["unique_recipients"] = total_recipients

        if not callback:
            print(f"\nSaving {total_recipients} unique recipients...")

        for i, ((name_lower, state), info) in enumerate(seen_recipients.items()):
            if callback and i % 50 == 0:
                pct = i / max(total_recipients, 1)
                callback(f"Saving recipients: {i}/{total_recipients}", pct)
            elif not callback and i % 500 == 0 and i > 0:
                print(f"  Saved {i}/{total_recipients}")

            awards_note = f"Federal contracts: ${info['total_awards']:,.0f} ({info['award_count']} awards)"

            business = {
                "legal_business_name": info["name"],
                "state": info["state"],
                "zip_code": info["zip_code"],
                "business_type": info["biz_type"],
                "source": SOURCE_USASPENDING,
                "notes": awards_note,
            }

            geocode_business(business)
            status = upsert_business_cross_source(business)
            result["total_fetched"] += 1
            if status == "new":
                result["new"] += 1
            elif status == "updated":
                result["updated"] += 1

        complete_fetch_log(
            log_id, status="completed",
            records_fetched=result["total_fetched"],
            records_new=result["new"],
            records_updated=result["updated"],
        )

        if callback:
            callback("USAspending fetch complete!", 1.0)
        else:
            print(f"\nDone! Fetched: {result['total_fetched']}, "
                  f"New: {result['new']}, Updated: {result['updated']}")

    except Exception as e:
        complete_fetch_log(log_id, status="failed", error_msg=str(e),
                           records_fetched=result["total_fetched"],
                           records_new=result["new"],
                           records_updated=result["updated"])
        raise

    return result
