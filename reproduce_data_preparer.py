
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.invoice_generator.data.data_preparer import prepare_data_rows

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_prepare_data_rows_new_structure():
    print("Testing prepare_data_rows with new column-oriented data structure...")

    # Mock data matching NEW "col only" structure
    data_source = {
        "col_unit": [1.3, 1.17],
        "col_amount": [11839.36, 1621.737],
        "col_po": ["9000798713", "9000798713"],
        "col_item": ["01.10.W653191", "01.10.W653191"]
    }

    # Mock mapping rules (Source Key -> Target ID)
    # Even if source key is "po", it should find "col_po" in data because of priority
    dynamic_mapping_rules = {
        "unit": {"column": "col_unit"},
        "amount": {"column": "col_amount"},
        "po": {"column": "col_po"},
        "item": {"column": "col_item"}
    }

    # Mock column ID map
    column_id_map = {
        "col_unit": 1,
        "col_amount": 2,
        "col_po": 3,
        "col_item": 4
    }

    idx_to_header_map = {
        1: "Unit",
        2: "Amount",
        3: "PO",
        4: "Item"
    }

    # Call prepare_data_rows with 'processed_tables' type
    data_source_type = 'processed_tables'

    data_rows, pallet_counts, dynamic_desc_used, num_rows = prepare_data_rows(
        data_source_type=data_source_type,
        data_source=data_source,
        dynamic_mapping_rules=dynamic_mapping_rules,
        column_id_map=column_id_map,
        idx_to_header_map=idx_to_header_map,
        desc_col_idx=-1,
        num_static_labels=0,
        static_value_map={},
        DAF_mode=False
    )

    print(f"Result: {len(data_rows)} rows generated.")
    print(data_rows)
    
    if len(data_rows) == 0:
        print("FAILURE: No rows generated. data_preparer does not support this structure yet.")
    elif len(data_rows) == 2:
        # Verify content of first row
        first_row = data_rows[0]
        if first_row.get(1) == 1.3 and first_row.get(3) == "9000798713":
            print("SUCCESS: Rows generated correctly with content.")
        else:
            print("FAILURE: Rows generated but content is incorrect/empty.")
            print(f"Expected: {{1: 1.3, 3: '9000798713', ...}}")
            print(f"Got: {first_row}")
    else:
        print(f"PARTIAL FAILURE: Generated {len(data_rows)} rows, expected 2.")

if __name__ == "__main__":
    test_prepare_data_rows_new_structure()
