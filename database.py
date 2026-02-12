"""
SQLite database setup and operations for veteran-owned business data.
Supports both local SQLite and Turso cloud database (via HTTP pipeline API).
"""

import sqlite3
import csv
import re
from datetime import datetime
from difflib import SequenceMatcher
from config import DB_PATH, TURSO_URL, TURSO_AUTH_TOKEN

# ---------------------------------------------------------------------------
# Streamlit caching wrappers (graceful fallback outside Streamlit)
# ---------------------------------------------------------------------------
try:
    import streamlit as st
    _cache_short = st.cache_data(ttl=60)
    _cache_long = st.cache_data(ttl=300)
except Exception:
    def _cache_short(fn): return fn
    def _cache_long(fn): return fn


def _clear_caches():
    """Clear all cached query data (call after writes)."""
    try:
        for fn in (get_stats, get_contact_stats, get_grade_distribution,
                   get_tier_completeness_stats, get_all_fetch_status,
                   get_all_states, get_all_business_types, get_yelp_stats):
            fn.clear()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Turso compatibility wrapper  (HTTP pipeline API)
# ---------------------------------------------------------------------------
# Turso exposes an HTTP endpoint at /v2/pipeline that accepts SQL statements
# and returns typed JSON results.  The wrapper below translates that into the
# same interface callers already use (cursor / fetchone / fetchall / dict(row))
# so *no* other code in database.py or enrich.py needs to change.
# ---------------------------------------------------------------------------

import requests as _requests


def _turso_url(libsql_url):
    """Convert libsql:// URL to https:// for the HTTP pipeline endpoint."""
    return libsql_url.replace("libsql://", "https://")


def _encode_param(value):
    """Encode a Python value into a Turso Hrana typed-value dict."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    if isinstance(value, bytes):
        import base64
        return {"type": "blob", "base64": base64.b64encode(value).decode()}
    return {"type": "text", "value": str(value)}


def _decode_value(typed):
    """Decode a Turso Hrana typed-value dict back to a Python value."""
    t = typed.get("type")
    if t == "null":
        return None
    if t == "integer":
        return int(typed["value"])
    if t == "float":
        return typed["value"]
    if t == "blob":
        import base64
        return base64.b64decode(typed["base64"])
    # text and anything else
    return typed.get("value")


class _TursoRow:
    """Drop-in replacement for sqlite3.Row."""
    __slots__ = ("_columns", "_values", "_map")

    def __init__(self, columns, values):
        self._columns = tuple(columns)
        self._values = tuple(values)
        self._map = dict(zip(columns, values))

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._values[key]
        return self._map[key]

    def keys(self):
        return self._columns

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class _TursoCursor:
    """Mimics sqlite3.Cursor over the Turso HTTP pipeline API."""

    def __init__(self, api_url, headers):
        self._api_url = api_url
        self._headers = headers
        self._results = []
        self._description = None
        self.lastrowid = None
        self.rowcount = -1

    def execute(self, sql, params=None):
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [_encode_param(p) for p in params]

        body = {"requests": [
            {"type": "execute", "stmt": stmt},
            {"type": "close"},
        ]}

        resp = _requests.post(self._api_url, headers=self._headers, json=body)
        resp.raise_for_status()
        data = resp.json()

        result_entry = data["results"][0]
        if result_entry["type"] == "error":
            raise RuntimeError(result_entry["error"].get("message", "Turso query error"))

        result = result_entry["response"]["result"]
        columns = [c["name"] for c in result.get("cols", [])]

        decoded_rows = []
        for raw_row in result.get("rows", []):
            decoded_rows.append(
                _TursoRow(columns, [_decode_value(v) for v in raw_row])
            )

        self._description = [(c,) for c in columns] if columns else None
        self._results = decoded_rows
        self.lastrowid = result.get("last_insert_rowid")
        self.rowcount = result.get("affected_row_count", -1)
        return self

    def fetchone(self):
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self):
        rows = self._results
        self._results = []
        return rows

    @property
    def description(self):
        return self._description


class _TursoConnection:
    """Mimics sqlite3.Connection over the Turso HTTP pipeline API."""

    def __init__(self, url, auth_token):
        self._api_url = _turso_url(url) + "/v2/pipeline"
        self._headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    def cursor(self):
        return _TursoCursor(self._api_url, self._headers)

    def commit(self):
        pass  # Turso auto-commits each statement

    def close(self):
        pass

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass  # row_factory handled by _TursoRow wrapper


# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

def get_connection():
    """Return a database connection.

    If TURSO_URL is configured, returns a _TursoConnection that talks to
    Turso cloud via HTTP.  Otherwise falls back to a local sqlite3 connection.
    """
    if TURSO_URL and TURSO_AUTH_TOKEN:
        return _TursoConnection(TURSO_URL, TURSO_AUTH_TOKEN)

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

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_name_zip
        ON businesses(legal_business_name COLLATE NOCASE, zip_code)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            records_fetched INTEGER DEFAULT 0,
            records_new INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            error_message TEXT,
            details TEXT
        )
    """)

    _migrate_columns(conn)

    conn.commit()
    conn.close()


def _migrate_columns(conn):
    """Add columns introduced after the initial schema (idempotent)."""
    migrations = [
        ("businesses", "owner_name", "TEXT"),
        ("businesses", "linkedin_url", "TEXT"),
        ("businesses", "yelp_rating", "REAL"),
        ("businesses", "yelp_review_count", "INTEGER"),
        ("businesses", "yelp_url", "TEXT"),
    ]
    cursor = conn.cursor()
    for table, column, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass  # column already exists


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
            _clear_caches()
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
    _clear_caches()


# --- Fetch log helpers ---

def start_fetch_log(source):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO fetch_log (source, started_at, status) VALUES (?, ?, 'running')",
        (source, datetime.now().isoformat()),
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def complete_fetch_log(log_id, status="completed", records_fetched=0,
                       records_new=0, records_updated=0, error_msg=None, details=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fetch_log SET
            completed_at = ?, status = ?,
            records_fetched = ?, records_new = ?, records_updated = ?,
            error_message = ?, details = ?
        WHERE id = ?
    """, (
        datetime.now().isoformat(), status,
        records_fetched, records_new, records_updated,
        error_msg, details, log_id,
    ))
    conn.commit()
    conn.close()


def get_last_fetch(source):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM fetch_log
        WHERE source = ? AND status = 'completed'
        ORDER BY completed_at DESC LIMIT 1
    """, (source,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


@_cache_short
def get_all_fetch_status():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f1.* FROM fetch_log f1
        INNER JOIN (
            SELECT source, MAX(id) as max_id
            FROM fetch_log WHERE status = 'completed'
            GROUP BY source
        ) f2 ON f1.id = f2.max_id
        ORDER BY f1.source
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_running_fetch(source):
    """Return the most recent running fetch for a source, if any."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM fetch_log
        WHERE source = ? AND status = 'running'
        ORDER BY started_at DESC LIMIT 1
    """, (source,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- Cross-source dedup ---

_NAME_SUFFIXES = re.compile(
    r'\b(llc|inc|corp|co|ltd|incorporated|corporation|company|limited|l\.l\.c\.?|l\.p\.?)\b',
    re.IGNORECASE,
)
_PUNCTUATION = re.compile(r'[^\w\s]')
_WHITESPACE = re.compile(r'\s+')


def _normalize_business_name(name):
    if not name:
        return ""
    name = _NAME_SUFFIXES.sub("", name)
    name = _PUNCTUATION.sub("", name)
    name = _WHITESPACE.sub(" ", name).strip().lower()
    return name


def upsert_business_cross_source(business: dict):
    """Insert or update a business using cross-source deduplication.

    Priority:
    1. Match by UEI (exact)
    2. Match by normalized name + zip (fuzzy, threshold 0.85)
    3. Insert new record

    On update: only overwrite empty fields; append source to comma-separated source field.
    Returns: 'new', 'updated', or 'unchanged'
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    existing = None

    # 1. Try UEI match
    uei = business.get("uei")
    if uei:
        cursor.execute("SELECT * FROM businesses WHERE uei = ?", (uei,))
        row = cursor.fetchone()
        if row:
            existing = dict(row)

    # 2. Try fuzzy name + zip match
    if existing is None:
        incoming_name = _normalize_business_name(business.get("legal_business_name", ""))
        incoming_zip = (business.get("zip_code") or "")[:5]

        if incoming_name and incoming_zip:
            cursor.execute(
                "SELECT * FROM businesses WHERE zip_code LIKE ?",
                (incoming_zip + "%",),
            )
            candidates = [dict(r) for r in cursor.fetchall()]
            best_ratio = 0.0
            best_match = None
            for cand in candidates:
                cand_name = _normalize_business_name(cand.get("legal_business_name", ""))
                ratio = SequenceMatcher(None, incoming_name, cand_name).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = cand
            if best_ratio >= 0.85 and best_match is not None:
                existing = best_match

    if existing:
        # Merge: only overwrite empty fields
        updates = {}
        merge_fields = [
            "uei", "cage_code", "dba_name",
            "physical_address_line1", "physical_address_line2",
            "city", "state", "zip_code", "phone", "email", "website",
            "business_type", "naics_codes", "naics_descriptions",
            "registration_status", "registration_expiration",
            "entity_start_date", "latitude", "longitude", "distance_miles",
        ]
        for field in merge_fields:
            new_val = business.get(field)
            old_val = existing.get(field)
            if new_val and not old_val:
                updates[field] = new_val

        # Append source
        new_source = business.get("source", "")
        old_source = existing.get("source", "")
        if new_source and new_source not in (old_source or ""):
            merged_source = f"{old_source}, {new_source}" if old_source else new_source
            updates["source"] = merged_source

        # Append notes
        new_notes = business.get("notes", "")
        old_notes = existing.get("notes", "")
        if new_notes and new_notes not in (old_notes or ""):
            merged_notes = f"{old_notes}; {new_notes}" if old_notes else new_notes
            updates["notes"] = merged_notes

        if updates:
            updates["date_updated"] = now
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [existing["id"]]
            cursor.execute(f"UPDATE businesses SET {set_clause} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return "updated"
        else:
            conn.close()
            return "unchanged"
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO businesses (
                uei, cage_code, legal_business_name, dba_name,
                physical_address_line1, physical_address_line2,
                city, state, zip_code, phone, email, website,
                business_type, naics_codes, naics_descriptions,
                registration_status, registration_expiration,
                entity_start_date, source,
                latitude, longitude, distance_miles,
                date_added, date_updated, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            now, now,
            business.get("notes"),
        ))
        conn.commit()
        conn.close()
        return "new"


@_cache_short
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
            owner_name, service_branch, linkedin_url,
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
            "(legal_business_name LIKE ? OR dba_name LIKE ? OR naics_descriptions LIKE ? OR city LIKE ? OR owner_name LIKE ?)"
        )
        q = f"%{query}%"
        params.extend([q, q, q, q, q])

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


def export_search_to_csv(query="", state="", business_type="", max_distance=None):
    """Return all matching businesses (no pagination) for CSV export."""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if query:
        conditions.append(
            "(legal_business_name LIKE ? OR dba_name LIKE ? OR naics_descriptions LIKE ? OR city LIKE ? OR owner_name LIKE ?)"
        )
        q = f"%{query}%"
        params.extend([q, q, q, q, q])

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

    cursor.execute(f"""
        SELECT * FROM businesses {where}
        ORDER BY distance_miles ASC, legal_business_name ASC
    """, params)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_business_by_id(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_businesses_by_ids(ids):
    if not ids:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ids)
    cursor.execute(
        f"SELECT * FROM businesses WHERE id IN ({placeholders}) ORDER BY distance_miles ASC, legal_business_name ASC",
        list(ids),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_map_data(max_distance=None):
    conn = get_connection()
    cursor = conn.cursor()

    _map_cols = """id, legal_business_name, dba_name, city, state, zip_code,
                   business_type, distance_miles, latitude, longitude,
                   phone, email, website,
                   uei, cage_code, registration_status, naics_codes,
                   naics_descriptions, registration_expiration,
                   entity_start_date, source"""

    if max_distance:
        cursor.execute(f"""
            SELECT {_map_cols}
            FROM businesses
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND distance_miles <= ?
        """, (max_distance,))
    else:
        cursor.execute(f"""
            SELECT {_map_cols}
            FROM businesses
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_businesses_with_coords():
    """Fetch all businesses that have coordinates, for custom-location search."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM businesses
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@_cache_long
def get_all_states():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT state FROM businesses WHERE state IS NOT NULL ORDER BY state")
    states = [row[0] for row in cursor.fetchall()]
    conn.close()
    return states


@_cache_long
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
    _clear_caches()


def update_business_notes(business_id, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET notes = ?, date_updated = ? WHERE id = ?",
        (notes, datetime.now().isoformat(), business_id),
    )
    conn.commit()
    conn.close()
    _clear_caches()


def update_business_contact(business_id, phone, email, website):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET phone = ?, email = ?, website = ?, date_updated = ? WHERE id = ?",
        (phone, email, website, datetime.now().isoformat(), business_id),
    )
    conn.commit()
    conn.close()
    _clear_caches()


def update_business_fields(business_id, fields: dict):
    conn = get_connection()
    cursor = conn.cursor()
    allowed = {
        "legal_business_name", "dba_name",
        "physical_address_line1", "physical_address_line2",
        "city", "state", "zip_code",
        "phone", "email", "website",
        "business_type", "naics_codes", "naics_descriptions",
        "service_branch", "owner_name", "linkedin_url", "notes",
        "yelp_rating", "yelp_review_count", "yelp_url",
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
    _clear_caches()


@_cache_short
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


@_cache_short
def get_grade_distribution():
    """Compute confidence grade distribution across all businesses.

    Uses the rule-based grading: checks UEI, location, contact, industry
    presence to assign A/B/C/D/F grades via SQL for performance.
    Returns dict like {"A": 150, "B": 3000, "C": 1200, "D": 50, "F": 10}.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Count filled fields out of the 17 scored fields, compute percentage,
    # then bucket into grades: A>=70%, B>=50%, C>=30%, D>=15%, F<15%
    cursor.execute("""
        SELECT
            CASE
                WHEN pct >= 70 THEN 'A'
                WHEN pct >= 50 THEN 'B'
                WHEN pct >= 30 THEN 'C'
                WHEN pct >= 15 THEN 'D'
                ELSE 'F'
            END as grade,
            COUNT(*) as cnt
        FROM (
            SELECT ROUND(
                (
                    (CASE WHEN legal_business_name IS NOT NULL AND legal_business_name != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN dba_name IS NOT NULL AND dba_name != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN business_type IS NOT NULL AND business_type != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN physical_address_line1 IS NOT NULL AND physical_address_line1 != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN city IS NOT NULL AND city != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN state IS NOT NULL AND state != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN zip_code IS NOT NULL AND zip_code != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN website IS NOT NULL AND website != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN naics_codes IS NOT NULL AND naics_codes != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN naics_descriptions IS NOT NULL AND naics_descriptions != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN uei IS NOT NULL AND uei != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN cage_code IS NOT NULL AND cage_code != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN registration_status IS NOT NULL AND registration_status != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN owner_name IS NOT NULL AND owner_name != '' THEN 1 ELSE 0 END)
                  + (CASE WHEN service_branch IS NOT NULL AND service_branch != '' THEN 1 ELSE 0 END)
                ) * 100.0 / 17
            ) as pct
            FROM businesses
        )
        GROUP BY grade
        ORDER BY grade
    """)
    result = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    # Ensure all grades present
    for g in ("A", "B", "C", "D", "F"):
        result.setdefault(g, 0)
    return result


@_cache_short
def get_tier_completeness_stats():
    """Return per-tier, per-field completeness percentages.

    Returns dict keyed by tier_key, each containing:
      - filled: average filled fields across all businesses
      - total: total fields in tier
      - fields: {field_name: pct_non_null}
    """
    from branding import TRUST_TIERS

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM businesses")
    total_biz = cursor.fetchone()[0]
    if total_biz == 0:
        conn.close()
        return {}

    result = {}
    for tier_key, tier_info in TRUST_TIERS.items():
        fields = tier_info["fields"]
        field_pcts = {}
        total_filled_pct = 0.0

        for field in fields:
            cursor.execute(
                f"SELECT COUNT(*) FROM businesses WHERE [{field}] IS NOT NULL AND [{field}] != ''",
            )
            count = cursor.fetchone()[0]
            pct = round(count / total_biz * 100)
            field_pcts[field] = pct
            total_filled_pct += pct

        avg_pct = round(total_filled_pct / len(fields)) if fields else 0
        # filled / total as average counts
        avg_filled = round(avg_pct / 100 * len(fields), 1)

        result[tier_key] = {
            "filled": avg_filled,
            "total": len(fields),
            "pct": avg_pct,
            "fields": field_pcts,
        }

    conn.close()
    return result


@_cache_short
def get_yelp_stats():
    """Return Yelp enrichment stats: total, has_rating, missing."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM businesses")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM businesses WHERE yelp_rating IS NOT NULL")
    has_rating = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "has_rating": has_rating,
        "missing": total - has_rating,
    }
