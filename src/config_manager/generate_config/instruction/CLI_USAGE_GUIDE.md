# Config Generator CLI Usage Guide

## 🚀 Quick Start

The CLI takes your quantity analysis data and generates a fully working configuration file by updating the template with your specific values while preserving all business logic.

### Basic Usage
```bash
# Generate config from your quantity data
python generate_config_ascii.py quantity_mode_analysis.json
```

This will:
- ✅ Load your quantity analysis data
- ✅ Update the template with your specific values  
- ✅ Preserve all business logic and configurations
- ✅ Generate a complete, ready-to-use config file

## 📋 Command Options

### Required Arguments
- `quantity_data` - Path to your quantity analysis JSON file

### Optional Arguments
- `-t, --template` - Template file path (default: sample_config.json)
- `-o, --output` - Output file path (default: auto-generated)
- `-v, --verbose` - Show detailed processing information
- `-q, --quiet` - Only show errors
- `--validate-only` - Only validate files without generating output
- `--show-info` - Show information about your quantity data

## 💡 Usage Examples

### 1. Basic Generation
```bash
python generate_config_ascii.py quantity_mode_analysis.json
```
**Output:** `quantity_mode_analysis_config.json`

### 2. Custom Output File
```bash
python generate_config_ascii.py quantity_mode_analysis.json -o my_config.json
```
**Output:** `my_config.json`

### 3. Custom Template
```bash
python generate_config_ascii.py my_data.json -t my_template.json -o output.json
```

### 4. Show Data Information
```bash
python generate_config_ascii.py quantity_mode_analysis.json --show-info
```
**Shows:** Sheet details, fonts, headers, start rows

### 5. Validate Files Only
```bash
python generate_config_ascii.py quantity_mode_analysis.json --validate-only
```
**Checks:** File validity without generating output

### 6. Verbose Mode
```bash
python generate_config_ascii.py quantity_mode_analysis.json -v
```
**Shows:** Detailed processing steps

### 7. Quiet Mode
```bash
python generate_config_ascii.py quantity_mode_analysis.json -q
```
**Shows:** Only errors

## 📊 What the CLI Does

### Input Processing
1. **Loads Template** - Reads `sample_config.json` (or custom template)
2. **Loads Quantity Data** - Reads your quantity analysis JSON
3. **Validates Structure** - Ensures both files are valid

### Configuration Generation
1. **Updates Start Rows** - Sets correct data starting positions
2. **Updates Fonts** - Applies font information from your data
3. **Updates Headers** - Maps header texts to correct positions
4. **Preserves Business Logic** - Keeps all mappings, formulas, styling

### Output
- **Complete Configuration** - Ready-to-use JSON file
- **Preserved Structure** - All template business logic intact
- **Updated Values** - Your specific data applied

## 📈 Example Output

```
[OK] Quantity data loaded: 3 sheets found
[OK] Template loaded: 3 sheet configurations

[GENERATING] Starting configuration generation...
[TEMPLATE] sample_config.json
[DATA] quantity_mode_analysis.json
[OUTPUT] quantity_mode_analysis_config.json

[SUCCESS] Configuration generated successfully!
[SAVED] Output saved to: quantity_mode_analysis_config.json

[SUMMARY] Generation Summary:
[PROCESSED] 3 sheets
[UPDATES] Applied:
  [UPDATED] Contract: start_row -> 18
  [UPDATED] Contract: fonts -> Times New Roman
  [UPDATED] Invoice: start_row -> 21
  [UPDATED] Invoice: fonts -> Times New Roman
  [UPDATED] Packing list: start_row -> 22
  [UPDATED] Packing list: fonts -> Times New Roman
[PRESERVED] Business logic: mappings, formulas, styling rules
[READY] Configuration is complete and valid
```

## 🔍 Data Information Example

```bash
python generate_config_ascii.py quantity_mode_analysis.json --show-info
```

```
[INFO] Quantity Data Information:
[FILE] quantity_mode_analysis.json
[SOURCE] C:\path\to\CT&INV&PL JLFHLZN25009 FCA.xlsx
[TIME] 2025-07-19T16:08:19.374269
[SHEETS] 3 sheets found

  [SHEET] Contract:
    [START_ROW] 18
    [HEADER_FONT] Times New Roman 10.0pt
    [DATA_FONT] Times New Roman 10.0pt
    [HEADERS] 6 positions
      - Cargo Descprition
      - HL ITEM
      - Quantity
      - ... and 3 more

  [SHEET] Invoice:
    [START_ROW] 21
    [HEADER_FONT] Times New Roman 12.0pt
    [DATA_FONT] Times New Roman 12.0pt
    [HEADERS] 7 positions
      - Mark & Nº
      - P.O. Nº
      - ITEM Nº
      - ... and 4 more
```

## ⚠️ Error Handling

### Common Errors and Solutions

**File Not Found:**
```
[ERROR] Quantity data file not found: my_data.json
```
**Solution:** Check file path and ensure file exists

**Invalid JSON:**
```
[ERROR] Invalid JSON in quantity data file: Expecting ',' delimiter
```
**Solution:** Validate JSON format using a JSON validator

**Missing Template:**
```
[ERROR] Template file not found: sample_config.json
[TIP] Make sure you have sample_config.json in the current directory
```
**Solution:** Ensure template file is in the correct location

**Invalid Structure:**
```
[ERROR] Invalid quantity data format: missing 'sheets' key
```
**Solution:** Ensure quantity data has the correct structure

## 🛠️ Batch Scripts

### Windows (generate_config.bat)
```batch
generate_config.bat quantity_mode_analysis.json
```

### Unix/Linux/Mac (generate_config.sh)
```bash
./generate_config.sh quantity_mode_analysis.json
```

## 📁 File Structure

```
your_project/
├── generate_config_ascii.py    # Main CLI script
├── sample_config.json          # Template configuration
├── quantity_mode_analysis.json # Your quantity data
├── config_generator/           # Core modules
└── generated_config.json       # Output (created by CLI)
```

## 🎯 Best Practices

1. **Always validate first:**
   ```bash
   python generate_config_ascii.py your_data.json --validate-only
   ```

2. **Check your data:**
   ```bash
   python generate_config_ascii.py your_data.json --show-info
   ```

3. **Use descriptive output names:**
   ```bash
   python generate_config_ascii.py data.json -o project_config_v1.json
   ```

4. **Keep templates safe:**
   - Always backup your `sample_config.json`
   - Use version control for templates

5. **Verify output:**
   - Check generated files before using in production
   - Validate JSON structure

## 🚀 Ready to Use!

The CLI is now ready for production use. It will generate complete, working configurations from your quantity analysis data while preserving all business logic from your templates.

**Start with:**
```bash
python generate_config_ascii.py quantity_mode_analysis.json
```

Your configuration will be ready in seconds! 🎉