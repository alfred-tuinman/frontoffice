# converter.py — completely rewritten as a rule-based parser:

## Booking reference extracted with a simple regex
## Guest names parsed by splitting title / name / nationality / DOB from each guest line
## Table rows parsed by anchoring to the DD.MM.YYYY DayName DayName pattern at the end of each line
## Hotel-listing rows identified and used to map cities across date ranges — with a two-pass system so the hotel that starts on a given day always takes priority over one continuing from a previous night
## Full date range is generated from arrival to departure, with leisure days (no PDF entries) automatically filled as "Day at leisure in [City]"
## Nights calculated directly from the date difference, not row count

# Install is now just:
pip install flask pdfplumber openpyxl pyodbc waitress
start.bat and config.py.

The parser is tuned to the erlebe PDF format. If you ever receive PDFs from a different operator with a different layout, let me know and we can adjust the regex patterns.