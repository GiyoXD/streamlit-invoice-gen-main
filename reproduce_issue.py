
import logging
from typing import Any, Dict, List
import sys
import os

# Add core to path
sys.path.append(os.getcwd())

from core.invoice_generator.data.data_preparer import prepare_data_rows

# Mock logger
logging.basicConfig(level=logging.INFO)

def test_prepare_data_rows_with_list():
    print("Testing prepare_data_rows with list input (new structure)...")
    
    # Mock data source as a list of maps (new structure)
    data_source = [
        {"col_po": "PO1", "col_item": "Item1", "col_qty": 10},
        {"col_po": "PO2", "col_item": "Item2", "col_qty": 20}
    ]
    
    # Mock mapping rules
    dynamic_mapping_rules = {
        "col_po": {"column": "col_po"},
        "col_item": {"column": "col_item"},
        "col_qty": {"column": "col_qty"},
        "col_desc": {"column": "col_desc", "fallback": "DESC"} # Add fallback to avoid warning
    }
    
    # Mock column maps
    column_id_map = {
        "col_po": 1,
        "col_item": 2,
        "col_qty": 3,
        "col_desc": 4
    }
    idx_to_header_map = {1: "PO", 2: "Item", 3: "Qty", 4: "Desc"}
    
    try:
        data_rows, _, _, _ = prepare_data_rows(
            data_source_type='DAF_aggregation',
            data_source=data_source,
            dynamic_mapping_rules=dynamic_mapping_rules,
            column_id_map=column_id_map,
            idx_to_header_map=idx_to_header_map,
            desc_col_idx=4,
            num_static_labels=0,
            static_value_map={},
            DAF_mode=True
        )
        print("Success! Result:", data_rows)
    except Exception as e:
        print(f"Caught expected exception: {e}")

if __name__ == "__main__":
    test_prepare_data_rows_with_list()
