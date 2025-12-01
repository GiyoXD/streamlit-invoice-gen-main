import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from core.orchestrator import Orchestrator

def main():

    print("--- Starting Manual Run ---")
    
    # Setup Paths
    if len(sys.argv) > 1:
        input_excel = Path(sys.argv[1])
    else:
        input_excel = project_root / "database" / "temp_uploads" / "test.xlsx"
    
    output_dir = project_root / "scripts" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use database/config/bundled for config
    config_dir = project_root / "database" / "config" / "bundled"
    # Use database/template for template
    template_dir = project_root / "database" / "template"
    
    if not input_excel.exists():
        print(f"Error: Input file not found at {input_excel}")
        return

    orchestrator = Orchestrator()
    
    try:
        # Determine mode based on file extension
        if input_excel.suffix.lower() == '.json':
            print(f"Input is JSON. Skipping Excel processing.")
            json_path = input_excel
            identifier = input_excel.stem
        else:
            # Step 1: Excel to JSON
            print(f"Processing Excel: {input_excel}")
            json_path, identifier = orchestrator.process_excel_to_json(input_excel, output_dir)
            print(f"JSON generated at: {json_path}")
        
        # Step 2: Generate Invoice
        print("Generating Invoice...")
        output_invoice = output_dir / f"{identifier}_invoice.xlsx"
        
        result_path = orchestrator.generate_invoice(
            json_path=json_path,
            output_path=output_invoice,
            template_dir=template_dir,
            config_dir=config_dir,
            flags=["--custom"] # Example flag
        )
        print(f"Invoice generated at: {result_path}")
        print("--- Run Passed ---")
        
    except Exception as e:
        print(f"--- Run Failed ---")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
