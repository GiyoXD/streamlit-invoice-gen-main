# Mapping Configuration Guide

This guide explains how to configure sheet name and header text mappings for the Config Generator system.

## Overview

The Config Generator now uses a flexible mapping system that allows you to manually configure how sheet names and header texts from your quantity analysis data are mapped to the template configuration.

## Files

- `mapping_config.json` - Main configuration file for all mappings
- `add_mapping.py` - Helper script to add new mappings
- `MAPPING_GUIDE.md` - This guide

## Quick Start

### 1. Check Current Mappings

```bash
python add_mapping.py --list-mappings
```

### 2. Add a New Sheet Name Mapping

When you have a new sheet name in your quantity data that doesn't match the template:

```bash
python add_mapping.py --add-sheet "NEW_SHEET_NAME:Template Sheet Name"
```

Examples:
```bash
python add_mapping.py --add-sheet "INVOICE_2024:Invoice"
python add_mapping.py --add-sheet "PACK_LIST:Packing list"
python add_mapping.py --add-sheet "CONTRACT_NEW:Contract"
```

### 3. Add a New Header Text Mapping

When you encounter new header texts that need to be mapped to column IDs:

```bash
python add_mapping.py --add-header "Header Text:col_id"
```

Examples:
```bash
python add_mapping.py --add-header "TOTAL AMOUNT USD:col_amount"
python add_mapping.py --add-header "ITEM NUMBER:col_item"
python add_mapping.py --add-header "NET WEIGHT KG:col_net"
```

## Common Column IDs

Here are the standard column IDs used in the template:

| Column ID | Purpose |
|-----------|---------|
| `col_static` | Mark & Number column |
| `col_po` | Purchase Order number |
| `col_item` | Item number |
| `col_dc` | Document/Delivery code |
| `col_desc` | Description |
| `col_qty_sf` | Quantity in square feet |
| `col_qty_pcs` | Quantity in pieces |
| `col_unit_price` | Unit price |
| `col_amount` | Total amount |
| `col_net` | Net weight |
| `col_gross` | Gross weight |
| `col_cbm` | Cubic meters |
| `col_pallet` | Pallet number |
| `col_remarks` | Remarks |
| `col_no` | Sequential number |

## Workflow for New Files

When you encounter a new Excel file with different sheet names or headers:

### Step 1: Run the Config Generator

```bash
.\generate_config.bat your_new_file.json
```

### Step 2: Check for Warnings

Look for warnings like:
```
Warning: Unrecognized headers found: ['Sheet:HEADER_NAME', ...]
Warning: Missing font data for sheets: ['SHEET_NAME']
```

### Step 3: Check the Mapping Report

A mapping report will be generated automatically (e.g., `your_new_file_config_mapping_report.txt`). Review this file for:
- Unrecognized sheet names
- Unrecognized header texts
- Suggestions for similar mappings

### Step 4: Add Missing Mappings

Based on the report, add the necessary mappings:

```bash
# Add sheet mappings
python add_mapping.py --add-sheet "ACTUAL_SHEET_NAME:Template Sheet Name"

# Add header mappings
python add_mapping.py --add-header "ACTUAL_HEADER_TEXT:col_appropriate_id"
```

### Step 5: Re-run the Config Generator

```bash
.\generate_config.bat your_new_file.json
```

The warnings should be reduced or eliminated.

## Manual Configuration

You can also edit `mapping_config.json` directly:

```json
{
  "sheet_name_mappings": {
    "mappings": {
      "INV": "Invoice",
      "YOUR_NEW_SHEET": "Invoice"
    }
  },
  "header_text_mappings": {
    "mappings": {
      "P.O Nº": "col_po",
      "YOUR_NEW_HEADER": "col_appropriate_id"
    }
  }
}
```

## Advanced Features

### Fallback Strategies

The system includes intelligent fallback strategies:

- **Case-insensitive matching**: "invoice" matches "INVOICE"
- **Partial matching**: Similar text gets suggested (configurable threshold)
- **Pattern matching**: Common patterns like "P.O" variations are automatically detected

### Configuration Options

In `mapping_config.json`, you can configure:

```json
{
  "fallback_strategies": {
    "case_insensitive_matching": true,
    "partial_matching_threshold": 0.7,
    "log_unrecognized_items": true,
    "create_suggestions": true
  }
}
```

## Troubleshooting

### Problem: Sheet not found
**Solution**: Add a sheet name mapping
```bash
python add_mapping.py --add-sheet "ACTUAL_NAME:Template Name"
```

### Problem: Headers not updating
**Solution**: Add header text mappings
```bash
python add_mapping.py --add-header "ACTUAL_HEADER:col_id"
```

### Problem: Too many warnings
**Solution**: 
1. Generate a mapping report: `python add_mapping.py --generate-report report.txt`
2. Review the report for patterns
3. Add mappings in bulk by editing `mapping_config.json`

### Problem: Wrong column mapping
**Solution**: Update the mapping
```bash
python add_mapping.py --add-header "HEADER_TEXT:correct_col_id"
```

## Best Practices

1. **Use descriptive names**: Make sheet and header mappings clear
2. **Follow conventions**: Use standard `col_*` format for column IDs
3. **Test incrementally**: Add a few mappings, test, then add more
4. **Keep backups**: Save your `mapping_config.json` file
5. **Document patterns**: Note common variations for future reference

## Examples

### Example 1: New Invoice Format

Quantity data has sheet "INV_2024" with headers:
- "P.O NUMBER"
- "ITEM CODE"
- "TOTAL VALUE"

Add mappings:
```bash
python add_mapping.py --add-sheet "INV_2024:Invoice"
python add_mapping.py --add-header "P.O NUMBER:col_po"
python add_mapping.py --add-header "ITEM CODE:col_item"
python add_mapping.py --add-header "TOTAL VALUE:col_amount"
```

### Example 2: Different Language Headers

For headers in different languages or formats:
```bash
python add_mapping.py --add-header "Numéro P.O:col_po"
python add_mapping.py --add-header "Quantité:col_qty_sf"
python add_mapping.py --add-header "Prix unitaire:col_unit_price"
```

This flexible system allows you to handle any variation in sheet names and header texts without modifying the code!