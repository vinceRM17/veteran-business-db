"""
SQLite database setup and operations for veteran-owned business data.
"""

import sqlite3
import csv
from datetime import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uei TEXT,
            cage_code TEXT,
            legal_business_name TEXT NOT NULL,
            dba_name TEXT,
            physical_address_line1 TEXT,
            physical_address_line2 TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT DEFAULT 'USA',
            phone TEXT,
            email TEXT,
            website TEXT,
            business_type TEXT,
            naics_codes TEXT,
            naics_descriptions TEXT,
            service_branch TEXT,
            certification_date TEXT,
            registration_status TEXT,
            registration_expiration TEXT,
            entity_start_date TEXT,
            source TEXT,
            latitude REAL,
            longitude REAL,
            distance_miles REAL,
            date_added TEXT DEFAULT (datetime('now')),
            date_updated TEXT DEFAULT (datetime('now')),
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_uei ON businesses(uei)
        WHERE uei IS NOT NULL
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_state ON businesses(state)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_type ON businesses(business_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_distance ON businesses(distance_miles)
    """)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


def upsert_business(business: dict):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    if business.get("uei"):
        cursor.execute("SELECT id FROM businesses WHERE uei = ?", (business["uei"],))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE businesses SET
                    legal_business_name = ?,
                    dba_name = ?,
                    physical_address_line1 = ?,
                    physical_address_line2 = ?,
                    city = ?,
                    state = ?,
                    zip_code = ?,
                    phone = ?,
                    email = ?,
                    website = ?,
                    business_type = ?,
                    naics_codes = ?,
                    naics_descriptions = ?,
                    cage_code = ?,
                    registration_status = ?,
                    registration_expiration = ?,
                    entity_start_date = ?,
                    latitude = ?,
                    longitude = ?,
                    distance_miles = ?,
                    source = ?,
                    date_updated = ?
                WHERE uei = ?
            """, (
                business.get("legal_business_name"),
                business.get("dba_name"),
                business.get("physical_address_line1"),
                business.get("physical_address_line2"),
                business.get("city"),
                business.get("state"),
                business.get("zip_code"),
                business.get("phone"),
                business.get("email"),
                business.get("website"),
                business.get("business_type"),
                business.get("naics_codes"),
                business.get("naics_descriptions"),
                business.get("cage_code"),
                business.get("registration_status"),
                business.get("registration_expiration"),
                business.get("entity_start_date"),
                business.get("latitude"),
                business.get("longitude"),
                business.get("distance_miles"),
                business.get("source"),
                now,
                business["uei"],
            ))
            conn.commit()
            conn.close()
            return

    cursor.execute("""
        INSERT INTO businesses (
            uei, cage_code, legal_business_name, dba_name,
            physical_address_line1, physical_address_line2,
            city, state, zip_code, phone, email, website,
            business_type, naics_codes, naics_descriptions,
            registration_status, registration_expiration,
            entity_start_date, source,
            latitude, longitude, distance_miles,
            date_added, date_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        business.get("uei"),
        business.get("cage_code"),
        business.get("legal_business_name"),
        business.get("dba_name"),
        business.get("physical_address_line1"),
        business.get("physical_address_line2"),
        business.get("city"),
        business.get("state"),
        business.get("zip_code"),
        business.get("phone"),
        business.get("email"),
        business.get("website"),
        business.get("business_type"),
        business.get("naics_codes"),
        business.get("naics_descriptions"),
        business.get("registration_status"),
        business.get("registration_expiration"),
        business.get("entity_start_date"),
        business.get("source"),
        business.get("latitude"),
        business.get("longitude"),
        business.get("distance_miles"),
        now,
        now,
    ))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}
    cursor.execute("SELECT COUNT(*) FROM businesses")
    stats["total"] = cursor.fetchone()[0]

    cursor.execute("SELECT business_type, COUNT(*) FROM businesses GROUP BY business_type")
    stats["by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT state, COUNT(*) FROM businesses GROUP BY state ORDER BY COUNT(*) DESC")
    stats["by_state"] = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT source, COUNT(*) FROM businesses GROUP BY source")
    stats["by_source"] = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT ROUND(distance_miles/25)*25 as bracket, COUNT(*)
        FROM businesses
        WHERE distance_miles IS NOT NULL
        GROUP BY bracket ORDER BY bracket
    """)
    stats["by_distance"] = {f"{int(row[0])}-{int(row[0])+25}mi": row[1] for row in cursor.fetchall()}

    conn.close()
    return stats


def export_to_csv(output_path="veteran_businesses_export.csv"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            legal_business_name, dba_name, business_type,
            physical_address_line1, physical_address_line2,
            city, state, zip_code,
            phone, email, website,
            naics_codes, naics_descriptions,
            uei, cage_code,
            registration_status, registration_expiration,
            entity_start_date, distance_miles, source, notes
        FROM businesses
        ORDER BY distance_miles ASC, legal_business_name ASC
    """)

    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    conn.close()
    print(f"Exported {len(rows)} businesses to {output_path}")
    return len(rows)


def import_from_csv(csv_path, source_name="Manual Import"):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            business = {
                "legal_business_name": row.get("legal_business_name") or row.get("Business Name") or row.get("Name", ""),
                "dba_name": row.get("dba_name") or row.get("DBA", ""),
                "physical_address_line1": row.get("physical_address_line1") or row.get("Address", ""),
                "city": row.get("city") or row.get("City", ""),
                "state": row.get("state") or row.get("State", ""),
                "zip_code": row.get("zip_code") or row.get("Zip", "") or row.get("Zip Code", ""),
                "phone": row.get("phone") or row.get("Phone", ""),
                "email": row.get("email") or row.get("Email", ""),
                "website": row.get("website") or row.get("Website", "") or row.get("URL", ""),
                "business_type": row.get("business_type") or row.get("Type", "VOB"),
                "naics_codes": row.get("naics_codes") or row.get("NAICS", ""),
                "source": source_name,
                "notes": row.get("notes") or row.get("Notes", ""),
            }
            if business["legal_business_name"]:
                upsert_business(business)
                count += 1

    print(f"Imported {count} businesses from {csv_path}")
    return count


# --- Web app query helpers ---

def search_businesses(query="", state="", business_type="", max_distance=None,
                      sort_by="distance_miles", page=1, per_page=25):
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if query:
        conditions.append(
            "(legal_business_name LIKE ? OR dba_name LIKE ? OR naics_descriptions LIKE ? OR city LIKE ?)"
        )
        q = f"%{query}%"
        params.extend([q, q, q, q])

    if state:
        conditions.append("state = ?")
        params.append(state)

    if business_type:
        conditions.append("business_type = ?")
        params.append(business_type)

    if max_distance is not None:
        conditions.append("distance_miles <= ?")
        params.append(max_distance)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM businesses {where}", params)
    total = cursor.fetchone()[0]

    # Validate sort column
    allowed_sorts = {"distance_miles", "legal_business_name", "city", "state", "date_added"}
    if sort_by not in allowed_sorts:
        sort_by = "distance_miles"

    offset = (page - 1) * per_page
    cursor.execute(f"""
        SELECT * FROM businesses {where}
        ORDER BY {sort_by} ASC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "businesses": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


def get_business_by_id(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_map_data(max_distance=None):
    conn = get_connection()
    cursor = conn.cursor()

    if max_distance:
        cursor.execute("""
            SELECT id, legal_business_name, city, state, zip_code,
                   business_type, distance_miles, latitude, longitude
            FROM businesses
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND distance_miles <= ?
        """, (max_distance,))
    else:
        cursor.execute("""
            SELECT id, legal_business_name, city, state, zip_code,
                   business_type, distance_miles, latitude, longitude
            FROM businesses
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_states():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT state FROM businesses WHERE state IS NOT NULL ORDER BY state")
    states = [row[0] for row in cursor.fetchall()]
    conn.close()
    return states


def get_all_business_types():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT business_type FROM businesses WHERE business_type IS NOT NULL ORDER BY business_type")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return types


def delete_business(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM businesses WHERE id = ?", (business_id,))
    conn.commit()
    conn.close()


def update_business_notes(business_id, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET notes = ?, date_updated = ? WHERE id = ?",
        (notes, datetime.now().isoformat(), business_id),
    )
    conn.commit()
    conn.close()


def update_business_contact(business_id, phone, email, website):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET phone = ?, email = ?, website = ?, date_updated = ? WHERE id = ?",
        (phone, email, website, datetime.now().isoformat(), business_id),
    )
    conn.commit()
    conn.close()


def update_business_fields(business_id, fields: dict):
    conn = get_connection()
    cursor = conn.cursor()
    allowed = {
        "legal_business_name", "dba_name",
        "physical_address_line1", "physical_address_line2",
        "city", "state", "zip_code",
        "phone", "email", "website",
        "business_type", "naics_codes", "naics_descriptions",
        "service_branch", "notes",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        conn.close()
        return
    updates["date_updated"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [business_id]
    cursor.execute(f"UPDATE businesses SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_contact_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM businesses")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE email IS NOT NULL AND email != ''")
    has_email = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE website IS NOT NULL AND website != ''")
    has_website = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "has_phone": has_phone,
        "has_email": has_email,
        "has_website": has_website,
        "missing_all": total - max(has_phone, has_email, has_website) if total else 0,
    }
