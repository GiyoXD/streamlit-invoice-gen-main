# Usage Guide - Automated Invoice Config Generator

## Quick Start

Generate a configuration from an Excel file:
```bash
python main.py path/to/your/invoice.xlsx
```

## Basic Commands

### Generate Configuration (Default)
```bash
python main.py invoice.xlsx
```
- Creates: `invoice_config.json`
- Creates: `invoice_headers_found.txt`

### Specify Output File
```bash
python main.py invoice.xlsx -o my_config.json
```

### Use Custom Template
```bash
python main.py invoice.xlsx -t path/to/template.json
```

## Advanced Options

### Interactive Mode
Add missing header mappings interactively:
```bash
python main.py invoice.xlsx --interactive
```

### Generate Processed XLSX
Create a processed Excel file with text replacement and row removal:
```bash
python main.py invoice.xlsx --generate-xlsx
```

### Specify XLSX Output
```bash
python main.py invoice.xlsx --generate-xlsx --xlsx-output processed.xlsx
```

### Verbose Output
See detailed processing information:
```bash
python main.py invoice.xlsx -v
```

### Keep Intermediate Files
Keep the analysis JSON file:
```bash
python main.py invoice.xlsx --keep-intermediate
```

## Complete Example

```bash
python main.py "CT&INV&PL MT2-25005E DAP.xlsx" \
  -o final_config.json \
  --interactive \
  --generate-xlsx \
  --xlsx-output processed.xlsx \
  -v
```

## What It Does

1. **Analyzes** your Excel file to extract structure, fonts, and data positions
2. **Generates** a configuration file based on the analysis and template
3. **Creates** a header log showing which headers were found and mapped
4. **Optionally** processes the Excel file with:
   - **Enhanced text replacement** using circular pattern checking
   - **Row removal** with merge restoration
   - **Intelligent label detection** for unusual positioning

## Output Files

- `*_config.json` - Final configuration file
- `*_headers_found.txt` - Header analysis and mapping status
- `*_processed.xlsx` - Processed Excel file (if --generate-xlsx used)

## Enhanced Text Replacement Features

The new enhanced text replacement uses **circular pattern checking** to find the correct target cell:

- **Intelligent positioning**: Checks adjacent cells in priority order (right, below, above, diagonal)
- **Content-aware scoring**: Evaluates cells based on their content suitability
- **Flexible label matching**: Works with unusual label positions and foreign languages
- **Pattern-based detection**: Uses regex patterns to identify different data types

### Test the Enhanced Features

Run the demo to see how it works:
```bash
python demo_enhanced_text_replacement.py
```

## Need Help?

Check the header log file to see which headers need mapping, then use interactive mode or manually add mappings to `mapping_config.json`. 