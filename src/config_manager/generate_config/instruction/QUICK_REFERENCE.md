# Config Generator - Quick Reference

## 🚀 Essential Commands

### Generate Configuration
```bash
# Basic generation
.\generate_config.bat your_data.json

# With custom output
python generate_config_ascii.py data.json -o custom_name.json

# Verbose mode (see details)
python generate_config_ascii.py data.json -v
```

### Manage Mappings
```bash
# List all current mappings
python add_mapping.py --list-mappings

# Add sheet name mapping
python add_mapping.py --add-sheet "ACTUAL_SHEET:Template Sheet"

# Add header text mapping
python add_mapping.py --add-header "ACTUAL_HEADER:col_id"
```

## 🔧 Common Column IDs

| Column ID | Purpose |
|-----------|---------|
| `col_po` | Purchase Order |
| `col_item` | Item Number |
| `col_dc` | Document/Delivery Code |
| `col_desc` | Description |
| `col_qty_sf` | Quantity (SF) |
| `col_unit_price` | Unit Price |
| `col_amount` | Total Amount |
| `col_net` | Net Weight |
| `col_gross` | Gross Weight |
| `col_cbm` | Cubic Meters |

## 🎯 Quick Fixes

### "Sheet not found" warning
```bash
python add_mapping.py --add-sheet "YOUR_SHEET:Invoice"
# or
python add_mapping.py --add-sheet "YOUR_SHEET:Packing list"
# or  
python add_mapping.py --add-sheet "YOUR_SHEET:Contract"
```

### "Unrecognized headers" warning
```bash
# Common examples:
python add_mapping.py --add-header "P.O NUMBER:col_po"
python add_mapping.py --add-header "ITEM CODE:col_item"
python add_mapping.py --add-header "TOTAL PRICE:col_amount"
python add_mapping.py --add-header "NET WEIGHT:col_net"
```

## 📋 Workflow Checklist

1. ✅ Run generator: `.\generate_config.bat data.json`
2. ✅ Check for warnings in output
3. ✅ Review mapping report: `data_config_mapping_report.txt`
4. ✅ Add missing mappings using `add_mapping.py`
5. ✅ Re-run generator
6. ✅ Verify output file is generated successfully

## 🔍 Debugging

```bash
# Validate input files
python generate_config_ascii.py data.json --validate-only

# Show data information
python generate_config_ascii.py data.json --show-info

# Verbose output for troubleshooting
python generate_config_ascii.py data.json -v
```

## 📁 File Locations

- **Input**: Your quantity data JSON files
- **Template**: `sample_config.json` (don't modify)
- **Mappings**: `mapping_config.json` (modify as needed)
- **Output**: `{input_name}_config.json`
- **Report**: `{input_name}_config_mapping_report.txt`

## 🆘 Emergency Commands

```bash
# Reset mappings to default
del mapping_config.json
python add_mapping.py --list-mappings  # This recreates default

# Check what's in your data
python generate_config_ascii.py data.json --show-info

# Validate everything is working
python generate_config_ascii.py data.json --validate-only
```