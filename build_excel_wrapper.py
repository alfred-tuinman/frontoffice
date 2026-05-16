#!/usr/bin/env python3
"""
build_excel_wrapper.py
Wrapper to generate Excel from PDF using converter.py
"""

import sys
from converter import extract_pdf_text, parse_pdf_rules, build_excel

def main():
    if len(sys.argv) < 3:
        print("[ERROR] Usage: build_excel_wrapper.py <input.pdf> <output.xlsx>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    xlsx_path = sys.argv[2]

    try:
        print(f"[PDF] Reading: {pdf_path}")
        raw_text = extract_pdf_text(pdf_path)

        print("[PARSE] Parsing with rule-based parser ...")
        data = parse_pdf_rules(raw_text)

        q = data.get('quotation', {})
        print(f"  Client : {q.get('PrincipalClient')}")
        print(f"  Ref    : {q.get('QuotationRef')}")
        print(f"  Pax    : {q.get('NumPax')}")
        print(f"  Days   : {len(data.get('itinerary', []))} itinerary entries")

        print("[BUILD] Building Excel ...")
        build_excel(data, xlsx_path)
        print(f"[OK] Saved: {xlsx_path}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
