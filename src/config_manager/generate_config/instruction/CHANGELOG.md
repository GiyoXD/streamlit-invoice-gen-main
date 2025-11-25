# Changelog

All notable changes to the Config Generator project.

## [2.0.0] - 2025-01-22

### 🎉 Major Release - Flexible Mapping System

### Added
- **Flexible Mapping System**: Complete overhaul of how sheet names and headers are mapped
  - `mapping_config.json`: Centralized configuration file for all mappings
  - `MappingManager`: Smart mapping system with fallback strategies
  - `add_mapping.py`: Command-line tool for easy mapping management
  - Automatic mapping reports with suggestions

- **Enhanced User Experience**:
  - Comprehensive documentation suite (README, USER_GUIDE, MAPPING_GUIDE, QUICK_REFERENCE)
  - Windows batch script for easy execution
  - Detailed error messages and warnings
  - Automatic generation of mapping reports

- **Intelligent Fallback Strategies**:
  - Case-insensitive matching
  - Partial text matching with configurable threshold
  - Pattern-based recognition for common header variations
  - Similarity scoring for suggestions

- **Robust Error Handling**:
  - Comprehensive validation of input files
  - Clear error messages with actionable solutions
  - Graceful handling of missing mappings
  - Detailed logging and reporting

### Fixed
- **Critical Bug**: Fixed batch script calling non-existent `generate_config.py`
  - Now correctly calls `generate_config_ascii.py`
- **Sheet Name Mapping**: Resolved issue where quantity data sheet names ("INV", "PAK") didn't match template names ("Invoice", "Packing list")
- **Configuration Updates**: Fixed issue where configurations weren't being updated with actual data
  - Start row values now update correctly (e.g., 20 → 21)
  - Font information now updates from quantity data
  - Header texts now update with actual column headers

### Changed
- **Architecture**: Modular design with specialized updater components
  - `HeaderTextUpdater`: Handles header text updates
  - `FontUpdater`: Handles font information updates  
  - `RowDataUpdater`: Handles start row and row height updates
  - `MappingManager`: Centralized mapping management

- **Configuration Management**: 
  - Moved from hardcoded mappings to configurable JSON file
  - Added command-line tools for mapping management
  - Implemented automatic report generation

### Technical Details

#### Core Improvements
- **Template-Based Updates**: System now properly updates specific fields while preserving business logic
- **Mapping Flexibility**: Handle any sheet name or header text variation through configuration
- **Comprehensive Validation**: Input validation, structure checking, and error reporting
- **Modular Architecture**: Clean separation of concerns with specialized components

#### New Components
- `config_generator/mapping_manager.py`: Central mapping management
- `mapping_config.json`: User-configurable mapping definitions
- `add_mapping.py`: Command-line mapping management tool
- Comprehensive documentation suite

#### Enhanced Features
- **Batch Processing**: Improved support for processing multiple files
- **Custom Templates**: Support for custom template configurations
- **Verbose Logging**: Detailed processing information for debugging
- **Report Generation**: Automatic mapping reports for manual review

### Migration Guide

#### From Version 1.x
1. **No breaking changes** for basic usage
2. **New mapping system** automatically handles previous hardcoded mappings
3. **Enhanced functionality** available through new command-line tools

#### Recommended Actions
1. **Review generated mapping reports** for optimization opportunities
2. **Add custom mappings** for your specific Excel file formats
3. **Update workflows** to use new batch script and tools

### Usage Examples

#### Basic Usage (Unchanged)
```bash
.\generate_config.bat your_data.json
```

#### New Mapping Management
```bash
# List current mappings
python add_mapping.py --list-mappings

# Add new mappings
python add_mapping.py --add-sheet "NEW_SHEET:Invoice"
python add_mapping.py --add-header "NEW_HEADER:col_amount"
```

### Performance Improvements
- **Faster Processing**: Optimized mapping lookup algorithms
- **Memory Efficiency**: Improved handling of large configuration files
- **Error Recovery**: Better handling of partial failures

### Documentation
- **Complete User Guide**: Step-by-step instructions with examples
- **Mapping Guide**: Detailed configuration management
- **Quick Reference**: Essential commands and common fixes
- **Setup Guide**: Installation and verification instructions

---

## [1.0.0] - Previous Version

### Initial Release
- Basic configuration generation from quantity analysis data
- Template-based updates for start row, fonts, and headers
- Hardcoded mapping system
- Command-line interface

### Known Issues (Fixed in 2.0.0)
- Batch script called wrong Python file
- Limited flexibility for different Excel formats
- No user-friendly mapping management
- Minimal error reporting and guidance

---

**Legend**:
- 🎉 Major features
- ✨ Enhancements  
- 🐛 Bug fixes
- 📚 Documentation
- ⚡ Performance
- 🔧 Technical changes