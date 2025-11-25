# Setup Guide

## System Requirements

- **Python 3.7+** (Python 3.8+ recommended)
- **Windows OS** (for batch script convenience)
- **No additional packages required** (uses Python standard library only)

## Installation

### Option 1: Download/Clone
1. Download or clone this repository to your local machine
2. No additional installation steps required

### Option 2: Copy Files
If you only need the essential files:
```
config_gen/
├── generate_config.bat           # Required
├── generate_config_ascii.py      # Required  
├── mapping_config.json          # Required
├── add_mapping.py              # Required
├── sample_config.json          # Required
└── config_generator/           # Required (entire folder)
```

## Verification

### Test Python Installation
```bash
python --version
# Should show Python 3.7 or higher
```

### Test the System
```bash
# Navigate to the config_gen directory
cd path/to/config_gen

# Test with the included sample (if available)
python generate_config_ascii.py --help

# Should show the help message without errors
```

### Test Mapping System
```bash
python add_mapping.py --list-mappings
# Should show current mappings without errors
```

## First Run

1. **Place your quantity data file** in the config_gen directory
2. **Run the generator**:
   ```bash
   .\generate_config.bat your_data.json
   ```
3. **Check the output** - you should see either success or helpful warnings

## Troubleshooting Setup

### Python Not Found
**Error**: `'python' is not recognized as an internal or external command`

**Solutions**:
- Install Python from [python.org](https://python.org)
- During installation, check "Add Python to PATH"
- Or use full path: `C:\Python39\python.exe generate_config_ascii.py`

### Permission Issues
**Error**: Permission denied or access errors

**Solutions**:
- Run command prompt as Administrator
- Check file permissions in the directory
- Ensure antivirus isn't blocking Python execution

### Import Errors
**Error**: Module import errors

**Cause**: Usually indicates missing files or incorrect directory structure

**Solution**: Ensure all files from the `config_generator/` folder are present

## Directory Structure Verification

Your directory should look like this:
```
config_gen/
├── generate_config.bat
├── generate_config_ascii.py
├── mapping_config.json
├── add_mapping.py
├── sample_config.json
├── README.md
├── USER_GUIDE.md
├── MAPPING_GUIDE.md
├── QUICK_REFERENCE.md
└── config_generator/
    ├── __init__.py
    ├── config_generator.py
    ├── mapping_manager.py
    ├── template_loader.py
    ├── quantity_data_loader.py
    ├── header_text_updater.py
    ├── font_updater.py
    ├── position_updater.py
    ├── config_writer.py
    └── models.py
```

## Ready to Use!

Once setup is complete, you're ready to:
1. **Generate configs**: `.\generate_config.bat your_data.json`
2. **Manage mappings**: `python add_mapping.py --list-mappings`
3. **Read the guides**: Start with [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## Getting Help

If you encounter setup issues:
1. **Check Python version**: Must be 3.7+
2. **Verify file structure**: All files must be present
3. **Test step by step**: Use the verification commands above
4. **Check permissions**: Ensure you can read/write in the directory

---

**Setup complete!** 🎉 You're ready to generate configurations!