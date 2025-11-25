# Config Generator

A powerful tool for generating Excel configuration files from quantity analysis data. This system automatically updates template configurations with your specific data while preserving all business logic and formatting rules.

## 🚀 Quick Start

1. **Generate a config from your quantity data:**
   ```bash
   .\generate_config.bat your_quantity_data.json
   ```

2. **If you see warnings about unrecognized items, add mappings:**
   ```bash
   python add_mapping.py --add-sheet "YOUR_SHEET:Template Sheet"
   python add_mapping.py --add-header "YOUR_HEADER:col_id"
   ```

3. **Re-run the generator:**
   ```bash
   .\generate_config.bat your_quantity_data.json
   ```

## 📁 Project Structure

```
config_gen/
├── generate_config.bat           # Main entry point (Windows)
├── generate_config_ascii.py      # CLI interface
├── mapping_config.json          # Mapping configuration
├── add_mapping.py              # Mapping management tool
├── sample_config.json          # Template configuration
├── config_generator/           # Core modules
│   ├── config_generator.py     # Main orchestrator
│   ├── mapping_manager.py      # Mapping system
│   ├── template_loader.py      # Template loading
│   ├── quantity_data_loader.py # Data loading
│   ├── header_text_updater.py  # Header updates
│   ├── font_updater.py         # Font updates
│   ├── position_updater.py     # Position updates
│   └── config_writer.py        # Output writing
├── README.md                   # Project overview (this file)
├── QUICK_REFERENCE.md          # Essential commands cheat sheet
├── USER_GUIDE.md              # Complete user guide
├── MAPPING_GUIDE.md           # Mapping configuration guide
├── SETUP.md                   # Installation instructions
└── CHANGELOG.md               # Version history
```

### 📖 Documentation Guide

**New to the system?** Start here:
1. **[SETUP.md](SETUP.md)** - Get the system running
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Learn essential commands
3. **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive usage guide

**Need to handle new Excel formats?**
- **[MAPPING_GUIDE.md](MAPPING_GUIDE.md)** - Configure mappings for any format

**Want to see what's changed?**
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and improvements

## 🎯 What It Does

The Config Generator takes your quantity analysis data (extracted from Excel files) and generates a complete, ready-to-use configuration file by:

- ✅ **Updating start row positions** based on your actual data
- ✅ **Updating font information** (names and sizes) from your Excel files
- ✅ **Updating header texts** with actual column headers
- ✅ **Preserving all business logic** (formulas, mappings, styling rules)
- ✅ **Maintaining template structure** (no manual editing required)

## 🔧 Key Features

### Intelligent Mapping System
- **Flexible sheet name mapping**: Handle any sheet name variation
- **Smart header text mapping**: Map any header text to the correct column
- **Automatic fallbacks**: Case-insensitive and pattern-based matching
- **Easy configuration**: Simple JSON configuration and command-line tools

### Robust Processing
- **Template preservation**: All business logic and formulas are maintained
- **Error handling**: Clear error messages and validation
- **Comprehensive reporting**: Detailed reports on what was updated
- **Batch processing**: Handle multiple files efficiently

### User-Friendly Tools
- **Windows batch script**: Double-click to run
- **Command-line interface**: Full control with options
- **Mapping helper**: Easy tools to add new mappings
- **Comprehensive documentation**: Guides for every scenario

## 📋 Requirements

- Python 3.7+
- Windows (for batch script) or any OS (for Python scripts)
- Required Python packages (automatically handled):
  - Standard library modules only (json, os, pathlib, etc.)

## 🛠️ Installation

1. **Clone or download** this repository
2. **No additional installation required** - uses Python standard library only
3. **Ensure Python is in your PATH** for the batch script to work

## 📖 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Essential commands and quick fixes ⚡
- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with examples 📚
- **[MAPPING_GUIDE.md](MAPPING_GUIDE.md)** - Detailed mapping configuration guide 🔧
- **[SETUP.md](SETUP.md)** - Installation and setup instructions 🛠️
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes 📝
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview and achievements 🎯

## 🎮 Usage Examples

### Basic Usage
```bash
# Generate config from quantity data
.\generate_config.bat quantity_mode_analysis.json

# Use custom template and output
python generate_config_ascii.py data.json -t custom_template.json -o output.json

# Verbose output
python generate_config_ascii.py data.json -v
```

### Mapping Management
```bash
# List current mappings
python add_mapping.py --list-mappings

# Add sheet name mapping
python add_mapping.py --add-sheet "INV_2024:Invoice"

# Add header text mapping
python add_mapping.py --add-header "TOTAL AMOUNT:col_amount"

# Generate mapping report
python add_mapping.py --generate-report report.txt
```

## 🔍 Common Scenarios

### New Excel File Format
When you encounter a new Excel file with different sheet names or headers:

1. **Run the generator** and note any warnings
2. **Check the mapping report** (automatically generated)
3. **Add missing mappings** using the helper tool
4. **Re-run the generator** - warnings should be resolved

### Different Languages/Formats
```bash
# Handle different language headers
python add_mapping.py --add-header "Numéro P.O:col_po"
python add_mapping.py --add-header "Quantité:col_qty_sf"

# Handle different sheet name formats
python add_mapping.py --add-sheet "FACTURE:Invoice"
python add_mapping.py --add-sheet "LISTE_EMBALLAGE:Packing list"
```

## 🏗️ Architecture

The system follows a modular architecture:

1. **Template Loader**: Loads and validates the base template
2. **Quantity Data Loader**: Loads and parses quantity analysis data
3. **Mapping Manager**: Handles all sheet and header mappings
4. **Updaters**: Specialized components for different update types
   - Header Text Updater
   - Font Updater
   - Position Updater
5. **Config Writer**: Writes and validates the final configuration

## 🤝 Contributing

This is a specialized tool for Excel configuration generation. For modifications:

1. **Mapping changes**: Use `mapping_config.json` and helper tools
2. **Template changes**: Modify `sample_config.json`
3. **Code changes**: Follow the modular architecture
4. **Testing**: Test with various Excel file formats

## 📝 License

This project is for internal use. See your organization's guidelines for usage and distribution.

## 🆘 Support

### Common Issues

**Issue**: "Sheet not found" warnings
**Solution**: Add sheet name mappings using `add_mapping.py`

**Issue**: Headers not updating
**Solution**: Add header text mappings for your specific headers

**Issue**: Font/position not updating
**Solution**: Check that your quantity data contains the required information

### Getting Help

1. **Check the logs** - detailed error messages are provided
2. **Review mapping reports** - automatically generated for each run
3. **Consult the guides** - USER_GUIDE.md and MAPPING_GUIDE.md
4. **Test incrementally** - add mappings one at a time

## 🎉 Success Stories

This tool successfully handles:
- ✅ Multiple Excel file formats and layouts
- ✅ Different languages and header variations
- ✅ Various sheet naming conventions
- ✅ Complex template configurations with business logic
- ✅ Batch processing of multiple files
- ✅ Automatic error detection and reporting

---

**Ready to get started?** Run `.\generate_config.bat your_file.json` and see the magic happen! 🚀