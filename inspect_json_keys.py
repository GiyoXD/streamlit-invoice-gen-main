import json
import os

file_path = r'c:\Users\JPZ031127\Desktop\main_stream_lit_giyo\GENERATE_INVOICE_STREAMLIT_WEB\scripts\output\JF25057.json'

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Keys in {os.path.basename(file_path)}:")
    for key, value in data.items():
        value_type = type(value).__name__
        if isinstance(value, list):
            count = len(value)
            print(f"- {key}: List (Length: {count})")
            if count > 0:
                print(f"  Sample item type: {type(value[0]).__name__}")
        elif isinstance(value, dict):
            count = len(value)
            print(f"- {key}: Dict (Length: {count})")
        else:
            print(f"- {key}: {value_type}")

except Exception as e:
    print(f"Error reading file: {e}")
