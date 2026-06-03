# PDF Booking App — Riksja, erlebe-fernreisen etc

A Node.js/Express web application that extracts booking data from PDF itineraries and generates professional Excel workbooks for database import.

## Features

- **PDF Upload**: Drag-and-drop interface for booking PDFs
- **Rule-Based Parsing**: Local regex parser (no external APIs) using `converter.py`
- **Two-Sheet Excel Export**:
  - **DB Import**: Friendly labels + database column names + values (blue styling)
  - **Itinerary**: Day-by-day reference with guest details and room breakdown (green styling)
- **Review Page**: Editable form to verify parsed data before submission
- **Professional Formatting**: Color-coded headers, borders, optimized column widths

## Tech Stack

- **Server**: Node.js + Express (port 3010)
- **Templates**: Nunjucks
- **Styling**: SCSS
- **PDF Processing**: Python 3 + pdfplumber
- **Excel Generation**: Python + openpyxl
- **Session Management**: express-session

## Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Windows (MSSQL server, if using Flask backend)

### Installation

```bash
npm install
```

### Running the Server

```bash
# Development (with SCSS watch)
npm run dev

# Or separately:
npm run server      # Node.js on http://localhost:3010
npm run sass        # SCSS compiler watch
```

## How It Works

1. **Upload PDF** → User selects booking PDF via web interface
2. **Parse PDF** → `parse_booking.py` extracts text using pdfplumber
3. **Extract Data** → `converter.py` applies rule-based regex patterns to identify:
   - Booking reference, client name, pax details
   - Travel dates, flights, destinations
   - Itinerary day-by-day schedule
4. **Generate Excel** → `build_excel_wrapper.py` calls `converter.build_excel()`
5. **Review & Download** → User reviews parsed data and downloads Excel from `/review` page

## Project Structure

```
├── server.js                 # Express bootstrap (middleware, listen)
├── lib/                      # Config, booking helpers, multer, nunjucks
├── routes/                   # Express routers by feature
├── converter.py              # Rule-based PDF parser + Excel builder
├── parse_booking.py          # Standalone parser wrapper (outputs JSON)
├── build_excel_wrapper.py    # Excel generation wrapper
├── templates/                # Nunjucks HTML templates
│   ├── index.html           # Upload form
│   ├── review.html          # Data review & edit form
│   ├── success.html         # Success confirmation page
│   ├── downloads.html       # Download management page
│   ├── base.html            # Layout
│   └── partials/            # Reusable template components
├── static/                   # CSS, JS, fonts
├── scss/                     # SCSS source files
└── uploads/                  # PDF & Excel output (organized by booking ref)
```

## Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Upload form |
| POST | `/upload` | Parse PDF & generate Excel |
| GET | `/review` | Review parsed data |
| GET | `/success` | Success confirmation page |
| GET | `/downloads` | Download management page |
| GET | `/download/excel` | Download generated Excel |
| GET | `/upload-notes` | Upload extra files to a booking folder |
| POST | `/upload-notes/:booking` | Save uploaded notes files |

## Configuration

- **Database** (Flask only): Edit `config.py` for MSSQL server details
- **Port**: 3010 (set `PORT` in `.env` or `lib/config.js`)
- **Python**: set `PYTHON_EXE` in `.env` if not using the default path
- **Max Upload**: 20MB (set in `config.py`)

## Notes

- All parsing is **local & offline** (no external services)
- Excel files include professional styling with color-coded sheets
- Folder organization: `uploads/{Surname}_{QuotationRef}/{QuotationRef}.pdf|xlsx` (surname omitted if unknown)
- Session-based data flow for multi-step upload → review → download

