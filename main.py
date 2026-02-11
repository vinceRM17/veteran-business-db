#!/usr/bin/env python3
"""
Veteran-Owned Business Database Pipeline

Builds a database of every veteran-owned business within 100 miles
of Active Heroes (1022 Ridgeview Dr, Shepherdsville, KY 40165).

Data sources:
  - SAM.gov Entity Management API (automated)
  - CSV import (manual data from VeteranOwnedBusiness.com, VetBiz, etc.)

Usage:
  python main.py fetch       # Pull from SAM.gov API
  python main.py import FILE # Import a CSV file
  python main.py export      # Export database to CSV
  python main.py stats       # Show database statistics
  python main.py search TERM # Search by business name
"""

import sys
import sqlite3

from config import DB_PATH, SEARCH_RADIUS_MILES, ACTIVE_HEROES_ZIP
from database import create_tables, get_stats, export_to_csv, import_from_csv, get_connection
from sam_gov import fetch_veteran_businesses
from geo import distance_from_active_heroes


def cmd_fetch():
    print("=" * 60)
    print("Veteran-Owned Business Database - SAM.gov Fetch")
    print(f"Center: Active Heroes, Shepherdsville KY ({ACTIVE_HEROES_ZIP})")
    print(f"Radius: {SEARCH_RADIUS_MILES} miles")
    print("States: KY, IN, OH, TN, WV")
    print("=" * 60)

    create_tables()
    total = fetch_veteran_businesses()
    print(f"\nDone! {total} businesses added/updated.")
    _print_stats()


def cmd_import(csv_path):
    create_tables()

    source = input("Source name (e.g., 'VeteranOwnedBusiness.com'): ").strip()
    if not source:
        source = "Manual Import"

    count = import_from_csv(csv_path, source)
    print(f"\nImported {count} businesses.")

    # Calculate distances for imported records missing them
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, zip_code FROM businesses WHERE distance_miles IS NULL AND zip_code IS NOT NULL")
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        dist = distance_from_active_heroes(row["zip_code"][:5])
        if dist is not None:
            if dist <= SEARCH_RADIUS_MILES:
                cursor.execute("UPDATE businesses SET distance_miles = ?, latitude = NULL, longitude = NULL WHERE id = ?",
                               (round(dist, 1), row["id"]))
                updated += 1
            else:
                cursor.execute("DELETE FROM businesses WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    if updated:
        print(f"Calculated distances for {updated} records.")

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
        ORDER BY distance_miles ASC
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
        dist = f"{row['distance_miles']}mi" if row["distance_miles"] else "?mi"
        btype = row["business_type"] or ""
        print(f"  {name}{dba}")
        print(f"    {loc} | {dist} | {btype}")
        if row["naics_descriptions"]:
            # Show first 2 NAICS descriptions
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
        for s, c in stats["by_state"].items():
            print(f"  {s}: {c}")

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
        cmd_fetch()
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
