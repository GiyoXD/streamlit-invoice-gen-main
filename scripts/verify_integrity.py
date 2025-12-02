
import json
import decimal
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.data_parser.excel_handler import ExcelHandler
from core.data_parser import sheet_parser
from core.data_parser import config as cfg

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def _to_decimal(val):
    if val is None: return decimal.Decimal(0)
    try:
        return decimal.Decimal(str(val))
    except:
        return decimal.Decimal(0)

def verify_integrity(excel_path: str, json_path: str):
    logging.info(f"--- Starting Integrity Verification ---")
    logging.info(f"Input Excel: {excel_path}")
    logging.info(f"Output JSON: {json_path}")

    # 1. Calculate Totals from Excel (Source of Truth)
    logging.info("\n[1] Calculating Source Totals from Excel...")
    handler = ExcelHandler(excel_path)
    sheet = handler.load_sheet(sheet_name=cfg.SHEET_NAME, data_only=True)
    
    # Use the same extraction logic as main.py to ensure we look at the same raw data
    header_row, col_map = sheet_parser.find_and_map_smart_headers(sheet)
    if not header_row:
        logging.error("Could not find header row in Excel.")
        return

    all_header_rows = [header_row] + sheet_parser.find_all_header_rows(sheet, cfg.HEADER_IDENTIFICATION_PATTERN, (header_row + 1, sheet.max_row), cfg.HEADER_SEARCH_COL_RANGE)
    raw_data_map = sheet_parser.extract_multiple_tables(sheet, all_header_rows, col_map)

    excel_totals = {
        'col_amount': decimal.Decimal(0),
        'col_qty_sf': decimal.Decimal(0),
        'col_net': decimal.Decimal(0),
        'col_gross': decimal.Decimal(0),
        'col_cbm': decimal.Decimal(0) # Note: CBM is calculated, but we can check if raw CBM sums match if they existed
    }

    # Sum up raw extracted values
    for table_id, data in raw_data_map.items():
        for col_key in excel_totals.keys():
            if col_key in data:
                # For CBM, raw data is string "L*W*H", so we can't sum it directly. 
                # We skip CBM raw sum comparison as it's a calculated field.
                if col_key == 'col_cbm': continue 
                
                values = data[col_key]
                for v in values:
                    excel_totals[col_key] += _to_decimal(v)

    logging.info(f"Excel Totals (Raw Extracted):")
    for k, v in excel_totals.items():
        if k != 'col_cbm':
            logging.info(f"  {k}: {v}")

    # 2. Calculate Totals from JSON (Aggregated Result)
    logging.info("\n[2] Calculating Result Totals from JSON...")
    with open(json_path, 'r') as f:
        json_data = json.load(f)

    json_totals = {
        'col_amount': decimal.Decimal(0),
        'col_qty_sf': decimal.Decimal(0),
        'col_net': decimal.Decimal(0),
        'col_gross': decimal.Decimal(0),
        'col_cbm': decimal.Decimal(0)
    }

    # Sum up from 'processed_tables_data' (which contains the distributed values)
    processed_tables = json_data.get('processed_tables_data', {})
    for table_id, data in processed_tables.items():
        for col_key in json_totals.keys():
             if col_key in data:
                values = data[col_key]
                for v in values:
                    json_totals[col_key] += _to_decimal(v)

    logging.info(f"JSON Totals (Processed & Distributed):")
    for k, v in json_totals.items():
        logging.info(f"  {k}: {v}")

    # 3. Compare
    logging.info("\n[3] Comparison (Difference = JSON - Excel)")
    match = True
    for k in ['col_amount', 'col_qty_sf', 'col_net', 'col_gross']:
        diff = json_totals[k] - excel_totals[k]
        status = "✅ MATCH" if diff == 0 else "❌ MISMATCH"
        if diff != 0: match = False
        logging.info(f"  {k}: Diff = {diff}  [{status}]")
    
    # Check CBM separately (JSON total vs JSON calculated sum)
    # Since CBM is calculated, we just show the total
    logging.info(f"  col_cbm: {json_totals['col_cbm']} (Calculated field, no raw sum to compare)")

    if match:
        logging.info("\nSUCCESS: All primary value totals match exactly! No fractional loss.")
    else:
        logging.error("\nFAILURE: Discrepancies found.")

if __name__ == "__main__":
    excel_file = "core/invoice_generator/JF25057.xlsx"
    json_file = "scripts/output/JF25057.json"
    verify_integrity(excel_file, json_file)
