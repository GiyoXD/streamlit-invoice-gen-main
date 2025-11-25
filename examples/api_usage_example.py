#!/usr/bin/env python3
"""
Example of how to use the Invoice Generator API

This example demonstrates how to use the new programmatic API
instead of relying on command-line interface.
"""

from pathlib import Path
from src.invoice_generator import generate_invoice, generate_invoice_api

def example_strategy_usage():
    """Example of how strategies can use the API"""
    
    # Example paths (adjust these to your actual paths)
    json_path = Path("data/sample_invoice.json")
    output_path = Path("output/generated_invoice.xlsx")
    template_dir = Path("src/invoice_generator/TEMPLATE")
    config_dir = Path("src/invoice_generator/config")
    
    try:
        # Strategy-style usage (simpler interface)
        result = generate_invoice(
            json_file_path=json_path,
            output_file_path=output_path,
            flags=['DAF'],  # Enable DAF processing
            template_dir=template_dir,
            config_dir=config_dir,
            verbose=True
        )
        
        print(f"✅ Invoice generated successfully!")
        print(f"📄 Output: {result['output_path']}")
        print(f"⏱️  Duration: {result['duration']:.2f}s")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")


def example_direct_api_usage():
    """Example of using the direct API function"""
    
    # Example paths
    json_file = "data/sample_invoice.json"
    output_file = "output/generated_invoice.xlsx"
    
    # Direct API usage with full control
    result = generate_invoice_api(
        input_data_file=json_file,
        output_file=output_file,
        template_dir="src/invoice_generator/TEMPLATE",
        config_dir="src/invoice_generator/config",
        enable_daf=True,
        enable_custom=False,
        verbose=True
    )
    
    if result['success']:
        print(f"✅ Success! Generated: {result['output_path']}")
        print(f"⏱️  Time taken: {result['duration']:.2f} seconds")
        if result['warnings']:
            print(f"⚠️  Warnings: {result['warnings']}")
    else:
        print(f"❌ Failed: {result['error']}")


def example_batch_processing():
    """Example of processing multiple invoices"""
    
    invoice_files = [
        "data/invoice1.json",
        "data/invoice2.json", 
        "data/invoice3.json"
    ]
    
    results = []
    
    for json_file in invoice_files:
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"⏭️  Skipping {json_file} (not found)")
            continue
            
        output_path = Path(f"output/{json_path.stem}_generated.xlsx")
        
        try:
            result = generate_invoice(
                json_file_path=json_path,
                output_file_path=output_path,
                flags=[],
                verbose=False  # Quiet mode for batch processing
            )
            results.append(result)
            print(f"✅ {json_path.name} -> {output_path.name}")
            
        except Exception as e:
            print(f"❌ Failed to process {json_path.name}: {e}")
    
    print(f"\n📊 Batch complete: {len(results)} files processed")


if __name__ == "__main__":
    print("🚀 Invoice Generator API Examples")
    print("=" * 40)
    
    print("\n1. Strategy Usage Example:")
    print("-" * 25)
    # example_strategy_usage()  # Uncomment when you have sample data
    print("(Commented out - requires sample data)")
    
    print("\n2. Direct API Usage Example:")
    print("-" * 30)
    # example_direct_api_usage()  # Uncomment when you have sample data
    print("(Commented out - requires sample data)")
    
    print("\n3. Batch Processing Example:")
    print("-" * 30)
    # example_batch_processing()  # Uncomment when you have sample data
    print("(Commented out - requires sample data)")
    
    print("\n✨ API is ready to use!")
    print("📚 Uncomment examples above when you have sample data files.")