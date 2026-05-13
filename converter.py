"""
converter.py — Rule-based PDF parser for erlebe-fernreisen booking PDFs.
No external API required — all parsing done locally via pdfplumber + regex.
"""

import re
from datetime import datetime, timedelta
from collections import defaultdict

import pdfplumber

# ── Regex patterns ─────────────────────────────────────────────────────────────

_DAYS = r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday'

BOOKING_REF_RE = re.compile(r'booking\s+number\s+(\S+)', re.IGNORECASE)

# Guest line: "Mr/Mrs First(s) Last Nationality DD.MM.YYYY ..."
GUEST_RE = re.compile(
    r'^\s*(Mr|Mrs|Ms|Dr)\.?\s+(.+?)\s+(\d{2}\.\d{2}\.\d{4})',
    re.IGNORECASE | re.MULTILINE,
)

# Table row: "description N DD.MM.YYYY DD.MM.YYYY DayName DayName"
TABLE_ROW_RE = re.compile(
    r'^(.*?)\s+(\d{1,2})\s+'
    r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+'
    r'(' + _DAYS + r')\s+(' + _DAYS + r')',
    re.IGNORECASE | re.MULTILINE,
)

# ── Date helpers ───────────────────────────────────────────────────────────────

def _parse_date(s: str):
    return datetime.strptime(s, '%d.%m.%Y').date()

def _fmt_date(d) -> str:
    return d.strftime('%d.%m.%Y')

def _day_name(d) -> str:
    return d.strftime('%A')

def _date_range(start_str: str, end_str: str):
    """Yield all dates from start to end inclusive as date objects."""
    cur = _parse_date(start_str)
    end = _parse_date(end_str)
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

# ── Guest name parser ──────────────────────────────────────────────────────────

_TWO_WORD_NATS = {'south african', 'new zealand', 'hong kong', 'saudi arabian'}

def _parse_name_nationality(raw: str) -> tuple[str, str]:
    """
    'First(s) Last Nationality' → (first_names, last_name).
    Drops the trailing nationality word(s), then splits name.
    """
    words = raw.strip().split()
    if len(words) >= 3 and ' '.join(words[-2:]).lower() in _TWO_WORD_NATS:
        words = words[:-2]
    elif len(words) >= 2:
        words = words[:-1]
    if not words:
        return raw, ''
    return ' '.join(words[:-1]), words[-1]

# ── Row classification helpers ─────────────────────────────────────────────────

def _extract_city(desc: str) -> str | None:
    """
    Return the city name if this row is a hotel-listing row, else None.

    Patterns handled:
      "Hotel Shimla: 1. Willow Banks"    → Shimla
      "Delhi: 1 Deventure..."            → Delhi
      "Dharamsala 1: Norling..."         → Dharamsala   (option-N in city ref)
      "Corbett: Hotel Tiger Camp"        → Corbett
    """
    # "Hotel [City]: ..."
    m = re.match(r'^Hotel\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:\s+\d+)?\s*:', desc)
    if m:
        return m.group(1).title()
    # "[City] [N]: [digit or Hotel]"  — standard numbered-option hotel rows
    m = re.match(
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:\s+\d+)?\s*:\s*'
        r'(?:\d+[\.\:\s]|Hotel\s)',
        desc, re.IGNORECASE,
    )
    if m:
        return m.group(1).title()
    # "[City] N: [any text]"  — e.g. "Dharamsala 1: Norling Guest House..."
    m = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+\d+\s*:', desc)
    if m:
        return m.group(1).title()
    return None


def _extract_hotel_name(desc: str) -> str:
    """Extract the first hotel-option name from a hotel-listing description."""
    # Strip city/Hotel prefix up to the colon
    stripped = re.sub(r'^(?:Hotel\s+)?\w+(?:\s+\d+)?\s*(?:\s+\d+)?\s*:\s*', '', desc).strip()
    # Strip leading option number  "1. " / "1 " / "1: "
    stripped = re.sub(r'^\d+[\.\:\s]+', '', stripped).strip()
    # Take up to the next numbered option "2." / "2 "
    m = re.match(r'(.+?)(?:\s+\d+[\.\:])', stripped)
    return m.group(1).strip() if m else stripped.strip()


_SECTION_TRANSPORT = ('flight', 'train', 'transfer', 'drive', 'transport', 'daytrain', 'coach')

def _is_section_header(row: dict) -> bool:
    """
    Section headers span multiple dates and summarise a segment.
    Multi-day transport rows are NOT section headers.
    """
    if row['start_date'] == row['end_date']:
        return False
    return not any(w in row['desc'].lower() for w in _SECTION_TRANSPORT)


_SKIP_PHRASES = ('client information only', 'international flight')

def _clean_activity(desc: str) -> str:
    desc = desc.strip().rstrip('.')
    return (desc[0].upper() + desc[1:] + '.') if desc else ''

# ── Main parser ────────────────────────────────────────────────────────────────

def parse_pdf_rules(raw_text: str) -> dict:

    # 1. Booking reference ─────────────────────────────────────────────────────
    m = BOOKING_REF_RE.search(raw_text)
    booking_ref = m.group(1) if m else ''

    # 2. Guests ────────────────────────────────────────────────────────────────
    guests, seen = [], set()
    for m in GUEST_RE.finditer(raw_text):
        title    = m.group(1).strip()
        name_nat = m.group(2).strip()
        first, last = _parse_name_nationality(name_nat)
        key = (title.lower(), last.lower())
        if key not in seen:
            seen.add(key)
            guests.append({'title': title, 'first_name': first, 'last_name': last})

    # 3. Parse table rows ──────────────────────────────────────────────────────
    rows = []
    for m in TABLE_ROW_RE.finditer(raw_text):
        desc = m.group(1).strip()
        if not desc:
            continue
        if any(s in desc.lower() for s in _SKIP_PHRASES):
            continue
        rows.append({
            'desc':       desc,
            'daynum':     int(m.group(2)),
            'start_date': m.group(3),
            'end_date':   m.group(4),
            'day_from':   m.group(5),
        })

    # 4. Index rows by start date ──────────────────────────────────────────────
    date_rows: dict[str, list] = defaultdict(list)
    for row in rows:
        date_rows[row['start_date']].append(row)

    # 5. Build hotel_by_date ───────────────────────────────────────────────────
    # Two passes so that a hotel starting today always wins over one continuing.
    hotel_by_date: dict[str, tuple] = {}

    # Pass A: fill continuation dates (lower priority — first-come wins)
    for row in rows:
        city = _extract_city(row['desc'])
        if not city:
            continue
        hotel_name = _extract_hotel_name(row['desc'])
        for d in _date_range(row['start_date'], row['end_date']):
            ds = _fmt_date(d)
            if ds not in hotel_by_date:
                hotel_by_date[ds] = (city, hotel_name)

    # Pass B: overwrite with the hotel that actually starts on each date
    for row in rows:
        city = _extract_city(row['desc'])
        if city:
            hotel_by_date[row['start_date']] = (city, _extract_hotel_name(row['desc']))

    # 6. Determine full date range (arrival → departure) ───────────────────────
    # Use the earliest and latest dates that appear in any row.
    all_row_dates = [_parse_date(r['start_date']) for r in rows] + \
                    [_parse_date(r['end_date'])   for r in rows]
    if not all_row_dates:
        return {'quotation': {}, 'guests': guests, 'itinerary': []}

    # Arrival = first date with actual rows (not just hotel coverage)
    # Departure = last row start date
    arrival_date   = min(_parse_date(d) for d in date_rows)
    departure_date = max(_parse_date(d) for d in date_rows)
    nights         = (departure_date - arrival_date).days

    # Build the complete date sequence including leisure days with no rows
    full_range = list(_date_range(_fmt_date(arrival_date), _fmt_date(departure_date)))

    # 7. Build itinerary ───────────────────────────────────────────────────────
    itinerary = []
    for i, d in enumerate(full_range):
        date_str = _fmt_date(d)
        is_first = (i == 0)
        is_last  = (i == len(full_range) - 1)

        city, hotel_name = hotel_by_date.get(date_str, (None, None))
        day_rows = date_rows.get(date_str, [])

        # Fallback city from non-hotel activity description
        if not city:
            for row in day_rows:
                m2 = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s', row['desc'])
                if m2 and m2.group(1).lower() not in (
                    'transfer', 'private', 'half', 'afternoon', 'the',
                    'intercity', 'daytrain', 'corbett', 'train',
                ):
                    city = m2.group(1).title()
                    break

        # Does a hotel START today?
        hotel_starts_today = any(
            _extract_city(r['desc']) and r['start_date'] == date_str
            for r in day_rows
        )

        # ── Build description ─────────────────────────────────────────────────
        parts = []

        if is_first:
            parts.append(f"Arrive in {city or 'destination'} by international flight.")

        if not day_rows:
            # Leisure / rest day — no entries in the PDF
            parts.append(f"Day at leisure in {city or 'destination'}.")
        else:
            for row in day_rows:
                if _extract_city(row['desc']):    # hotel listing → city already captured
                    continue
                if _is_section_header(row):        # segment summary → skip
                    continue
                parts.append(_clean_activity(row['desc']))

        if hotel_starts_today and hotel_name:
            parts.append(f"Stay at {hotel_name}.")

        if is_last:
            parts.append("Transfer to airport for international flight home.")

        description = ' '.join(p for p in parts if p) or f"Day in {city or 'transit'}."

        itinerary.append({
            'sr_no':       i + 1,
            'day_name':    _day_name(d),
            'date':        date_str,
            'destination': city or 'In Transit',
            'description': description,
        })

    # 8. Quotation fields ──────────────────────────────────────────────────────
    num_pax   = len(guests)
    principal = guests[0] if guests else {}
    principal_name = (
        f"{principal.get('title', '')}. "
        f"{principal.get('first_name', '')} "
        f"{principal.get('last_name', '')}"
    ).strip('. ')

    raw_lower = raw_text.lower()

    quotation = {
        'QuotationRef':    booking_ref,
        'PaxName':         principal.get('last_name', ''),
        'PaxFirstName':    principal.get('first_name', ''),
        'PrincipalClient': principal_name,
        'Email':           None,
        'NumPax':          num_pax,
        'NumSingles':      1 if num_pax == 1 else 0,
        'NumDoubles':      1 if num_pax == 2 else 0,
        'NumTwins':        0,
        'NumTriples':      1 if num_pax == 3 else 0,
        'DateOfArrival':   _fmt_date(arrival_date),
        'DateOfDeparture': _fmt_date(departure_date),
        'StartDate':       _fmt_date(arrival_date),
        'EndDate':         _fmt_date(departure_date),
        'Nights':          nights,
        'FlightNo':        None,
        'FlightNoDept':    None,
        'PlaceFrom':       None,
        'PlaceTo':         None,
        'ETA':             None,
        'ETD':             None,
        'Guide':           'guide' in raw_lower,
        'EntranceFees':    'entrance fee' in raw_lower,
        'TourCode':        None,
        'Comment':         None,
    }

    return {'quotation': quotation, 'guests': guests, 'itinerary': itinerary}


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text(layout=True) for p in pdf.pages]
    return '\n\n--- PAGE BREAK ---\n\n'.join(t for t in pages if t)


def parse_with_claude(raw_text: str) -> dict:
    """Name kept for app.py compatibility — calls local rule-based parser."""
    return parse_pdf_rules(raw_text)
