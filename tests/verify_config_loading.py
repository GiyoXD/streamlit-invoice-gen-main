import sys
import os
import pprint

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_parser import config

def verify_config_loading():
    print("Verifying config.py loading of external mappings...")
    
    # Check a few key mappings
    expected_mappings = {
        'col_po': ['PO NO.', 'po', 'PO', 'Po', '订单号', 'order number', 'order no', 'Po Nb', '尺数', 'PO NB', 'Po Nb', '客户订单号', '订单号', 'P.O Nº', 'P.O NO', 'PO Nº', 'P.O. Nº', 'P.O N°', 'P.O. N°', 'P.O. NO.', 'P.O', 'Cargo Description', 'Cargo Descprition', 'Description of Goods', 'Description of Goods.', 'FAIL HEADER', 'CUT.P.O.', 'TEST PO'],
        'col_item': ['物料代码', 'item no', 'ITEM NO.', 'item', 'Item No', 'ITEM NO', 'Item No', '客户品名', '物料编码', '产品编号', 'ITEM Nº', 'Item Nº', 'HL ITEM', 'ITEM', 'Name of\\nCormodity', 'Name of\nCormodity', 'Name of Commodity', 'Name of Cormodity\nTên và miêu tả'],
        'col_cbm': ['cbm', '材积', 'CBM', 'remarks', '备注', 'Remark', 'remark', '低', 'REMARKS', 'REMARK', '(CBM)'],
        'col_remarks': ['cbm', '材积', 'CBM', 'remarks', '备注', 'Remark', 'remark', '低', 'REMARKS', 'REMARK']
    }

    all_passed = True
    for canonical, expected_headers in expected_mappings.items():
        if canonical not in config.TARGET_HEADERS_MAP:
            print(f"FAILURE: Canonical key '{canonical}' not found in TARGET_HEADERS_MAP.")
            all_passed = False
            continue
        
        actual_headers = config.TARGET_HEADERS_MAP[canonical]
        print(f"\nChecking '{canonical}':")
        # print(f"  Actual: {actual_headers}")
        
        missing = [h for h in expected_headers if h not in actual_headers]
        if missing:
            print(f"  FAILURE: Missing expected headers: {missing}")
            all_passed = False
        else:
            print(f"  SUCCESS: All expected headers found.")

    if all_passed:
        print("\nALL CONFIG CHECKS PASSED!")
    else:
        print("\nSOME CONFIG CHECKS FAILED.")

if __name__ == "__main__":
    verify_config_loading()
