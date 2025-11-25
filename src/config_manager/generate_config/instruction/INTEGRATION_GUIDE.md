# Integration Guide

This guide explains how to use the Config Generator from another main application or different directory.

## 🎯 Integration Options

### Option 1: Using the Wrapper Class (Recommended)

The easiest way to integrate Config Generator into your application:

```python
from config_generator_wrapper import ConfigGeneratorWrapper

# Initialize wrapper (auto-detects config_gen location)
wrapper = ConfigGeneratorWrapper()

# Or specify the path explicitly
wrapper = ConfigGeneratorWrapper("/path/to/config_gen")

# Generate configuration
success, output_path, info = wrapper.generate_config("your_data.json")

if success:
    print(f"Generated config: {output_path}")
else:
    print(f"Error: {output_path}")
```

### Option 2: Simple Function

For basic usage with minimal setup:

```python
from config_generator_wrapper import generate_config_simple

success, message = generate_config_simple(
    quantity_data_path="your_data.json",
    config_gen_path="/path/to/config_gen"  # Optional
)

print(message)
```

### Option 3: Direct Module Import

For advanced usage with full control:

```python
import sys
sys.path.append('/path/to/config_gen')

from config_generator.config_generator import ConfigGenerator

generator = ConfigGenerator()
generator.generate_config(
    template_path="/path/to/config_gen/sample_config.json",
    quantity_data_path="your_data.json",
    output_path="output_config.json"
)
```

## 📁 Directory Structure Examples

### Example 1: Config Gen as Subdirectory

```
your_main_project/
├── main.py
├── config_gen/                    # Config Generator here
│   ├── generate_config.bat
│   ├── sample_config.json
│   ├── mapping_config.json
│   ├── config_generator/
│   └── config_generator_wrapper.py
└── data/
    └── quantity_data.json
```

**Usage in main.py:**
```python
from config_gen.config_generator_wrapper import ConfigGeneratorWrapper

wrapper = ConfigGeneratorWrapper("./config_gen")
success, output, info = wrapper.generate_config("./data/quantity_data.json")
```

### Example 2: Config Gen as Sibling Directory

```
parent_directory/
├── your_main_project/
│   ├── main.py
│   └── data/
│       └── quantity_data.json
└── config_gen/                    # Config Generator here
    ├── generate_config.bat
    ├── sample_config.json
    └── config_generator_wrapper.py
```

**Usage in main.py:**
```python
from config_generator_wrapper import ConfigGeneratorWrapper

wrapper = ConfigGeneratorWrapper("../config_gen")
success, output, info = wrapper.generate_config("./data/quantity_data.json")
```

### Example 3: Config Gen in Different Location

```
C:/tools/config_gen/               # Config Generator here
C:/projects/your_project/
├── main.py
└── data/
    └── quantity_data.json
```

**Usage in main.py:**
```python
from config_generator_wrapper import ConfigGeneratorWrapper

wrapper = ConfigGeneratorWrapper("C:/tools/config_gen")
success, output, info = wrapper.generate_config("./data/quantity_data.json")
```

## 🔧 Complete Integration Example

Here's a complete example of integrating Config Generator into your main application:

```python
#!/usr/bin/env python3
"""
Example main application using Config Generator.
"""

import os
import sys
from pathlib import Path

# Add config_gen to path (adjust path as needed)
config_gen_path = Path(__file__).parent / "config_gen"
sys.path.append(str(config_gen_path))

from config_generator_wrapper import ConfigGeneratorWrapper


class MyMainApplication:
    def __init__(self):
        # Initialize Config Generator wrapper
        self.config_generator = ConfigGeneratorWrapper(str(config_gen_path))
        
    def process_client_data(self, client_name: str, data_file: str):
        """Process data for a specific client."""
        print(f"Processing data for {client_name}...")
        
        # Generate output path
        output_dir = Path("output") / client_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{client_name}_config.json"
        
        # Generate configuration
        success, result, info = self.config_generator.generate_config(
            quantity_data_path=data_file,
            output_path=str(output_path)
        )
        
        if success:
            print(f"✅ Generated config for {client_name}: {result}")
            return str(result)
        else:
            print(f"❌ Failed to generate config for {client_name}: {result}")
            return None
    
    def add_client_mappings(self, client_mappings: dict):
        """Add client-specific mappings."""
        for sheet_mapping in client_mappings.get("sheets", []):
            self.config_generator.add_sheet_mapping(
                sheet_mapping["from"], 
                sheet_mapping["to"]
            )
        
        for header_mapping in client_mappings.get("headers", []):
            self.config_generator.add_header_mapping(
                header_mapping["from"], 
                header_mapping["to"]
            )
    
    def batch_process(self, data_files: list):
        """Process multiple data files."""
        results = []
        
        for data_file in data_files:
            client_name = Path(data_file).stem
            result = self.process_client_data(client_name, data_file)
            results.append({"client": client_name, "config": result})
        
        return results


def main():
    """Main application entry point."""
    app = MyMainApplication()
    
    # Example: Add custom mappings for a specific client
    client_mappings = {
        "sheets": [
            {"from": "INVOICE_2024", "to": "Invoice"},
            {"from": "PACK_LIST", "to": "Packing list"}
        ],
        "headers": [
            {"from": "TOTAL AMOUNT", "to": "col_amount"},
            {"from": "ITEM CODE", "to": "col_item"}
        ]
    }
    app.add_client_mappings(client_mappings)
    
    # Example: Process single file
    config_path = app.process_client_data("client1", "data/client1_data.json")
    
    # Example: Batch process multiple files
    data_files = [
        "data/client1_data.json",
        "data/client2_data.json",
        "data/client3_data.json"
    ]
    results = app.batch_process(data_files)
    
    print(f"Processed {len(results)} files")
    for result in results:
        print(f"  {result['client']}: {result['config']}")


if __name__ == "__main__":
    main()
```

## 🛠️ Advanced Integration Features

### Error Handling

```python
try:
    wrapper = ConfigGeneratorWrapper("/path/to/config_gen")
    success, output, info = wrapper.generate_config("data.json")
    
    if not success:
        # Handle generation errors
        error_info = info
        print(f"Error type: {error_info.get('error_type')}")
        print(f"Error message: {error_info.get('error')}")
        
except RuntimeError as e:
    # Handle setup errors (missing files, etc.)
    print(f"Setup error: {e}")
```

### Dynamic Mapping Management

```python
# Check current mappings
mappings = wrapper.get_mappings()
print(f"Sheet mappings: {len(mappings['sheet_mappings'])}")
print(f"Header mappings: {len(mappings['header_mappings'])}")

# Add mappings based on data analysis
if "unrecognized_items" in mappings:
    for item in mappings["unrecognized_items"]:
        if item.startswith("Sheet:"):
            sheet_name = item.split(":", 1)[1]
            # Add logic to determine correct mapping
            wrapper.add_sheet_mapping(sheet_name, "Invoice")
```

### Validation Before Processing

```python
# Validate data before processing
is_valid, message = wrapper.validate_quantity_data("data.json")

if is_valid:
    success, output, info = wrapper.generate_config("data.json")
else:
    print(f"Data validation failed: {message}")
```

## 📋 Integration Checklist

### Before Integration
- [ ] Ensure Python 3.7+ is available
- [ ] Verify all Config Generator files are present
- [ ] Test Config Generator standalone first

### During Integration
- [ ] Choose appropriate integration method
- [ ] Handle file paths correctly (absolute vs relative)
- [ ] Implement proper error handling
- [ ] Test with sample data

### After Integration
- [ ] Verify generated configs are correct
- [ ] Test with various data formats
- [ ] Document any custom mappings needed
- [ ] Set up monitoring/logging if needed

## 🚨 Common Issues and Solutions

### Issue: "Module not found"
**Solution**: Ensure config_gen path is added to sys.path correctly

### Issue: "File not found" errors
**Solution**: Use absolute paths or ensure working directory is correct

### Issue: Mappings not persisting
**Solution**: Ensure mapping_config.json is writable and in correct location

### Issue: Generated configs are empty/incorrect
**Solution**: Verify quantity data format and template compatibility

---

The Config Generator is designed to be easily integrated into larger applications while maintaining its flexibility and ease of use. Choose the integration method that best fits your application's architecture and requirements.