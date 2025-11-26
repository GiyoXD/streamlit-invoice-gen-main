
import json
import pprint

file_path = 'CLW250046.json'

try:
    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"--- Summaries for {file_path} ---")
    
    if 'processed_tables_data' in data:
        for table_key, table_data in data['processed_tables_data'].items():
            print(f"\nTable {table_key}:")
            print(f"  Keys: {list(table_data.keys())}")
            
            if 'leather_summary' in table_data:
                print("  Leather Summary:")
                pprint.pprint(table_data['leather_summary'], indent=4)
            else:
                print("  Leather Summary: Not found")
                
            if 'weight_summary' in table_data:
                print("  Weight Summary:")
                pprint.pprint(table_data['weight_summary'], indent=4)
            else:
                print("  Weight Summary: Not found")
                
            if 'pallet_summary_total' in table_data:
                print(f"  Pallet Summary Total: {table_data['pallet_summary_total']}")
            else:
                print("  Pallet Summary Total: Not found")
                
            if 'description' in table_data:
                print(f"  First 5 Descriptions: {table_data['description'][:5]}")
                
    else:
        print("No 'processed_tables_data' found in JSON.")

except Exception as e:
    print(f"Error reading JSON: {e}")
