"""
SAM.gov Entity Management API client.
Fetches veteran-owned businesses by state and parses results.
"""

import time
import requests

from config import SAM_GOV_API_KEY, SAM_GOV_BASE_URL, VETERAN_BUSINESS_TYPES, SEARCH_STATES
from geo import is_within_radius
from database import upsert_business


def fetch_veteran_businesses():
    if not SAM_GOV_API_KEY:
        print("ERROR: Set SAM_GOV_API_KEY in config.py")
        print("Get your free key at: https://sam.gov/profile/details")
        return 0

    total_saved = 0

    for biz_type in VETERAN_BUSINESS_TYPES:
        for state in SEARCH_STATES:
            count = _fetch_by_state_and_type(state, biz_type)
            total_saved += count

    return total_saved


def _fetch_by_state_and_type(state: str, biz_type: str):
    print(f"\nFetching: {biz_type} in {state}...")
    saved = 0
    skipped = 0
    page = 0
    total_pages = 1  # will be updated after first call

    while page < total_pages:
        params = {
            "api_key": SAM_GOV_API_KEY,
            "physicalAddressProvinceOrStateCode": state,
            "sbaBusinessTypeDesc": biz_type,
            "registrationStatus": "A",  # Active registrations only
            "page": page,
            "size": 100,
        }

        try:
            resp = requests.get(SAM_GOV_BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print("  Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            print(f"  API error: {e}")
            break
        except Exception as e:
            print(f"  Request error: {e}")
            break

        total_records = data.get("totalRecords", 0)
        if page == 0:
            total_pages = (total_records // 100) + 1
            print(f"  Found {total_records} records ({total_pages} pages)")

        entities = data.get("entityData", [])
        if not entities:
            break

        for entity in entities:
            business = _parse_entity(entity, biz_type)
            if business is None:
                continue

            zip_code = business.get("zip_code", "")
            if zip_code:
                # Take first 5 digits of zip
                zip5 = zip_code[:5]
                within, dist = is_within_radius(zip5)
                if within:
                    business["distance_miles"] = dist
                    upsert_business(business)
                    saved += 1
                else:
                    skipped += 1
            else:
                skipped += 1

        page += 1
        time.sleep(0.5)  # Be polite to the API

    print(f"  Saved: {saved}, Skipped (outside radius): {skipped}")
    return saved


def _parse_entity(entity: dict, biz_type: str):
    try:
        reg = entity.get("entityRegistration", {})
        core = entity.get("coreData", {})
        entity_info = core.get("entityInformation", {})
        phys_addr = core.get("physicalAddress", {})

        # Get NAICS codes
        assertions = entity.get("assertions", {})
        goods = assertions.get("goodsAndServices", {})
        naics_list = goods.get("naicsList", []) if goods else []
        naics_codes = []
        naics_descs = []
        for n in naics_list:
            naics_entry = n.get("naicsCode", "")
            if naics_entry:
                naics_codes.append(str(naics_entry))
                desc = n.get("naicsDescription", "")
                if desc:
                    naics_descs.append(desc)

        # Get contact info
        poc = core.get("businessInformation", {})

        return {
            "uei": reg.get("ueiSAM", ""),
            "cage_code": reg.get("cageCode", ""),
            "legal_business_name": reg.get("legalBusinessName", ""),
            "dba_name": reg.get("dbaName", ""),
            "physical_address_line1": phys_addr.get("addressLine1", ""),
            "physical_address_line2": phys_addr.get("addressLine2", ""),
            "city": phys_addr.get("city", ""),
            "state": phys_addr.get("stateOrProvinceCode", ""),
            "zip_code": phys_addr.get("zipCode", ""),
            "phone": "",  # Not in public API response
            "email": "",  # Not in public API response
            "website": "",
            "business_type": biz_type,
            "naics_codes": ", ".join(naics_codes),
            "naics_descriptions": ", ".join(naics_descs),
            "registration_status": reg.get("registrationStatus", ""),
            "registration_expiration": reg.get("registrationExpirationDate", ""),
            "entity_start_date": entity_info.get("entityStartDate", ""),
            "source": "SAM.gov",
        }
    except Exception as e:
        print(f"  Parse error: {e}")
        return None
