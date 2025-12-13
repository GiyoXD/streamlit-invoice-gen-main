
import sys
import os
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import directly from core
from core.data_parser.main import run_invoice_automation
from core.invoice_generator.generate_invoice import run_invoice_generation

def run_e2e_test():
    input_excel = ROOT / "tests" / "database" / "hostfile" / "CT25551.xlsx"
    output_dir = ROOT / "tests" / "database" / "hostfile"
    
    # 1. Excel -> JSON
    print(f"--- Step 1: Parsing {input_excel} ---")
    try:
        json_path, identifier = run_invoice_automation(
            input_excel_override=str(input_excel),
            output_dir_override=str(output_dir)
        )
        print(f"✅ Created JSON: {json_path}")
    except Exception as e:
        print(f"❌ Data Parser Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. JSON -> Invoice
    print(f"\n--- Step 2: Generating Invoice from {json_path} ---")
    
    # Check if we should override output name
    output_invoice = output_dir / f"{identifier}_Result.xlsx"
    
    try:
        result_path = run_invoice_generation(
            input_data_path=Path(json_path),
            output_path=output_invoice,
            # Let it resolve config automatically
        )
        print(f"✅ Checkmate! Invoice generated: {result_path}")
    except Exception as e:
        print(f"❌ Invoice Generation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_e2e_test()
