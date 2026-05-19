"""db.py — MSSQL connection, lookups, and quotation insert."""
import pyodbc
from datetime import datetime, date
import config


def get_connection():
    if config.DB_USER:
        cs = (f"DRIVER={{{config.DB_DRIVER}}};SERVER={config.DB_SERVER};"
              f"DATABASE={config.DB_NAME};UID={config.DB_USER};PWD={config.DB_PASS};")
    else:
        cs = (f"DRIVER={{{config.DB_DRIVER}}};SERVER={config.DB_SERVER};"
              f"DATABASE={config.DB_NAME};Trusted_Connection=yes;")
    return pyodbc.connect(cs, timeout=10)


def get_all_lookups() -> dict:
    """Return {key: [{id, name}, ...]} for every lookup table in config."""
    results = {}
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            for key, cfg in config.LOOKUP_TABLES.items():
                try:
                    where = f" WHERE {cfg['filter']}" if cfg.get('filter') else ""
                    cur.execute(
                        f"SELECT {cfg['id_col']}, {cfg['name_col']} "
                        f"FROM {cfg['table']}{where} "
                        f"ORDER BY {cfg['name_col']}"
                    )
                    results[key] = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
                except Exception:
                    results[key] = []   # table / column mismatch — staff still sees blank dropdown
    except Exception:
        results = {k: [] for k in config.LOOKUP_TABLES}
    return results


def get_next_quotation_no() -> dict:
    """Return the next Quotations_id, QuotationNo, and current year from the DB."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ISNULL(MAX(Quotations_id),0)+1, "
                "       ISNULL(MAX(QuotationNo),0)+1, "
                "       YEAR(GETDATE()) "
                "FROM quotations"
            )
            row = cur.fetchone()
            return {
                "Quotations_id":  row[0],
                "QuotationNo":    row[1],
                "QuotationYearRef": row[2],
            }
    except Exception:
        return {"Quotations_id": None, "QuotationNo": None, "QuotationYearRef": datetime.now().year}


# Columns we INSERT (Quotations_id is NOT an identity col — must be supplied)
_INSERT_COLS = [
    "Quotations_id",
    "QuotationRef","PaxName","Email","EconomyPax","TimePax","NumPax",
    "NumSingles","NumDoubles","StartDate","QuotationDate","QuotationNo",
    "QuotationYearRef","MealPlans_id","Guide","Tickets_id","Nights",
    "EntranceFees","DateOfArrival","FlightNo","PlaceFrom","PaxFirstName",
    "NumTriples","CarHireAgents_id","CarHireCities_id","ETA","HotelTypes_id",
    "Reference","Countries_id","Currencies_id","ExtraBed","DateOfDeparture",
    "FlightNoDept","PlaceTo","ETD","PrincipalAgents_id","TourCode","Vehicles_id",
    "domestic","StartCities_id","TourNo","Managers_id","AdmUsers_id","NumTwins",
    "DeptDomestic","EndCities_id","EndDate","Confirmed","Consultants_id",
    "Comment","PrincipalClient","BookingRecdDate","BookingEntryDate",
    "BasicRate","BasicAmt","ServiceTaxPerc","ServiceTaxAmt","QuotationAmt",
    "AdvanceAmt","ExtraMargin","DueDate",
]


def insert_quotation(fields: dict) -> int:
    """Insert into quotations; return new Quotations_id."""

    cols, vals = [], []
    for col in _INSERT_COLS:
        v = fields.get(col)
        if v is not None and v != "":
            cols.append(col)
            vals.append(v)

    sql = (f"INSERT INTO quotations ({', '.join(cols)}) "
           f"VALUES ({', '.join(['?']*len(vals))})")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
        return fields['Quotations_id']


# itineraries columns we INSERT (itineraries_id is NOT an identity col — must be supplied)
_ITIN_COLS = [
    "itineraries_id",
    "departuredate", "masters_id", "invoices_id", "sessionid",
    "leadname", "arr_cities_id", "arrtime", "dep_cities_id",
    "depdate", "deptime", "countries_id", "flightbooked",
    "pax", "singles", "doubles", "triples", "twins",
    "resident", "web_users_id", "TourLeader", "TourLeaderCountries_id",
    "IssuedOn", "Status", "IssuedBy", "TourRef", "Quotations_id",
]

def get_next_itinerary_id() -> int:
    """Return MAX(itineraries_id)+1 from the itineraries table."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ISNULL(MAX(itineraries_id),0)+1 FROM itineraries")
            return cur.fetchone()[0]
    except Exception:
        return None

def insert_itinerary(fields: dict) -> int:
    """Insert into itineraries linked to the new Quotations_id; return itineraries_id."""
    # itineraries_id is NOT an identity col — generate it if not supplied
    if not fields.get('itineraries_id'):
        fields['itineraries_id'] = get_next_itinerary_id()

    cols, vals = [], []
    for col in _ITIN_COLS:
        v = fields.get(col)
        if v is not None and v != "":
            cols.append(col)
            vals.append(v)

    sql = (f"INSERT INTO itineraries ({', '.join(cols)}) "
           f"VALUES ({', '.join(['?']*len(vals))})")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
        return fields['itineraries_id']


def find_by_quotation_ref(quotation_ref: str) -> dict | None:
    """
    Return Quotations_id and itineraries_id for an existing QuotationRef, or None.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT Quotations_id, QuotationRef, PrincipalClient "
                "FROM quotations WHERE QuotationRef = ?",
                [quotation_ref]
            )
            row = cur.fetchone()
            if not row:
                return None
            result = {
                "Quotations_id":  row[0],
                "QuotationRef":   row[1],
                "PrincipalClient": row[2],
            }
            cur.execute(
                "SELECT itineraries_id FROM itineraries WHERE Quotations_id = ?",
                [row[0]]
            )
            itin = cur.fetchone()
            result["itineraries_id"] = itin[0] if itin else None
            return result
    except Exception:
        return None


def find_existing(quotations_id: int) -> dict | None:
    """
    Return the quotation row and its linked itineraries row (if any)
    for a given Quotations_id, or None if not found.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT Quotations_id, QuotationRef, PrincipalClient "
                "FROM quotations WHERE Quotations_id = ?",
                [quotations_id]
            )
            row = cur.fetchone()
            if not row:
                return None
            result = {
                "Quotations_id":  row[0],
                "QuotationRef":   row[1],
                "PrincipalClient": row[2],
            }
            # Look for a linked itinerary row
            cur.execute(
                "SELECT itineraries_id FROM itineraries "
                "WHERE Quotations_id = ?",
                [quotations_id]
            )
            itin = cur.fetchone()
            result["itineraries_id"] = itin[0] if itin else None
            return result
    except Exception:
        return None


def find_itinerary_by_quotation(quotations_id: int, tour_ref: str = None) -> dict | None:
    """
    Return the itinerary linked to a Quotations_id.
    Optionally filter by TourRef if provided.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            if tour_ref:
                cur.execute(
                    "SELECT itineraries_id, Quotations_id, TourRef FROM itineraries "
                    "WHERE Quotations_id = ? AND TourRef = ?",
                    [quotations_id, tour_ref]
                )
            else:
                cur.execute(
                    "SELECT itineraries_id, Quotations_id, TourRef FROM itineraries "
                    "WHERE Quotations_id = ?",
                    [quotations_id]
                )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "itineraries_id": row[0],
                "Quotations_id": row[1],
                "TourRef": row[2],
            }
    except Exception:
        return None


def update_quotation(quotations_id: int, fields: dict) -> int:
    """UPDATE quotations WHERE Quotations_id = ?; return the same id."""
    cols, vals = [], []
    for col in _INSERT_COLS:
        v = fields.get(col)
        if v is not None and v != "":
            cols.append(f"{col} = ?")
            vals.append(v)

    if not cols:
        return quotations_id

    vals.append(quotations_id)
    sql = f"UPDATE quotations SET {', '.join(cols)} WHERE Quotations_id = ?"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
    return quotations_id


def update_itinerary(itineraries_id: int, fields: dict) -> int:
    """UPDATE itineraries WHERE itineraries_id = ?; return the same id."""
    cols, vals = [], []
    for col in _ITIN_COLS:
        v = fields.get(col)
        if v is not None and v != "":
            cols.append(f"{col} = ?")
            vals.append(v)

    if not cols:
        return itineraries_id

    vals.append(itineraries_id)
    sql = f"UPDATE itineraries SET {', '.join(cols)} WHERE itineraries_id = ?"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
    return itineraries_id