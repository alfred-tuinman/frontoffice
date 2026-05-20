"""resolve_lookups.py — Fuzzy-match text values against DB lookup tables.

Usage (from Node via spawn):
    python resolve_lookups.py '{"country": "India", "currency": "Euro"}'

Returns JSON:
    {
      "countries_id":  { "id": 12,   "name": "India",  "score": 100, "status": "matched" },
      "currencies_id": { "id": 5,    "name": "Euro",   "score": 95,  "status": "matched" },
      "vehicles_id":   { "id": null, "name": null,     "score": 0,   "status": "unmatched" }
    }

status values:
    "matched"   — score >= THRESHOLD, safe to auto-fill
    "low"       — score < THRESHOLD, best guess returned but needs user confirmation
    "unmatched" — no candidates found at all (empty table etc.)
"""
import sys
import json
from rapidfuzz import process, fuzz
import pyodbc
import config

# Score threshold — above this we consider it a confident match
THRESHOLD = 80

# Maps the text field name (from PDF/form) to the lookup key in config.LOOKUP_TABLES
# and the DB column name to store the result in
FIELD_MAP = {
    "country":    ("countries",   "Countries_id"),
    "currency":   ("currencies",  "Currencies_id"),
    "vehicle":    ("vehicles",    "Vehicles_id"),
    "hotel_type": ("hotel_types", "HotelTypes_id"),
    "meal_plan":  ("meal_plans",  "MealPlans_id"),
    "start_city": ("start_cities","StartCities_id"),
    "end_city":   ("end_cities",  "EndCities_id"),
    "arr_city":   ("arr_cities",  "arr_cities_id"),
    "dep_city":   ("dep_cities",  "dep_cities_id"),
}


def get_connection():
    if config.DB_USER:
        cs = (f"DRIVER={{{config.DB_DRIVER}}};SERVER={config.DB_SERVER};"
              f"DATABASE={config.DB_NAME};UID={config.DB_USER};PWD={config.DB_PASS};")
    else:
        cs = (f"DRIVER={{{config.DB_DRIVER}}};SERVER={config.DB_SERVER};"
              f"DATABASE={config.DB_NAME};Trusted_Connection=yes;")
    return pyodbc.connect(cs, timeout=10)


def fetch_lookup(lookup_key: str) -> list[dict]:
    """Fetch all rows for a lookup key defined in config.LOOKUP_TABLES."""
    cfg = config.LOOKUP_TABLES.get(lookup_key)
    if not cfg:
        return []
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            where = f" WHERE {cfg['filter']}" if cfg.get('filter') else ""
            cur.execute(
                f"SELECT {cfg['id_col']}, {cfg['name_col']} "
                f"FROM {cfg['table']}{where}"
            )
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall() if r[1]]
    except Exception as e:
        print(f"⚠️  fetch_lookup({lookup_key}) error: {e}", file=sys.stderr)
        return []


def fuzzy_match(text: str, candidates: list[dict]) -> dict:
    """Return the best fuzzy match from candidates for the given text."""
    if not candidates or not text:
        return {"id": None, "name": None, "score": 0, "status": "unmatched"}

    names = [c["name"] for c in candidates]
    match = process.extractOne(text, names, scorer=fuzz.WRatio)

    if not match:
        return {"id": None, "name": None, "score": 0, "status": "unmatched"}

    matched_name, score, _ = match
    matched_item = next(c for c in candidates if c["name"] == matched_name)

    return {
        "id":     matched_item["id"],
        "name":   matched_item["name"],
        "score":  round(score),
        "status": "matched" if score >= THRESHOLD else "low",
    }


def resolve(text_values: dict) -> dict:
    """
    Resolve a dict of {field_name: text_value} to lookup IDs.
    Returns {db_column: {id, name, score, status, candidates?}}
    """
    results = {}

    for field, text in text_values.items():
        if field not in FIELD_MAP:
            continue

        lookup_key, db_col = FIELD_MAP[field]
        candidates = fetch_lookup(lookup_key)
        result = fuzzy_match(str(text).strip() if text else "", candidates)

        # For low/unmatched, include all candidates so the UI can show a dropdown
        if result["status"] in ("low", "unmatched"):
            result["candidates"] = [{"id": c["id"], "name": c["name"]} for c in candidates]

        results[db_col] = result

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('{"error": "No input provided"}')
        sys.exit(1)

    try:
        text_values = json.loads(sys.argv[1])
        result = resolve(text_values)
        print(json.dumps(result))
    except Exception as e:
        print(f'{{"error": "{str(e)}"}}')
        sys.exit(1)
