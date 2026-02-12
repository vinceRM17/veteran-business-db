#!/usr/bin/env python3
"""
Contact enrichment script.
Searches the web for each business and extracts phone, website, email, and social links.
Uses the duckduckgo-search library for reliable results.
"""

import re
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ddgs import DDGS
from database import get_connection, create_tables

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

PHONE_RE = re.compile(r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}')
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

SOCIAL_PATTERNS = {
    "facebook": re.compile(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.]+/?'),
    "instagram": re.compile(r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+/?'),
    "linkedin": re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-]+/?'),
    "twitter": re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+/?'),
}

SKIP_DOMAINS = {
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
    "yelp.com", "yellowpages.com", "bbb.org", "mapquest.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
    "veteranownedbusiness.com", "sam.gov", "wikipedia.org",
    "indeed.com", "glassdoor.com", "manta.com", "nextdoor.com",
    "angi.com", "thumbtack.com", "chamberofcommerce.com",
}


def search_web(query, max_results=8):
    """Search using duckduckgo-search library."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
    except Exception as e:
        print(f"search error: {e}")
        return []


def extract_website(results, business_name):
    """Find the most likely business website from search results."""
    for r in results:
        try:
            domain = urlparse(r["url"]).netloc.lower().replace("www.", "")
        except Exception:
            continue
        if any(skip in domain for skip in SKIP_DOMAINS):
            continue
        return r["url"]
    return ""


def extract_phone_from_snippets(results):
    """Extract phone numbers from search result snippets."""
    for r in results:
        text = r.get("snippet", "") + " " + r.get("title", "")
        match = PHONE_RE.search(text)
        if match:
            return match.group(0)
    return ""


def extract_email_from_snippets(results):
    """Extract email addresses from search result snippets."""
    for r in results:
        text = r.get("snippet", "") + " " + r.get("title", "")
        match = EMAIL_RE.search(text)
        if match:
            email = match.group(0)
            if not any(x in email.lower() for x in ["example.com", "email.com", "domain.com"]):
                return email
    return ""


def extract_socials_from_results(results):
    """Extract social media URLs from search results."""
    socials = {}
    for r in results:
        url = r.get("url", "")
        for platform, pattern in SOCIAL_PATTERNS.items():
            if platform not in socials:
                match = pattern.search(url)
                if match:
                    socials[platform] = match.group(0)
    return socials


def scrape_website_for_contact(url):
    """Visit the business website and scrape for phone, email, social links."""
    info = {"phone": "", "email": "", "socials": {}}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return info

        text = resp.text

        # Phone
        match = PHONE_RE.search(text)
        if match:
            info["phone"] = match.group(0)

        # Email - look in mailto links first
        soup = BeautifulSoup(text, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("mailto:"):
                email = a["href"].replace("mailto:", "").split("?")[0].strip()
                if EMAIL_RE.match(email):
                    info["email"] = email
                    break

        if not info["email"]:
            match = EMAIL_RE.search(text)
            if match:
                email = match.group(0)
                if not any(x in email.lower() for x in [
                    "example.com", "wixpress", "sentry", "webpack",
                    "googleapis", "schema.org", "w3.org", "jquery",
                    "godaddy", "squarespace", "wordpress", "shopify",
                    "wix.com", "weebly", "cloudflare", "cpanel",
                    "placeholder", "yourname", "youremail", "noreply",
                ]):
                    info["email"] = email

        # Social links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            for platform, pattern in SOCIAL_PATTERNS.items():
                if platform not in info["socials"]:
                    match = pattern.search(href)
                    if match:
                        info["socials"][platform] = match.group(0)

    except Exception:
        pass

    return info


def enrich_business(biz_id, name, city, state):
    """Search for a business and extract all available contact info."""
    query = f"{name} {city} {state} phone"
    results = search_web(query)

    if not results:
        return None

    website = extract_website(results, name)
    phone = extract_phone_from_snippets(results)
    email = extract_email_from_snippets(results)
    socials = extract_socials_from_results(results)

    # If we found a website, try to scrape it for more details
    if website and (not phone or not email or not socials):
        site_info = scrape_website_for_contact(website)
        if not phone and site_info["phone"]:
            phone = site_info["phone"]
        if not email and site_info["email"]:
            email = site_info["email"]
        if site_info["socials"]:
            for k, v in site_info["socials"].items():
                if k not in socials:
                    socials[k] = v

    # Build social string for notes
    social_str = ""
    if socials:
        social_str = " | ".join(f"{k}: {v}" for k, v in socials.items())

    return {
        "phone": phone,
        "email": email,
        "website": website,
        "socials": social_str,
    }


def run_enrichment():
    """Enrich all businesses that are missing contact info."""
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, legal_business_name, city, state
        FROM businesses
        WHERE (phone IS NULL OR phone = '')
          AND (email IS NULL OR email = '')
          AND (website IS NULL OR website = '')
        ORDER BY distance_miles ASC
    """)
    businesses = cursor.fetchall()
    conn.close()

    total = len(businesses)
    print(f"Enriching {total} businesses missing contact info...\n")

    enriched = 0
    for i, biz in enumerate(businesses):
        name = biz["legal_business_name"]
        city = biz["city"]
        state = biz["state"]

        print(f"  [{i+1}/{total}] {name}, {city} {state}...", end=" ", flush=True)

        try:
            info = enrich_business(biz["id"], name, city, state)
        except Exception as e:
            print(f"error: {e}")
            time.sleep(3)
            continue

        if info is None:
            print("no results")
            time.sleep(2)
            continue

        found = []
        if info["phone"]:
            found.append("phone")
        if info["email"]:
            found.append("email")
        if info["website"]:
            found.append("website")
        if info["socials"]:
            found.append("social")

        if found:
            conn = get_connection()
            cursor = conn.cursor()

            existing_notes = ""
            cursor.execute("SELECT notes FROM businesses WHERE id = ?", (biz["id"],))
            row = cursor.fetchone()
            if row and row["notes"]:
                existing_notes = row["notes"]

            notes = existing_notes
            if info["socials"]:
                social_note = f"Social: {info['socials']}"
                if social_note not in (notes or ""):
                    notes = f"{notes}\n{social_note}".strip() if notes else social_note

            cursor.execute("""
                UPDATE businesses
                SET phone = CASE WHEN phone IS NULL OR phone = '' THEN ? ELSE phone END,
                    email = CASE WHEN email IS NULL OR email = '' THEN ? ELSE email END,
                    website = CASE WHEN website IS NULL OR website = '' THEN ? ELSE website END,
                    notes = ?
                WHERE id = ?
            """, (info["phone"], info["email"], info["website"], notes, biz["id"]))

            conn.commit()
            conn.close()
            enriched += 1
            print(f"found: {', '.join(found)}")
        else:
            print("nothing found")

        time.sleep(2)

    print(f"\nDone! Enriched {enriched}/{total} businesses.")

    # Print summary
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE phone != '' AND phone IS NOT NULL")
    phones = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE email != '' AND email IS NOT NULL")
    emails = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE website != '' AND website IS NOT NULL")
    websites = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses")
    total_biz = cursor.fetchone()[0]
    conn.close()

    print(f"\nContact coverage:")
    print(f"  Phone:   {phones}/{total_biz}")
    print(f"  Email:   {emails}/{total_biz}")
    print(f"  Website: {websites}/{total_biz}")


def run_enrichment_batch(batch_size=50, callback=None):
    """Enrich a batch of businesses missing contact info.

    Args:
        batch_size: Max number of businesses to process.
        callback: Optional callable(message, progress_pct) for UI updates.

    Returns:
        dict with keys: enriched, skipped, total_processed
    """
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, legal_business_name, city, state
        FROM businesses
        WHERE (phone IS NULL OR phone = '')
          AND (email IS NULL OR email = '')
          AND (website IS NULL OR website = '')
        ORDER BY distance_miles ASC
        LIMIT ?
    """, (batch_size,))
    businesses = cursor.fetchall()
    conn.close()

    total = len(businesses)
    if callback:
        callback(f"Found {total} businesses to enrich...", 0.0)

    enriched = 0
    skipped = 0

    for i, biz in enumerate(businesses):
        name = biz["legal_business_name"]
        city = biz["city"]
        state = biz["state"]
        progress = (i + 1) / total if total else 1.0

        if callback:
            callback(f"[{i+1}/{total}] {name}, {city} {state}", progress * 0.95)

        try:
            info = enrich_business(biz["id"], name, city, state)
        except Exception:
            skipped += 1
            time.sleep(3)
            continue

        if info is None:
            skipped += 1
            time.sleep(2)
            continue

        found = []
        if info["phone"]:
            found.append("phone")
        if info["email"]:
            found.append("email")
        if info["website"]:
            found.append("website")
        if info["socials"]:
            found.append("social")

        if found:
            conn = get_connection()
            cursor = conn.cursor()

            existing_notes = ""
            cursor.execute("SELECT notes FROM businesses WHERE id = ?", (biz["id"],))
            row = cursor.fetchone()
            if row and row["notes"]:
                existing_notes = row["notes"]

            notes = existing_notes
            if info["socials"]:
                social_note = f"Social: {info['socials']}"
                if social_note not in (notes or ""):
                    notes = f"{notes}\n{social_note}".strip() if notes else social_note

            cursor.execute("""
                UPDATE businesses
                SET phone = CASE WHEN phone IS NULL OR phone = '' THEN ? ELSE phone END,
                    email = CASE WHEN email IS NULL OR email = '' THEN ? ELSE email END,
                    website = CASE WHEN website IS NULL OR website = '' THEN ? ELSE website END,
                    notes = ?
                WHERE id = ?
            """, (info["phone"], info["email"], info["website"], notes, biz["id"]))

            conn.commit()
            conn.close()
            enriched += 1
        else:
            skipped += 1

        time.sleep(2)

    if callback:
        callback("Enrichment complete!", 1.0)

    return {"enriched": enriched, "skipped": skipped, "total_processed": total}


if __name__ == "__main__":
    run_enrichment()
