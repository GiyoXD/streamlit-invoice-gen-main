import sys
import os
import decimal
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_parser import data_processor

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_strict_col_naming():
    print("Testing strict col_ naming in data_processor.py...")

    # Mock Data with 'col_' keys
    mock_data = {
        'col_po': ['PO123', 'PO123'],
        'col_item': ['ITEM-A', 'ITEM-A'],
        'col_unit_price': [10.0, 10.0],
        'col_qty_sf': [100.0, 200.0],
        'col_amount': [1000.0, 2000.0],
        'col_desc': ['Desc A', 'Desc A'],
        'col_qty_pcs': [10, 20],
        'col_net': [50.0, 100.0],
        'col_gross': [55.0, 110.0],
        'col_cbm': ['1*1*1', '2*2*2'],
        'col_pallet_count': [1, 1]
    }

    # Test aggregate_standard_by_po_item_price
    print("\nTesting aggregate_standard_by_po_item_price...")
    global_agg_map = {}
    data_processor.aggregate_standard_by_po_item_price(mock_data, global_agg_map)
    
    expected_key = ('PO123', 'ITEM-A', decimal.Decimal('10.0'), 'Desc A')
    if expected_key in global_agg_map:
        res = global_agg_map[expected_key]
        print(f"SUCCESS: Found aggregated key: {expected_key}")
        print(f"  SQFT Sum: {res['sqft_sum']} (Expected 300.0)")
        print(f"  Amount Sum: {res['amount_sum']} (Expected 3000.0)")
        assert res['sqft_sum'] == decimal.Decimal('300.0')
        assert res['amount_sum'] == decimal.Decimal('3000.0')
    else:
        print(f"FAILURE: Key {expected_key} not found in aggregation map.")
        print(f"Map keys: {list(global_agg_map.keys())}")
        return

    # Test aggregate_custom_by_po_item
    print("\nTesting aggregate_custom_by_po_item...")
    global_custom_map = {}
    data_processor.aggregate_custom_by_po_item(mock_data, global_custom_map)
    
    expected_custom_key = ('PO123', 'ITEM-A', None, 'Desc A')
    if expected_custom_key in global_custom_map:
        res = global_custom_map[expected_custom_key]
        print(f"SUCCESS: Found custom aggregated key: {expected_custom_key}")
        print(f"  SQFT Sum: {res['sqft_sum']} (Expected 300.0)")
        assert res['sqft_sum'] == decimal.Decimal('300.0')
    else:
        print(f"FAILURE: Key {expected_custom_key} not found in custom aggregation map.")
        return

    # Test calculate_footer_totals
    print("\nTesting calculate_footer_totals...")
    totals = data_processor.calculate_footer_totals(mock_data)
    print(f"Totals: {totals}")
    assert totals['total_pcs'] == 30
    assert totals['total_sqft'] == decimal.Decimal('300.0')
    assert totals['total_amount'] == decimal.Decimal('3000.0')
    print("SUCCESS: Footer totals match expected values.")

    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_strict_col_naming()
