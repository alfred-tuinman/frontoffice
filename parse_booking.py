
import sys
import json
import pdfplumber

# Use the converter module for superior rule-based parsing
from converter import extract_pdf_text, parse_pdf_rules

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: parse_booking.py <pdf_path>"}))
        sys.exit(1)
    pdf_path = sys.argv[1]
    text = extract_pdf_text(pdf_path)
    data = parse_pdf_rules(text)
    # Output only the quotation part for the review form
    print(json.dumps(data.get('quotation', {})))

if __name__ == "__main__":
    main()
