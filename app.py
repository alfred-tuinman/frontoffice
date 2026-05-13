"""app.py — Booking Converter web application."""
import os, sys, uuid, json, threading, time
from pathlib import Path
from datetime import datetime, date

from flask import (Flask, request, render_template, jsonify,
                   redirect, url_for, send_file, abort)

sys.path.insert(0, str(Path(__file__).parent))
import config
from converter import extract_pdf_text, parse_with_claude
from db import (get_all_lookups, get_next_quotation_no,
               insert_quotation, insert_itinerary,
               update_quotation, update_itinerary, find_existing)

sys.path.insert(0, str(Path(__file__).parent.parent))
from pdf_to_booking_excel import build_excel

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

TEMP_DIR   = Path(__file__).parent / "temp"
OUTPUT_DIR = Path(__file__).parent / "outputs"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Auto-clean files older than 2 hours ───────────────────────
def _cleanup():
    while True:
        time.sleep(900)
        cutoff = time.time() - 7200
        for folder in (TEMP_DIR, OUTPUT_DIR):
            for f in folder.iterdir():
                if f.is_file() and f.stat().st_mtime < cutoff:
                    f.unlink(missing_ok=True)

threading.Thread(target=_cleanup, daemon=True).start()


# ── Helpers ────────────────────────────────────────────────────
def _load_session(token):
    p = TEMP_DIR / f"{token}.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)

def _fmt_date_html(s):
    """DD.MM.YYYY → YYYY-MM-DD for HTML date inputs."""
    if not s:
        return ""
    try:
        return datetime.strptime(s, "%d.%m.%Y").strftime("%Y-%m-%d")
    except Exception:
        return ""

def _parse_form(f):
    """Extract and coerce all form fields from request.form."""
    def txt(k):   v = f.get(k, "").strip(); return v or None
    def num(k):
        try: return int(f.get(k, ""))
        except: return None
    def dec(k):
        try: return float(f.get(k, ""))
        except: return None
    def dt(k):
        v = f.get(k, "").strip()
        try: return datetime.strptime(v, "%Y-%m-%d").date() if v else None
        except: return None
    def dtt(k):
        """Date + time combined from a datetime-local input (YYYY-MM-DDTHH:MM)."""
        v = f.get(k, "").strip()
        if not v: return None
        try: return datetime.strptime(v, "%Y-%m-%dT%H:%M")
        except:
            try: return datetime.strptime(v, "%Y-%m-%d")
            except: return None
    def chk(k): return k in f

    quotation_fields = {
        # Identification
        "QuotationRef":       txt("QuotationRef"),
        "PrincipalClient":    txt("PrincipalClient"),
        "PaxName":            txt("PaxName"),
        "PaxFirstName":       txt("PaxFirstName"),
        "Email":              txt("Email"),
        "Reference":          txt("Reference"),
        "TourCode":           txt("TourCode"),
        "TourNo":             num("TourNo"),
        "Comment":            txt("Comment"),
        # Pax & Rooms
        "NumPax":             num("NumPax"),
        "NumSingles":         num("NumSingles"),
        "NumDoubles":         num("NumDoubles"),
        "NumTwins":           num("NumTwins"),
        "NumTriples":         num("NumTriples"),
        "ExtraBed":           chk("ExtraBed"),
        "HotelTypes_id":      num("HotelTypes_id"),
        # Dates
        "DateOfArrival":      dt("DateOfArrival"),
        "DateOfDeparture":    dt("DateOfDeparture"),
        "StartDate":          dt("StartDate"),
        "EndDate":            dt("EndDate"),
        "Nights":             num("Nights"),
        "BookingRecdDate":    dt("BookingRecdDate"),
        "BookingEntryDate":   dt("BookingEntryDate"),
        "QuotationDate":      dt("QuotationDate"),
        "DueDate":            dt("DueDate"),
        # Flights
        "FlightNo":           txt("FlightNo"),
        "ETA":                txt("ETA"),
        "PlaceFrom":          txt("PlaceFrom"),
        "FlightNoDept":       txt("FlightNoDept"),
        "ETD":                txt("ETD"),
        "PlaceTo":            txt("PlaceTo"),
        # Destination FK
        "Countries_id":       num("Countries_id"),
        "StartCities_id":     num("StartCities_id"),
        "EndCities_id":       num("EndCities_id"),
        "CarHireAgents_id":   num("CarHireAgents_id"),
        "CarHireCities_id":   num("CarHireCities_id"),
        "Vehicles_id":        num("Vehicles_id"),
        # Quotation FK + auto
        "QuotationNo":        num("QuotationNo"),
        "QuotationYearRef":   num("QuotationYearRef"),
        "PrincipalAgents_id": num("PrincipalAgents_id"),
        "Managers_id":        num("Managers_id"),
        "Consultants_id":     num("Consultants_id"),
        "AdmUsers_id":        num("AdmUsers_id"),
        # Inclusions FK + flags
        "MealPlans_id":       num("MealPlans_id"),
        "Tickets_id":         num("Tickets_id"),
        "Currencies_id":      num("Currencies_id"),
        "Guide":              chk("Guide"),
        "EntranceFees":       chk("EntranceFees"),
        "EconomyPax":         chk("EconomyPax"),
        "TimePax":            chk("TimePax"),
        "domestic":           chk("domestic"),
        "DeptDomestic":       chk("DeptDomestic"),
        "Confirmed":          chk("Confirmed"),
        # Financial
        "BasicRate":          dec("BasicRate"),
        "BasicAmt":           dec("BasicAmt"),
        "ServiceTaxPerc":     dec("ServiceTaxPerc"),
        "ServiceTaxAmt":      dec("ServiceTaxAmt"),
        "QuotationAmt":       dec("QuotationAmt"),
        "AdvanceAmt":         dec("AdvanceAmt"),
        "ExtraMargin":        dec("ExtraMargin"),
    }

    itinerary_fields = {
        "departuredate":          dt("itin_departuredate"),
        "masters_id":             num("itin_masters_id"),
        "invoices_id":            num("itin_invoices_id"),
        "sessionid":              txt("itin_sessionid"),
        "leadname":               txt("itin_leadname"),
        "arr_cities_id":          num("itin_arr_cities_id"),
        "arrtime":                dtt("itin_arrtime"),
        "dep_cities_id":          num("itin_dep_cities_id"),
        "depdate":                dt("itin_depdate"),
        "deptime":                dtt("itin_deptime"),
        "countries_id":           num("itin_countries_id"),
        "flightbooked":           chk("itin_flightbooked"),
        "pax":                    num("itin_pax"),
        "singles":                num("itin_singles"),
        "doubles":                num("itin_doubles"),
        "triples":                num("itin_triples"),
        "twins":                  num("itin_twins"),
        "resident":               chk("itin_resident"),
        "web_users_id":           num("itin_web_users_id"),
        "TourLeader":             txt("itin_TourLeader"),
        "TourLeaderCountries_id": num("itin_TourLeaderCountries_id"),
        "IssuedOn":               dt("itin_IssuedOn"),
        "Status":                 num("itin_Status"),
        "IssuedBy":               txt("itin_IssuedBy"),
        "TourRef":                txt("itin_TourRef"),
        # Quotations_id is set after the quotation insert
    }

    # Hidden fields that signal an update vs insert
    try:
        existing_quot_id = int(request.form.get("_existing_Quotations_id", ""))
    except ValueError:
        existing_quot_id = None
    try:
        existing_itin_id = int(request.form.get("_existing_itineraries_id", ""))
    except ValueError:
        existing_itin_id = None

    quotation_fields["_existing_Quotations_id"] = existing_quot_id
    itinerary_fields["_existing_itineraries_id"] = existing_itin_id

    return quotation_fields, itinerary_fields


# ── Routes ─────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    pdf = request.files.get("pdf")
    if not pdf or not pdf.filename.lower().endswith(".pdf"):
        return render_template("index.html", error="Please upload a PDF file.")

    token    = uuid.uuid4().hex
    pdf_path = TEMP_DIR / f"{token}.pdf"

    try:
        pdf.save(str(pdf_path))
        raw  = extract_pdf_text(str(pdf_path))
        data = parse_with_claude(raw)
        with open(TEMP_DIR / f"{token}.json", "w") as fh:
            json.dump(data, fh)
        return redirect(url_for("review", token=token))
    except Exception as e:
        return render_template("index.html", error=f"Could not process PDF: {e}")
    finally:
        pdf_path.unlink(missing_ok=True)


@app.route("/review/<token>")
def review(token):
    if not (token.isalnum() and len(token) == 32):
        abort(400)

    data = _load_session(token)
    if not data:
        return render_template("index.html", error="Session expired — please upload again.")

    q = dict(data["quotation"])
    for df in ("DateOfArrival", "DateOfDeparture", "StartDate", "EndDate"):
        q[df] = _fmt_date_html(q.get(df))

    return render_template(
        "review.html",
        token=token,
        q=q,
        guests=data["guests"],
        itinerary=data["itinerary"],
        lookups=get_all_lookups(),
        auto_no=get_next_quotation_no(),
        today=date.today().isoformat(),
    )


@app.route("/lookup/<token>", methods=["POST"])
def lookup(token):
    """AJAX endpoint: given a Quotations_id, return whether a record exists."""
    if not (token.isalnum() and len(token) == 32):
        abort(400)
    try:
        qid = int(request.form.get("Quotations_id", ""))
    except ValueError:
        return jsonify(found=False)
    rec = find_existing(qid)
    if rec:
        return jsonify(found=True, **rec)
    return jsonify(found=False)


@app.route("/submit/<token>", methods=["POST"])
def submit(token):
    if not (token.isalnum() and len(token) == 32):
        abort(400)

    data = _load_session(token)
    if not data:
        return render_template("index.html", error="Session expired — please upload again.")

    quot_fields, itin_fields = _parse_form(request.form)

    # Determine whether this is an INSERT or UPDATE
    existing_quot_id = quot_fields.pop("_existing_Quotations_id", None)
    existing_itin_id = itin_fields.pop("_existing_itineraries_id", None)
    is_update = bool(existing_quot_id)

    try:
        if is_update:
            # ── UPDATE existing records ───────────────────────────────────────
            quot_id = update_quotation(existing_quot_id, quot_fields)

            itin_fields["Quotations_id"] = quot_id
            if existing_itin_id:
                itin_id = update_itinerary(existing_itin_id, itin_fields)
            else:
                # Quotation existed but had no itinerary row yet — insert one
                itin_id = insert_itinerary(itin_fields)
        else:
            # ── INSERT new records ────────────────────────────────────────────
            quot_id = insert_quotation(quot_fields)
            itin_fields["Quotations_id"] = quot_id
            itin_id = insert_itinerary(itin_fields)

    except Exception as e:
        return render_template(
            "review.html",
            token=token,
            q=request.form,
            guests=data["guests"],
            itinerary=data["itinerary"],
            lookups=get_all_lookups(),
            auto_no=get_next_quotation_no(),
            today=date.today().isoformat(),
            db_error=str(e),
        )

    # Build confirmation Excel (non-fatal)
    xlsx_path = OUTPUT_DIR / f"{token}.xlsx"
    try:
        build_excel(data, str(xlsx_path))
    except Exception:
        pass

    (TEMP_DIR / f"{token}.json").unlink(missing_ok=True)

    return render_template(
        "success.html",
        quot_id=quot_id,
        itin_id=itin_id,
        is_update=is_update,
        client=quot_fields.get("PrincipalClient", ""),
        quotation_ref=quot_fields.get("QuotationRef", ""),
        token=token,
        has_excel=xlsx_path.exists(),
    )


@app.route("/download/<token>")
def download(token):
    if not (token.isalnum() and len(token) == 32):
        abort(400)
    path = OUTPUT_DIR / f"{token}.xlsx"
    if not path.exists():
        abort(404)
    return send_file(
        str(path), as_attachment=True,
        download_name="booking_confirmation.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    from waitress import serve
    print(f"🚀  Booking Converter → http://0.0.0.0:{config.PORT}")
    serve(app, host="0.0.0.0", port=config.PORT)
