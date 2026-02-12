"""
SAM.gov Entity Management API client.
Fetches veteran-owned businesses by state and parses results.
Supports nationwide pull, resume, and progress callbacks.
"""

import time
import requests

from config import (
    SAM_GOV_API_KEY, SAM_GOV_BASE_URL, VETERAN_BUSINESS_TYPES,
    ALL_US_STATES, SOURCE_SAM_GOV,
)
from geo import geocode_business
from database import (
    upsert_business_cross_source, start_fetch_log, complete_fetch_log,
    get_last_fetch,
)


def fetch_veteran_businesses(states=None, callback=None, resume=False):
    """Fetch veteran-owned businesses from SAM.gov.

    Args:
        states: List of state codes to fetch. Defaults to ALL_US_STATES.
        callback: Optional callable(message, progress_pct) for UI updates.
        resume: If True, skip state/type combos already fetched today.

    Returns:
        dict with total_fetched, new, updated, states_completed, states_failed.
    """
    if not SAM_GOV_API_KEY:
        raise ValueError("SAM_GOV_API_KEY not set in config.py")

    if states is None:
        states = ALL_US_STATES

    log_id = start_fetch_log(SOURCE_SAM_GOV)

    # Check what was already fetched today for resume
    completed_today = set()
    if resume:
        last = get_last_fetch(SOURCE_SAM_GOV)
        if last and last.get("details"):
            completed_today = set(last["details"].split(","))

    result = {"total_fetched": 0, "new": 0, "updated": 0,
              "states_completed": [], "states_failed": []}

    total_combos = len(states) * len(VETERAN_BUSINESS_TYPES)
    done_combos = 0

    try:
        for state in states:
            for biz_type in VETERAN_BUSINESS_TYPES:
                combo_key = f"{state}:{biz_type}"
                if resume and combo_key in completed_today:
                    done_combos += 1
                    continue

                try:
                    fetched, new, updated = _fetch_by_state_and_type(
                        state, biz_type, callback, done_combos, total_combos,
                    )
                    result["total_fetched"] += fetched
                    result["new"] += new
                    result["updated"] += updated
                except Exception as e:
                    if callback:
                        callback(f"Error fetching {state}/{biz_type}: {e}", None)
                    result["states_failed"].append(state)

                done_combos += 1

            result["states_completed"].append(state)

        completed_details = ",".join(
            f"{s}:{t}" for s in result["states_completed"] for t in VETERAN_BUSINESS_TYPES
        )
        complete_fetch_log(
            log_id, status="completed",
            records_fetched=result["total_fetched"],
            records_new=result["new"],
            records_updated=result["updated"],
            details=completed_details,
        )
    except Exception as e:
        complete_fetch_log(log_id, status="failed", error_msg=str(e),
                           records_fetched=result["total_fetched"],
                           records_new=result["new"],
                           records_updated=result["updated"])
        raise

    return result


def _fetch_by_state_and_type(state, biz_type, callback, done_combos, total_combos):
    """Fetch all entities for a single state/type combo. Returns (fetched, new, updated)."""
    if callback:
        pct = done_combos / max(total_combos, 1)
        callback(f"Fetching {biz_type} in {state}...", pct)
    else:
        print(f"\nFetching: {biz_type} in {state}...")

    fetched = 0
    new = 0
    updated = 0
    page = 0
    total_pages = 1

    while page < total_pages:
        params = {
            "api_key": SAM_GOV_API_KEY,
            "physicalAddressProvinceOrStateCode": state,
            "sbaBusinessTypeDesc": biz_type,
            "registrationStatus": "A",
            "page": page,
            "size": 10,
        }

        try:
            resp = requests.get(SAM_GOV_BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError:
            if resp.status_code == 429:
                msg = f"Rate limited on {state}, waiting 60s..."
                if callback:
                    callback(msg, None)
                else:
                    print(f"  {msg}")
                time.sleep(60)
                continue
            break
        except Exception as e:
            if not callback:
                print(f"  Request error: {e}")
            break

        total_records = data.get("totalRecords", 0)
        if page == 0:
            total_pages = min((total_records // 10) + 1, 1000)

        entities = data.get("entityData", [])
        if not entities:
            break

        for entity in entities:
            business = _parse_entity(entity, biz_type)
            if business is None:
                continue

            geocode_business(business)
            status = upsert_business_cross_source(business)
            fetched += 1
            if status == "new":
                new += 1
            elif status == "updated":
                updated += 1

        page += 1
        time.sleep(0.5)

    if not callback:
        print(f"  Fetched: {fetched}, New: {new}, Updated: {updated}")

    return fetched, new, updated


def _parse_entity(entity: dict, biz_type: str):
    try:
        reg = entity.get("entityRegistration", {})
        core = entity.get("coreData", {})
        entity_info = core.get("entityInformation", {})
        phys_addr = core.get("physicalAddress", {})

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
            "phone": "",
            "email": "",
            "website": "",
            "business_type": biz_type,
            "naics_codes": ", ".join(naics_codes),
            "naics_descriptions": ", ".join(naics_descs),
            "registration_status": reg.get("registrationStatus", ""),
            "registration_expiration": reg.get("registrationExpirationDate", ""),
            "entity_start_date": entity_info.get("entityStartDate", ""),
            "source": SOURCE_SAM_GOV,
        }
    except Exception as e:
        print(f"  Parse error: {e}")
        return None
