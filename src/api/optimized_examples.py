#!/usr/bin/env python3
"""
Optimized API Usage - Raw Excel File Downloads
Much simpler and more efficient!
"""

import requests
from pathlib import Path
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def example_1_direct_download():
    """Example 1: Get Excel file directly - NO BASE64!"""
    print("📋 Example 1: Direct Excel Download")
    print("-" * 40)
    
    # Sample invoice data
    invoice_data = {
        "metadata": {"workbook_filename": "CLW250039.xlsx"},
        "processed_tables_data": {
            "1": {
                "po": ["PT25P82", "PT26797"],
                "item": [140489, 140519],
                "desc": ["Buffalo Steel", "ModMax Black"],
                "sqft": [2750.1, 11032.5]
            }
        }
    }
    
    # Send request
    response = requests.post(
        f"{API_BASE_URL}/invoice/generate",
        json={
            "invoice_data": invoice_data,
            "template_type": "CLW"
        }
    )
    
    if response.status_code == 200:
        # Save Excel file directly!
        output_file = Path("direct_download.xlsx")
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {output_file}")
        print(f"📁 Size: {output_file.stat().st_size:,} bytes")
        print(f"🕒 Processing time: {response.headers.get('X-Processing-Time', 'unknown')}s")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

def example_2_file_upload_direct():
    """Example 2: Upload JSON, download Excel directly"""
    print("\n📋 Example 2: File Upload → Direct Excel")
    print("-" * 40)
    
    json_file = Path("data/invoices_to_process/CLW250039.json")
    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return
    
    # Upload and get Excel back
    with open(json_file, 'rb') as f:
        files = {'invoice_data': (json_file.name, f, 'application/json')}
        
        response = requests.post(
            f"{API_BASE_URL}/invoice/generate/upload",
            files=files,
            data={'template_type': 'CLW'}
        )
    
    if response.status_code == 200:
        # Get filename from headers
        content_disp = response.headers.get('content-disposition', '')
        filename = 'uploaded_invoice.xlsx'
        if 'filename=' in content_disp:
            filename = content_disp.split('filename=')[1].strip('"')
        
        # Save Excel file
        output_file = Path(filename)
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Generated: {output_file}")
        print(f"📁 Size: {output_file.stat().st_size:,} bytes")
    else:
        print(f"❌ Failed: {response.status_code}")

def example_3_curl_commands():
    """Example 3: cURL commands for raw downloads"""
    print("\n📋 Example 3: cURL Commands (Raw Downloads)")
    print("-" * 50)
    
    print("# Download Excel directly from JSON payload:")
    print('''curl -X POST http://localhost:8000/api/v1/invoice/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "invoice_data": {
      "metadata": {"workbook_filename": "test.xlsx"},
      "processed_tables_data": {"1": {"po": ["PT001"]}}
    },
    "template_type": "CLW"
  }' \\
  --output generated_invoice.xlsx''')
    
    print("\n# Upload JSON file and download Excel:")
    print('''curl -X POST http://localhost:8000/api/v1/invoice/generate/upload \\
  -F "invoice_data=@data/invoices_to_process/CLW250039.json" \\
  -F "template_type=CLW" \\
  --output CLW250039_generated.xlsx''')
    
    print("\n# Stream large files:")
    print('''curl -X POST http://localhost:8000/api/v1/invoice/generate/stream \\
  -H "Content-Type: application/json" \\
  -d '{"invoice_data": {...}}' \\
  --output streamed_invoice.xlsx''')

def example_4_javascript_fetch():
    """Example 4: JavaScript fetch for web applications"""
    print("\n📋 Example 4: JavaScript Fetch API")
    print("-" * 40)
    
    js_code = '''
// JavaScript example for downloading Excel files
async function generateInvoice(invoiceData) {
    const response = await fetch('/api/v1/invoice/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            invoice_data: invoiceData,
            template_type: 'CLW'
        })
    });
    
    if (response.ok) {
        // Get filename from headers
        const contentDisp = response.headers.get('content-disposition');
        const filename = contentDisp 
            ? contentDisp.split('filename=')[1].replace(/"/g, '')
            : 'invoice.xlsx';
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log(`✅ Downloaded: ${filename}`);
    } else {
        console.error('❌ Generation failed:', response.status);
    }
}

// Usage
const invoiceData = {
    metadata: { workbook_filename: "CLW250039.xlsx" },
    processed_tables_data: { "1": { po: ["PT25P82"] } }
};

generateInvoice(invoiceData);
'''
    
    print(js_code)

def example_5_python_requests_batch():
    """Example 5: Python batch processing"""
    print("\n📋 Example 5: Batch Processing")
    print("-" * 40)
    
    data_dir = Path("data/invoices_to_process")
    json_files = list(data_dir.glob("*.json")) if data_dir.exists() else []
    
    if not json_files:
        print("❌ No JSON files found")
        return
    
    print(f"🔄 Processing {len(json_files)} files...")
    
    for json_file in json_files:
        try:
            # Upload and download
            with open(json_file, 'rb') as f:
                files = {'invoice_data': (json_file.name, f, 'application/json')}
                
                response = requests.post(
                    f"{API_BASE_URL}/invoice/generate/upload",
                    files=files,
                    timeout=30  # 30 second timeout
                )
            
            if response.status_code == 200:
                output_file = Path(f"batch_{json_file.stem}.xlsx")
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"  ✅ {json_file.name} → {output_file.name} ({output_file.stat().st_size:,} bytes)")
            else:
                print(f"  ❌ {json_file.name} failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {json_file.name} error: {e}")

if __name__ == "__main__":
    print("🚀 Optimized API Usage Examples")
    print("=" * 50)
    print("✨ Raw Excel downloads - NO base64 encoding!")
    print("✨ Much faster and more efficient!")
    print()
    
    # Show examples (comment out actual API calls if server not running)
    try:
        # Test if API is running
        response = requests.get(f"{API_BASE_URL}/../health", timeout=2)
        print("✅ API server is running")
        
        # Uncomment to run examples:
        # example_1_direct_download()
        # example_2_file_upload_direct()
        # example_5_python_requests_batch()
        
    except requests.exceptions.RequestException:
        print("⚠️ API server not running. Showing examples only.")
    
    example_3_curl_commands()
    example_4_javascript_fetch()
    
    print("\n🎯 Benefits of Raw Binary Response:")
    print("  ✅ No base64 encoding/decoding overhead")
    print("  ✅ ~25% smaller response size")
    print("  ✅ Faster processing and downloads")
    print("  ✅ Direct file downloads in browsers")
    print("  ✅ Simpler client code")
'''