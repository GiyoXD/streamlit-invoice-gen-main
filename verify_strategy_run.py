
import sys
import os
from pathlib import Path
import streamlit as st

# Mock streamlit to avoid errors
if not hasattr(st, 'spinner'):
    class MockSpinner:
        def __enter__(self): pass
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def __call__(self, text): return self
    
    st.spinner = MockSpinner()
    st.success = lambda x: print(f"SUCCESS: {x}")
    st.error = lambda x: print(f"ERROR: {x}")
    st.warning = lambda x: print(f"WARNING: {x}")
    st.info = lambda x: print(f"INFO: {x}")

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

try:
    from app.strategies.high_quality_strategy import HighQualityLeatherStrategy
    
    print("Instantiating HighQualityLeatherStrategy...")
    strategy = HighQualityLeatherStrategy()
    
    input_excel = project_root / "database" / "temp_uploads" / "test.xlsx"
    output_dir = project_root / "scripts" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_excel.exists():
        print(f"Input file not found: {input_excel}")
        sys.exit(1)
        
    print(f"Processing {input_excel}...")
    
    # Test validation first
    is_valid, warnings = strategy.validate_excel_data(input_excel)
    print(f"Validation result: {is_valid}")
    for w in warnings:
        try:
            print(w.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
        except:
            print(w.encode('ascii', 'replace').decode('ascii'))
        
    if is_valid:
        # Test processing
        json_path, identifier = strategy.process_excel_to_json(input_excel, output_dir)
        print(f"Processed JSON path: {json_path}")
        print(f"Identifier: {identifier}")
    else:
        print("Skipping processing due to validation failure.")
        
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
