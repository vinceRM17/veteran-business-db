#!/usr/bin/env python3
"""
Veteran-Owned Business Database Pipeline

Builds a nationwide database of veteran-owned businesses from
federal data sources (SAM.gov, USAspending.gov).

Data sources:
  - SAM.gov Entity Management API (automated, nationwide)
  - USAspending.gov contract awards (automated, no key needed)
  - CSV import (manual data)

Usage:
  python main.py fetch                    # Fetch from all sources
  python main.py fetch --source sam       # SAM.gov only
  python main.py fetch --source usaspending  # USAspending only
  python main.py fetch --resume           # Resume interrupted SAM.gov fetch
  python main.py status                   # Show fetch history per source
  python main.py import FILE              # Import a CSV file
  python main.py export                   # Export database to CSV
  python main.py stats                    # Show database statistics
  python main.py search TERM             # Search by business name
"""

import sys

from config import DB_PATH, SOURCE_SAM_GOV, SOURCE_USASPENDING
from database import (
    create_tables, get_stats, export_to_csv, import_from_csv,
    get_connection, get_all_fetch_status, get_last_fetch,
)
from geo import distance_from_active_heroes, batch_geocode_missing


def cmd_fetch(source=None, resume=False):
    print("=" * 60)
    print("Veteran-Owned Business Database - Data Fetch")
    print("=" * 60)

    create_tables()

    if source is None or source == "sam":
        print("\n--- SAM.gov ---")
        from sam_gov import fetch_veteran_businesses
        result = fetch_veteran_businesses(resume=resume)
        print(f"SAM.gov: Fetched {result['total_fetched']}, "
              f"New: {result['new']}, Updated: {result['updated']}, "
              f"States completed: {len(result['states_completed'])}")

    if source is None or source == "usaspending":
        print("\n--- USAspending.gov ---")
        from usaspending import fetch_usaspending_veterans
        result = fetch_usaspending_veterans()
        print(f"USAspending: Fetched {result['total_fetched']}, "
              f"New: {result['new']}, Updated: {result['updated']}, "
              f"Unique recipients: {result['unique_recipients']}")

    # Geocode any records missing coordinates
    geocoded = batch_geocode_missing()
    if geocoded:
        print(f"\nGeocoded {geocoded} records missing coordinates.")

    print("\nDone!")
    _print_stats()


def cmd_status():
    create_tables()
    statuses = get_all_fetch_status()

    print("=" * 60)
    print("FETCH STATUS")
    print("=" * 60)

    if not statuses:
        print("No fetch history found. Run 'python main.py fetch' to pull data.")
        return

    for s in statuses:
        print(f"\n{s['source']}:")
        print(f"  Last completed: {s.get('completed_at', 'N/A')}")
        print(f"  Records fetched: {s.get('records_fetched', 0)}")
        print(f"  New: {s.get('records_new', 0)}")
        print(f"  Updated: {s.get('records_updated', 0)}")
        if s.get("error_message"):
            print(f"  Error: {s['error_message']}")

    # Also show per-source counts
    sam_last = get_last_fetch(SOURCE_SAM_GOV)
    usa_last = get_last_fetch(SOURCE_USASPENDING)

    print(f"\nSAM.gov last fetch: {sam_last['completed_at'] if sam_last else 'Never'}")
    print(f"USAspending last fetch: {usa_last['completed_at'] if usa_last else 'Never'}")


def cmd_import(csv_path):
    create_tables()

    source = input("Source name (e.g., 'VeteranOwnedBusiness.com'): ").strip()
    if not source:
        source = "CSV Import"

    count = import_from_csv(csv_path, source)
    print(f"\nImported {count} businesses.")

    # Geocode imported records missing coordinates
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, zip_code FROM businesses "
        "WHERE distance_miles IS NULL AND zip_code IS NOT NULL"
    )
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        dist = distance_from_active_heroes(row["zip_code"][:5])
        if dist is not None:
            cursor.execute(
                "UPDATE businesses SET distance_miles = ? WHERE id = ?",
                (round(dist, 1), row["id"]),
            )
            updated += 1
    conn.commit()
    conn.close()
    if updated:
        print(f"Calculated distances for {updated} records.")

    # Geocode lat/lon for any missing
    geocoded = batch_geocode_missing()
    if geocoded:
        print(f"Geocoded {geocoded} records missing coordinates.")

    _print_stats()


def cmd_export():
    create_tables()
    export_to_csv()


def cmd_stats():
    create_tables()
    _print_stats()


def cmd_search(term):
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT legal_business_name, dba_name, city, state, zip_code,
               business_type, distance_miles, phone, website, naics_descriptions
        FROM businesses
        WHERE legal_business_name LIKE ? OR dba_name LIKE ? OR naics_descriptions LIKE ?
        ORDER BY legal_business_name ASC
        LIMIT 50
    """, (f"%{term}%", f"%{term}%", f"%{term}%"))

    rows = cursor.fetchall()
    if not rows:
        print(f"No businesses found matching '{term}'")
        return

    print(f"\nFound {len(rows)} businesses matching '{term}':\n")
    for row in rows:
        name = row["legal_business_name"]
        dba = f" (DBA: {row['dba_name']})" if row["dba_name"] else ""
        loc = f"{row['city']}, {row['state']} {row['zip_code']}"
        dist = f"{row['distance_miles']}mi from HQ" if row["distance_miles"] else ""
        btype = row["business_type"] or ""
        print(f"  {name}{dba}")
        print(f"    {loc} | {dist} | {btype}")
        if row["naics_descriptions"]:
            descs = row["naics_descriptions"].split(", ")[:2]
            print(f"    Industry: {', '.join(descs)}")
        print()

    conn.close()


def _print_stats():
    stats = get_stats()
    print(f"\n{'=' * 40}")
    print(f"DATABASE SUMMARY")
    print(f"{'=' * 40}")
    print(f"Total businesses: {stats['total']}")

    if stats["by_type"]:
        print(f"\nBy certification type:")
        for t, c in stats["by_type"].items():
            print(f"  {t or 'Unknown'}: {c}")

    if stats["by_state"]:
        print(f"\nBy state:")
        for s, c in list(stats["by_state"].items())[:10]:
            print(f"  {s}: {c}")
        remaining = len(stats["by_state"]) - 10
        if remaining > 0:
            print(f"  ... and {remaining} more states")

    if stats["by_distance"]:
        print(f"\nBy distance from Active Heroes:")
        for d, c in stats["by_distance"].items():
            print(f"  {d}: {c}")

    if stats["by_source"]:
        print(f"\nBy data source:")
        for s, c in stats["by_source"].items():
            print(f"  {s}: {c}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "fetch":
        source = None
        resume = False
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--source" and i + 1 < len(sys.argv):
                source = sys.argv[i + 1].lower()
                i += 2
            elif sys.argv[i] == "--resume":
                resume = True
                i += 1
            else:
                i += 1
        cmd_fetch(source=source, resume=resume)
    elif command == "status":
        cmd_status()
    elif command == "import":
        if len(sys.argv) < 3:
            print("Usage: python main.py import <csv_file>")
            return
        cmd_import(sys.argv[2])
    elif command == "export":
        cmd_export()
    elif command == "stats":
        cmd_stats()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python main.py search <term>")
            return
        cmd_search(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
