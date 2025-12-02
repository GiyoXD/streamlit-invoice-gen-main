import unittest
import sys
import os
import logging

# Ensure the project root is in sys.path to allow imports
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.invoice_generator.data.data_preparer import prepare_data_rows

# Configure logging to suppress warnings during tests
logging.basicConfig(level=logging.CRITICAL)

class TestPrepareDataRows(unittest.TestCase):
    def setUp(self):
        # Common setup for all tests
        self.column_id_map = {
            "col_unit": 1,
            "col_amount": 2,
            "col_po": 3,
            "col_item": 4
        }
        self.idx_to_header_map = {
            1: "Unit",
            2: "Amount",
            3: "PO",
            4: "Item"
        }
        self.dynamic_mapping_rules = {
            "unit": {"column": "col_unit"},
            "amount": {"column": "col_amount"},
            "po": {"column": "col_po"},
            "item": {"column": "col_item"}
        }
        self.static_value_map = {}
        self.desc_col_idx = -1
        self.num_static_labels = 0
        self.DAF_mode = False

    def test_processed_tables_valid_col_only(self):
        """Test that data is correctly extracted when using valid 'col_' keys."""
        data_source = {
            "col_unit": [1.5, 2.0],
            "col_amount": [100.0, 200.0],
            "col_po": ["PO123", "PO456"],
            "col_item": ["ITEM1", "ITEM2"]
        }
        
        rows, _, _, _ = prepare_data_rows(
            data_source_type='processed_tables',
            data_source=data_source,
            dynamic_mapping_rules=self.dynamic_mapping_rules,
            column_id_map=self.column_id_map,
            idx_to_header_map=self.idx_to_header_map,
            desc_col_idx=self.desc_col_idx,
            num_static_labels=self.num_static_labels,
            static_value_map=self.static_value_map,
            DAF_mode=self.DAF_mode
        )
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], 1.5)      # col_unit
        self.assertEqual(rows[0][3], "PO123")  # col_po
        self.assertEqual(rows[1][2], 200.0)    # col_amount
        self.assertEqual(rows[1][4], "ITEM2")  # col_item

    def test_processed_tables_legacy_keys_fail(self):
        """Test that using legacy keys (e.g., 'po') fails to extract data (Strict Mode)."""
        data_source = {
            "unit": [1.5],
            "amount": [100.0],
            "po": ["PO123"],
            "item": ["ITEM1"]
        }
        
        rows, _, _, _ = prepare_data_rows(
            data_source_type='processed_tables',
            data_source=data_source,
            dynamic_mapping_rules=self.dynamic_mapping_rules,
            column_id_map=self.column_id_map,
            idx_to_header_map=self.idx_to_header_map,
            desc_col_idx=self.desc_col_idx,
            num_static_labels=self.num_static_labels,
            static_value_map=self.static_value_map,
            DAF_mode=self.DAF_mode
        )
        
        self.assertEqual(len(rows), 1)
        # The rows should be empty dicts because no matching 'col_' keys were found
        self.assertEqual(rows[0], {}) 

    def test_processed_tables_partial_data(self):
        """Test behavior when some columns are missing in data source."""
        data_source = {
            "col_unit": [1.5],
            # col_amount is missing
            "col_po": ["PO123"],
            "col_item": ["ITEM1"]
        }
        
        rows, _, _, _ = prepare_data_rows(
            data_source_type='processed_tables',
            data_source=data_source,
            dynamic_mapping_rules=self.dynamic_mapping_rules,
            column_id_map=self.column_id_map,
            idx_to_header_map=self.idx_to_header_map,
            desc_col_idx=self.desc_col_idx,
            num_static_labels=self.num_static_labels,
            static_value_map=self.static_value_map,
            DAF_mode=self.DAF_mode
        )
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 1.5)
        self.assertEqual(rows[0][3], "PO123")
        self.assertNotIn(2, rows[0]) # col_amount (index 2) should be missing

    def test_processed_tables_mismatched_lengths(self):
        """Test that the number of rows is determined by the first list found."""
        data_source = {
            "col_unit": [1.0, 2.0, 3.0], # 3 items
            "col_po": ["PO1", "PO2"]     # 2 items
        }
        
        rows, _, _, _ = prepare_data_rows(
            data_source_type='processed_tables',
            data_source=data_source,
            dynamic_mapping_rules=self.dynamic_mapping_rules,
            column_id_map=self.column_id_map,
            idx_to_header_map=self.idx_to_header_map,
            desc_col_idx=self.desc_col_idx,
            num_static_labels=self.num_static_labels,
            static_value_map=self.static_value_map,
            DAF_mode=self.DAF_mode
        )
        
        # If col_unit is found first, it might try to generate 3 rows.
        # But col_po only has 2 items, so the 3rd row won't have PO data.
        # The exact behavior depends on dict iteration order, but let's verify safety.
        
        num_rows = len(rows)
        self.assertTrue(num_rows in [2, 3]) 
        
        if num_rows == 3:
            # 3rd row should have unit but no PO
            self.assertEqual(rows[2].get(1), 3.0)
            self.assertIsNone(rows[2].get(3))

    def test_invalid_data_source_type(self):
        """Test that unknown data source types return empty results."""
        rows, _, _, _ = prepare_data_rows(
            data_source_type='unknown_type',
            data_source={},
            dynamic_mapping_rules={},
            column_id_map={},
            idx_to_header_map={},
            desc_col_idx=-1,
            num_static_labels=0,
            static_value_map={},
            DAF_mode=False
        )
        self.assertEqual(rows, [])

if __name__ == '__main__':
    unittest.main()
