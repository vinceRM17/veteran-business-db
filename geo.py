"""
Geographic utilities for filtering businesses by distance from Active Heroes.
Uses pgeocode for offline zip-to-coordinates lookup and Haversine formula.
"""

import math
import pgeocode

from config import ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON, SEARCH_RADIUS_MILES

_nomi = pgeocode.Nominatim("us")


def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def zip_to_coords(zip_code: str):
    result = _nomi.query_postal_code(zip_code)
    if result is not None and not math.isnan(result.latitude):
        return result.latitude, result.longitude
    return None, None


def distance_from_active_heroes(zip_code: str):
    lat, lon = zip_to_coords(zip_code)
    if lat is None:
        return None
    return haversine_miles(ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON, lat, lon)


def is_within_radius(zip_code: str, radius=SEARCH_RADIUS_MILES):
    dist = distance_from_active_heroes(zip_code)
    if dist is None:
        return False, None
    return dist <= radius, round(dist, 1)


def geocode_business(business: dict) -> dict:
    """Add lat/lon from zip code and compute distance_miles from Active Heroes HQ.

    Modifies and returns the business dict in-place.
    """
    zip_code = (business.get("zip_code") or "")[:5]
    if zip_code and not business.get("latitude"):
        lat, lon = zip_to_coords(zip_code)
        if lat is not None:
            business["latitude"] = lat
            business["longitude"] = lon
            business["distance_miles"] = round(
                haversine_miles(ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON, lat, lon), 1
            )
    return business


def batch_geocode_missing():
    """Find all DB records with zip but no coords, geocode them.

    Returns number of records updated.
    """
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, zip_code FROM businesses "
        "WHERE zip_code IS NOT NULL AND zip_code != '' "
        "AND (latitude IS NULL OR longitude IS NULL)"
    )
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        zip5 = (row["zip_code"] or "")[:5]
        lat, lon = zip_to_coords(zip5)
        if lat is not None:
            dist = round(haversine_miles(ACTIVE_HEROES_LAT, ACTIVE_HEROES_LON, lat, lon), 1)
            cursor.execute(
                "UPDATE businesses SET latitude = ?, longitude = ?, distance_miles = ? WHERE id = ?",
                (lat, lon, dist, row["id"]),
            )
            updated += 1
    conn.commit()
    conn.close()
    return updated


def compute_distances_from_point(origin_lat, origin_lon, businesses):
    """Return copies of business dicts with custom_distance_miles added, sorted by distance."""
    results = []
    for biz in businesses:
        lat, lon = biz.get("latitude"), biz.get("longitude")
        if lat is None or lon is None:
            continue
        dist = round(haversine_miles(origin_lat, origin_lon, lat, lon), 1)
        entry = dict(biz)
        entry["custom_distance_miles"] = dist
        results.append(entry)
    results.sort(key=lambda b: b["custom_distance_miles"])
    return results


def filter_by_custom_radius(origin_lat, origin_lon, businesses, radius_miles):
    """Compute distances from origin and return only those within radius_miles."""
    with_distances = compute_distances_from_point(origin_lat, origin_lon, businesses)
    return [b for b in with_distances if b["custom_distance_miles"] <= radius_miles]
