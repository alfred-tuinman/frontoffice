"""save_booking.py — Save booking data to database and return IDs."""
import sys
import json
from db import insert_quotation, insert_itinerary, get_next_quotation_no, find_by_quotation_ref, update_quotation, update_itinerary, find_itinerary_by_quotation

# ─────────────────────────────────────────────────────────────────────────
# Configuration: Set to False to disable automatic itinerary processing
# ─────────────────────────────────────────────────────────────────────────
PROCESS_ITINERARIES = False  # Toggle itinerary automation here

def save_booking(raw_data):
    """
    Insert quotation (and optionally itinerary) from form data.
    Return dict with Quotations_id, itineraries_id, QuotationRef.
    """
    try:
        print(f"📥 Raw data received: {len(raw_data)} fields", file=sys.stderr)
        
        # Separate quotation and itinerary fields
        quotation_data = {}
        itinerary_data = {}
        
        for key, value in raw_data.items():
            # Convert 'on' checkbox values to 1, normalise all null-like values to None
            if value == 'on':
                value = 1
            elif value in ('', None, 'null', 'NULL', 'None'):
                value = None

            # Skip empty/null values for cleaner insert
            if value is None:
                continue

            # Also skip falsy numeric IDs (e.g. Quotations_id=0 arriving from a form)
            if key.endswith('_id') and value in (0, '0'):
                continue

            # Route to appropriate table
            if key.startswith('itin_'):
                # Remove prefix and add to itinerary data
                itin_key = key[5:]
                itinerary_data[itin_key] = value
            else:
                quotation_data[key] = value
        
        print(f"✅ Parsed quotation_data ({len(quotation_data)} fields): {list(quotation_data.keys())}", file=sys.stderr)
        print(f"✅ Parsed itinerary_data ({len(itinerary_data)} fields): {list(itinerary_data.keys())}", file=sys.stderr)
        
        # Generate QuotationRef if needed
        if not quotation_data.get('QuotationRef'):
            quotation_data['QuotationRef'] = f"QT-{quotation_data.get('QuotationYearRef', 2026)}-{str(quotation_data.get('QuotationNo', 1)).zfill(4)}"

        # Check if this QuotationRef already exists — update if so
        existing = find_by_quotation_ref(quotation_data['QuotationRef'])
        if existing:
            print(f"✅ QuotationRef {quotation_data['QuotationRef']} already exists — updating", file=sys.stderr)
            quotations_id = existing['Quotations_id']
            
            # Update the quotation
            update_quotation(quotations_id, quotation_data)
            print(f"✅ Quotation updated: ID {quotations_id}", file=sys.stderr)
            
            # Update itinerary if it exists and we have new itinerary data
            itineraries_id = existing['itineraries_id']
            
            if PROCESS_ITINERARIES:
                # Use TourRef from itinerary data if provided, otherwise fall back to QuotationRef
                if itineraries_id and itinerary_data:
                    update_itinerary(itineraries_id, itinerary_data)
                    print(f"✅ Itinerary updated: ID {itineraries_id}", file=sys.stderr)
                elif not itineraries_id and itinerary_data and (itinerary_data.get('departuredate') or itinerary_data.get('depdate')):
                    # Create new itinerary if it doesn't exist
                    itinerary_data['Quotations_id'] = quotations_id
                    itineraries_id = insert_itinerary(itinerary_data)
                    print(f"✅ Itinerary created: ID {itineraries_id}", file=sys.stderr)
            else:
                print(f"⏭️ Itinerary processing disabled (PROCESS_ITINERARIES=False)", file=sys.stderr)
            
            result = {
                'Quotations_id': quotations_id,
                'itineraries_id': itineraries_id,
                'QuotationRef': quotation_data.get('QuotationRef'),
                'is_update': True,
            }
            print(f"✅ Updated existing: {result}", file=sys.stderr)
            return result

        # Get next IDs/numbers (Quotations_id is NOT an identity col)
        if not quotation_data.get('QuotationNo') or not quotation_data.get('Quotations_id'):
            next_numbers = get_next_quotation_no()
            if not quotation_data.get('Quotations_id'):
                quotation_data['Quotations_id'] = next_numbers['Quotations_id']
            if not quotation_data.get('QuotationNo'):
                quotation_data['QuotationNo'] = next_numbers['QuotationNo']
                quotation_data['QuotationYearRef'] = next_numbers['QuotationYearRef']
            print(f"📊 Generated Quotations_id={quotation_data['Quotations_id']}, QuotationNo={quotation_data['QuotationNo']}, Year={quotation_data['QuotationYearRef']}", file=sys.stderr)

        print(f"💾 Ready to insert quotation: {quotation_data}", file=sys.stderr)

        # Insert the quotation
        quotations_id = insert_quotation(quotation_data)
        print(f"✅ Quotation inserted: ID {quotations_id}", file=sys.stderr)
        
        # Handle itinerary — check if one exists for this quotation
        itineraries_id = None
        
        if PROCESS_ITINERARIES:
            tour_ref = itinerary_data.get('TourRef') or quotation_data.get('QuotationRef')
            
            if itinerary_data and (itinerary_data.get('departuredate') or itinerary_data.get('depdate')):
                
                # Check for existing itinerary
                existing_itin = find_itinerary_by_quotation(quotations_id, tour_ref)
                
                if existing_itin:
                    # Update existing itinerary
                    itineraries_id = existing_itin['itineraries_id']
                    itinerary_data['Quotations_id'] = quotations_id
                    print(f"💾 Ready to update itinerary {itineraries_id}: {itinerary_data}", file=sys.stderr)
                    update_itinerary(itineraries_id, itinerary_data)
                    print(f"✅ Itinerary updated: ID {itineraries_id}", file=sys.stderr)
                else:
                    # Create new itinerary
                    itinerary_data['Quotations_id'] = quotations_id
                    print(f"💾 Ready to insert itinerary: {itinerary_data}", file=sys.stderr)
                    itineraries_id = insert_itinerary(itinerary_data)
                    print(f"✅ Itinerary inserted: ID {itineraries_id}", file=sys.stderr)
        else:
            print(f"⏭️ Itinerary processing disabled (PROCESS_ITINERARIES=False)", file=sys.stderr)
        
        result = {
            'Quotations_id': quotations_id,
            'itineraries_id': itineraries_id,
            'QuotationRef': quotation_data.get('QuotationRef')
        }
        
        print(f"✅ Success! Result: {result}", file=sys.stderr)
        return result
    
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('{"error": "No data provided"}')
        sys.exit(1)
    
    try:
        booking_data = json.loads(sys.argv[1])
        result = save_booking(booking_data)
        print(json.dumps(result))
    except json.JSONDecodeError as e:
        print(f'{{"error": "Invalid JSON: {str(e)}"}}')
        sys.exit(1)
    except Exception as e:
        print(f'{{"error": "{str(e)}"}}')
        sys.exit(1)