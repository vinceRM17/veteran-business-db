"""Yelp Fusion API enrichment for veteran-owned businesses."""

import requests
from config import YELP_API_KEY, YELP_API_BASE
from database import get_connection, update_business_fields


def search_yelp(name, city, state):
    """Search Yelp for a business and return rating data.

    Returns dict with rating, review_count, url or None if not found.
    """
    if not YELP_API_KEY:
        return None

    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "term": name,
        "location": f"{city}, {state}",
        "limit": 1,
    }

    try:
        resp = requests.get(
            f"{YELP_API_BASE}/businesses/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        businesses = data.get("businesses", [])
        if not businesses:
            return None

        biz = businesses[0]
        return {
            "yelp_rating": biz.get("rating"),
            "yelp_review_count": biz.get("review_count", 0),
            "yelp_url": biz.get("url", ""),
        }
    except Exception:
        return None


def run_yelp_enrichment_batch(batch_size=50, callback=None):
    """Enrich businesses missing Yelp data.

    Returns dict with total_processed, enriched, skipped counts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, legal_business_name, city, state
        FROM businesses
        WHERE yelp_rating IS NULL
          AND legal_business_name IS NOT NULL AND legal_business_name != ''
          AND city IS NOT NULL AND city != ''
          AND state IS NOT NULL AND state != ''
        LIMIT ?
    """, (batch_size,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total = len(rows)
    enriched = 0
    skipped = 0

    for i, row in enumerate(rows):
        if callback:
            pct = (i + 1) / total if total > 0 else 1.0
            callback(f"Searching Yelp for {row['legal_business_name']}...", pct)

        result = search_yelp(row["legal_business_name"], row["city"], row["state"])
        if result and result.get("yelp_rating") is not None:
            update_business_fields(row["id"], result)
            enriched += 1
        else:
            skipped += 1

    return {
        "total_processed": total,
        "enriched": enriched,
        "skipped": skipped,
    }
