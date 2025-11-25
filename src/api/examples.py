#!/usr/bin/env python3
"""
Invoice Generator API - Usage Examples
Demonstrates how to use the API from different clients
"""

import requests
import json
import base64
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class InvoiceAPIClient:
    """Client for Invoice Generator API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
    
    def health_check(self):
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def list_templates(self):
        """Get available templates"""
        response = requests.get(f"{self.base_url}/templates")
        return response.json()
    
    def generate_from_json_data(self, invoice_data: dict, template_type: str = None, **options):
        """Generate invoice from JSON data"""
        payload = {
            "invoice_data": invoice_data,
            "template_type": template_type,
            "options": options
        }
        
        response = requests.post(
            f"{self.base_url}/invoice/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def generate_from_file(self, json_file: Path, template_type: str = None, **options):
        """Generate invoice from JSON file"""
        with open(json_file, 'rb') as f:
            files = {'invoice_data': (json_file.name, f, 'application/json')}
            data = {
                'template_type': template_type,
                **options
            }
            
            response = requests.post(
                f"{self.base_url}/invoice/generate/upload",
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def save_generated_file(self, api_response: dict, output_path: Path):
        """Save generated Excel file from API response"""
        if api_response.get('success') and 'result' in api_response:
            file_data = api_response['result']['file_data']
            excel_bytes = base64.b64decode(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(excel_bytes)
            
            return output_path
        else:
            raise ValueError("Invalid API response or generation failed")

# Example Usage Functions

def example_1_json_payload():
    """Example 1: Generate invoice using JSON payload"""
    print("📋 Example 1: JSON Payload")
    print("-" * 30)
    
    client = InvoiceAPIClient()
    
    # Sample invoice data (simplified)
    invoice_data = {
        "metadata": {
            "workbook_filename": "CLW250039.xlsx",
            "worksheet_name": "Sheet1",
            "timestamp": "2025-10-08T12:54:23"
        },
        "processed_tables_data": {
            "1": {
                "po": ["PT25P82", "PT26797"],
                "item": [140489, 140519],
                "desc": ["Buffalo Steel", "ModMax Black"],
                "sqft": [2750.1, 11032.5]
            }
        },
        "standard_aggregation_results": {
            "('PT25P82', 140489, 0.9, None)": {"sqft": 17706.2, "amount": 15935.58}
        }
    }
    
    try:
        # Generate invoice
        result = client.generate_from_json_data(
            invoice_data=invoice_data,
            template_type="CLW",
            enable_daf=False,
            verbose=True
        )
        
        if result['success']:
            print(f"✅ Success! Request ID: {result['request_id']}")
            print(f"📁 File size: {result['result']['file_size']:,} bytes")
            print(f"⏱️ Processing time: {result['metadata']['processing_duration']:.2f}s")
            
            # Save file
            output_path = Path("generated_invoice_example1.xlsx")
            client.save_generated_file(result, output_path)
            print(f"💾 Saved to: {output_path}")
        else:
            print(f"❌ Failed: {result['error']['message']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_2_file_upload():
    """Example 2: Generate invoice using file upload"""
    print("\n📋 Example 2: File Upload")
    print("-" * 30)
    
    client = InvoiceAPIClient()
    
    # Use existing test file
    json_file = Path("data/invoices_to_process/CLW250039.json")
    
    if not json_file.exists():
        print(f"❌ Test file not found: {json_file}")
        return
    
    try:
        # Generate invoice
        result = client.generate_from_file(
            json_file=json_file,
            template_type="CLW",
            enable_daf=False,
            enable_custom=False
        )
        
        if result['success']:
            print(f"✅ Success! Request ID: {result['request_id']}")
            print(f"📁 File size: {result['result']['file_size']:,} bytes")
            print(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
            
            # Save file
            output_path = Path("generated_invoice_example2.xlsx")
            client.save_generated_file(result, output_path)
            print(f"💾 Saved to: {output_path}")
        else:
            print(f"❌ Failed: {result['error']['message']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_3_batch_processing():
    """Example 3: Batch processing multiple invoices"""
    print("\n📋 Example 3: Batch Processing")
    print("-" * 30)
    
    client = InvoiceAPIClient()
    
    # Find all JSON files
    data_dir = Path("data/invoices_to_process")
    json_files = list(data_dir.glob("*.json")) if data_dir.exists() else []
    
    if not json_files:
        print("❌ No JSON files found for batch processing")
        return
    
    results = []
    for json_file in json_files[:2]:  # Process first 2 files
        try:
            print(f"🔄 Processing: {json_file.name}")
            
            result = client.generate_from_file(
                json_file=json_file,
                enable_daf=False,
                verbose=False  # Quiet mode for batch
            )
            
            if result['success']:
                # Save file
                output_path = Path(f"batch_{json_file.stem}_generated.xlsx")
                client.save_generated_file(result, output_path)
                
                results.append({
                    'input': json_file.name,
                    'output': output_path.name,
                    'success': True,
                    'size': result['result']['file_size'],
                    'time': result.get('processing_time', 0)
                })
                print(f"  ✅ Generated: {output_path.name}")
            else:
                results.append({
                    'input': json_file.name,
                    'success': False,
                    'error': result['error']['message']
                })
                print(f"  ❌ Failed: {result['error']['message']}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Summary
    print(f"\n📊 Batch Summary:")
    successful = sum(1 for r in results if r['success'])
    print(f"  Processed: {len(results)} files")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")

def example_4_curl_commands():
    """Example 4: cURL command examples"""
    print("\n📋 Example 4: cURL Commands")
    print("-" * 30)
    
    print("# Health check")
    print("curl -X GET http://localhost:8000/api/v1/health")
    print()
    
    print("# List templates")
    print("curl -X GET http://localhost:8000/api/v1/templates")
    print()
    
    print("# Generate from JSON payload")
    print('''curl -X POST http://localhost:8000/api/v1/invoice/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "invoice_data": {
      "metadata": {"workbook_filename": "test.xlsx"},
      "processed_tables_data": {"1": {"po": ["PT001"]}}
    },
    "template_type": "CLW",
    "options": {"enable_daf": false}
  }' ''')
    print()
    
    print("# Generate from file upload")
    print('''curl -X POST http://localhost:8000/api/v1/invoice/generate/upload \\
  -F "invoice_data=@data/invoices_to_process/CLW250039.json" \\
  -F "template_type=CLW" \\
  -F "enable_daf=false"''')

if __name__ == "__main__":
    print("🚀 Invoice Generator API - Usage Examples")
    print("=" * 50)
    
    # Run examples (comment out API calls if server not running)
    try:
        client = InvoiceAPIClient()
        health = client.health_check()
        print(f"✅ API is healthy: {health['status']}")
        
        # Uncomment to run examples:
        # example_1_json_payload()
        # example_2_file_upload() 
        # example_3_batch_processing()
        
    except requests.exceptions.ConnectionError:
        print("⚠️ API server not running. Showing cURL examples instead:")
        
    example_4_curl_commands()
    
    print("\n🔗 API Documentation:")
    print("  - Swagger UI: http://localhost:8000/api/docs")
    print("  - ReDoc: http://localhost:8000/api/redoc")