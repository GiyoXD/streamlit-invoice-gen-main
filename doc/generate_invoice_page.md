# Generate Invoice Page Documentation

## Overview

The Generate Invoice Page (`pages/0_Generate_Invoice.py`) is the core user interface for the invoice generation system. It implements a multi-step workflow that guides users through the process of generating invoices and packing lists using different strategies.

### Purpose
- Provide a unified interface for invoice generation
- Support multiple invoice generation strategies
- Handle file uploads, validation, and processing
- Manage user authentication and session state
- Generate downloadable invoice and packing list documents

### Key Features
- **Multi-step workflow**: 7 distinct steps from strategy selection to final generation
- **Strategy pattern implementation**: Supports High-Quality Leather and 2nd Layer Leather strategies
- **File validation**: Excel file validation with detailed error reporting
- **Database integration**: SQLite database for invoice record management
- **Authentication**: Integrated user authentication and authorization
- **Error handling**: Comprehensive error handling and user feedback

## Architecture

### Design Patterns
- **Strategy Pattern**: Used for different invoice generation approaches
- **State Machine**: Workflow steps managed through session state
- **Factory Pattern**: Strategy instantiation through registry

### Dependencies
```python
# Core Streamlit
import streamlit as st

# File and path management
import os, sys
from pathlib import Path

# Data processing
import json, datetime, sqlite3, tempfile

# Utilities
from zoneinfo import ZoneInfo
import time, re

# Custom modules
from auth_wrapper import setup_page_auth
from invoice_strategies import (
    STRATEGIES,
    apply_print_settings_to_files,
    create_download_zip,
)
```

### Directory Structure
```
pages/0_Generate_Invoice.py
├── Authentication setup
├── Path configuration
├── Database initialization
├── Session state management
├── Workflow steps (7 steps)
└── Utility functions
```

## Workflow Steps

The page implements a 7-step workflow managed through `st.session_state.workflow_step`:

### 1. Strategy Selection (`select_strategy`)
**Purpose**: Allow users to choose invoice generation strategy
**UI Elements**:
- Strategy selection buttons with descriptions
- Navigation controls (Reset Workflow)
**Logic**:
- Display available strategies from `STRATEGIES` registry
- Update `selected_strategy` in session state
- Transition to upload step

### 2. File Upload (`upload`)
**Purpose**: Upload Excel file for processing
**UI Elements**:
- File uploader (Excel files only)
- Strategy information display
- Process button
- Navigation controls
**Logic**:
- Save uploaded file to temporary directory
- Store file reference in session state
- Transition to validation step

### 3. Excel Validation (`validate_excel`)
**Purpose**: Validate uploaded Excel file structure and content
**UI Elements**:
- File name display
- Validation status (pass/fail)
- Detailed validation warnings/errors
- Action buttons (Back/Continue/Process)
**Logic**:
- Call `strategy.validate_excel_data()`
- Display validation results
- Handle validation failures gracefully

### 4. Input Collection (`collect_inputs`) - *2nd Layer Leather Only*
**Purpose**: Collect additional invoice details for 2nd Layer Leather strategy
**UI Elements**:
- Dynamic form based on strategy requirements
- Input validation
- Navigation controls
**Logic**:
- Generate form fields from strategy configuration
- Validate required inputs
- Store collected data in session state

### 5. File Processing (`process_file`)
**Purpose**: Process validated Excel data into JSON format
**UI Elements**:
- Processing status
- Progress indicators
- Error handling
**Logic**:
- Call `strategy.process_excel_to_json()`
- Generate intermediate JSON data
- Handle processing errors

### 6. Overrides (`overrides`)
**Purpose**: Allow users to override default settings
**UI Elements**:
- Override configuration form
- **Field Prefiller Component**: Invoice No field with "Use Filename" button (pre-fills with uploaded filename without extension)
- Preview of current settings
- Navigation controls
**Logic**:
- Display strategy-specific override options
- **New Feature**: Invoice No field uses field_prefiller component with uploaded filename suggestion
- Update configuration in session state

### 7. Generation (`generate`)
**Purpose**: Generate final invoice and packing list documents
**UI Elements**:
- Generation options selection
- Progress tracking
- Download buttons
- Success/error messages
**Logic**:
- Call `strategy.generate_invoice()`
- Apply print settings
- Create downloadable ZIP archive

## Code Structure

### Session State Variables
```python
st.session_state.workflow_step          # Current workflow step
st.session_state.selected_strategy      # Chosen strategy object
st.session_state.uploaded_file          # Uploaded file reference
st.session_state.temp_file_path         # Temporary file path
st.session_state.excel_validation_passed # Validation status
st.session_state.excel_validation_warnings # Validation messages
st.session_state.json_path             # Processed JSON file path
```

### Key Functions

#### `initialize_database(db_file: Path) -> bool`
**Purpose**: Initialize SQLite database with required tables
**Parameters**:
- `db_file`: Path to database file
**Returns**: Success status
**Tables Created**:
- `invoices`: Main invoice data
- `invoice_containers`: Container information
- Indexes for performance

#### `reset_workflow()`
**Purpose**: Reset all session state to initial values
**Side Effects**: Clears all workflow-related session variables

### Error Handling
- Database initialization failures → App termination
- File upload errors → User notification with cleanup
- Validation failures → Detailed error display with recovery options
- Processing errors → Graceful fallback with user feedback

## Testing

### Test Coverage
The page is tested through `tests/pages/test_0_Generate_Invoice.py` with:
- **UI Workflow Tests**: Session state transitions
- **Strategy Integration**: Strategy selection and validation
- **Mocking**: Streamlit components properly mocked

### Running Tests
```bash
# Run all tests
python run_tests.py

# Run page-specific tests
python -m unittest tests.pages.test_0_Generate_Invoice -v
```

### Test Scenarios
1. **Initial State**: Verify default session state values
2. **Strategy Selection**: Test strategy selection updates session state
3. **File Upload Flow**: Test file upload and temporary storage
4. **Validation Flow**: Test Excel validation with mock data

## API Reference

### Strategy Interface
The page interacts with strategies through this interface:

#### `strategy.validate_excel_data(file_path: Path) -> tuple[bool, list[str]]`
Validate Excel file structure and content.

#### `strategy.process_excel_to_json(file_path: Path, **kwargs) -> dict`
Process Excel data into JSON format.

#### `strategy.generate_invoice(json_data: dict, **kwargs) -> dict`
Generate final invoice documents.

#### `strategy.get_required_fields() -> list[str]`
Get list of required Excel columns.

#### `strategy.get_generation_options() -> list[dict]`
Get available generation options.

**Example Outputs**:

*SecondLayerLeatherStrategy*:
```python
[
    {
        'name': 'Standard Invoice',
        'key': 'standard',
        'flags': []
    }
]
```

*HighQualityLeatherStrategy*:
```python
[
    {
        'name': 'Normal Invoice',
        'key': 'normal',
        'flags': []
    },
    {
        'name': 'DAF Version',
        'key': 'daf',
        'flags': ['--DAF']
    },
    {
        'name': 'Combine Version',
        'key': 'combine',
        'flags': ['--custom']
    }
]
```

### Session State API
```python
# Workflow control
st.session_state.workflow_step = 'step_name'
st.session_state.selected_strategy = strategy_object

# File management
st.session_state.uploaded_file = file_object
st.session_state.temp_file_path = Path('/temp/file.xlsx')

# Validation state
st.session_state.excel_validation_passed = True/False
st.session_state.excel_validation_warnings = ['warning1', 'warning2']

# Processing state
st.session_state.json_path = Path('/output/data.json')
```

## Usage Examples

### Basic Invoice Generation Flow
```python
# 1. User selects strategy
st.session_state.selected_strategy = STRATEGIES['high_quality']
st.session_state.workflow_step = 'upload'

# 2. User uploads file
uploaded_file = st.file_uploader("Choose Excel file")
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    st.session_state.workflow_step = 'validate_excel'

# 3. System validates file
strategy = st.session_state.selected_strategy
is_valid, warnings = strategy.validate_excel_data(temp_path)

# 4. Generate invoice
if is_valid:
    result = strategy.generate_invoice(json_data)
    create_download_zip(result)
```

### Error Handling Example
```python
try:
    # Process file
    json_data = strategy.process_excel_to_json(temp_path)
    st.session_state.json_path = json_data['output_path']
except Exception as e:
    st.error(f"Processing failed: {e}")
    # Cleanup and reset to previous step
    st.session_state.workflow_step = 'validate_excel'
```

## Configuration

### Directory Paths
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREATE_JSON_DIR = PROJECT_ROOT / "create_json"
INVOICE_GEN_DIR = PROJECT_ROOT / "invoice_gen"
DATA_DIR = PROJECT_ROOT / "data"
JSON_OUTPUT_DIR = DATA_DIR / "invoices_to_process"
TEMP_UPLOAD_DIR = DATA_DIR / "temp_uploads"
TEMPLATE_DIR = INVOICE_GEN_DIR / "TEMPLATE"
CONFIG_DIR = INVOICE_GEN_DIR / "config"
```

### Database Configuration
- **File**: `data/Invoice Record/master_invoice_data.db`
- **Table**: `invoices`
- **Indexes**: Performance indexes on `inv_ref` and `inv_no`

## Security Considerations

### Authentication
- Integrated with `auth_wrapper.py`
- User session validation
- Page-level access control

### File Handling
- Temporary file cleanup on errors
- Secure file path validation
- No direct file system access for users

### Data Validation
- Excel file structure validation
- Input sanitization
- SQL injection prevention through parameterized queries

## Performance Considerations

### File Processing
- Temporary files cleaned up immediately after use
- Large file handling with streaming
- Memory-efficient JSON processing

### Database Operations
- Connection pooling through SQLite
- Indexed queries for performance
- Transaction-based operations

### UI Responsiveness
- Progressive disclosure (step-by-step workflow)
- Loading states for long operations
- Error recovery without full page reload

## Recent Features

### Field Prefiller Component (October 2025)
- **Reusable UI Component**: Created `ui_utils/field_prefiller.py` for pre-filling text input fields
- **Invoice Number Auto-Fill**: Invoice No field now includes "Use Filename" button that pre-fills with the uploaded file's name (without extension)
- **Component-Based Architecture**: Modular design for easy reuse across different forms
- **Test Coverage**: Comprehensive unit tests ensure reliability

## Future Improvements

### Planned Enhancements
1. **Batch Processing**: Support multiple files simultaneously
2. **Template Management**: User-customizable invoice templates
3. **Progress Tracking**: Real-time generation progress
4. **Audit Logging**: Comprehensive user action logging
5. **Export Formats**: Additional output formats (PDF, CSV)
6. **Integration APIs**: REST API for external integrations

### Technical Debt
1. **Code Organization**: Extract workflow steps into separate functions
2. **Error Handling**: Centralized error handling system
3. **Testing**: Increase test coverage for edge cases
4. **Documentation**: API documentation generation

### Scalability Considerations
1. **Database**: Consider migration to PostgreSQL for high volume
2. **File Storage**: Implement cloud storage for large files
3. **Caching**: Add Redis for session state management
4. **Async Processing**: Background job processing for large files

## Troubleshooting

### Common Issues

#### Database Connection Failed
**Symptoms**: App shows database error on startup
**Solution**:
```bash
# Check database file permissions
ls -la data/Invoice\ Record/master_invoice_data.db

# Reinitialize database
rm data/Invoice\ Record/master_invoice_data.db
# Restart app to recreate database
```

#### File Upload Errors
**Symptoms**: Files fail to upload or process
**Solution**:
- Check temporary directory permissions
- Verify file size limits
- Ensure Excel file format compatibility

#### Strategy Loading Errors
**Symptoms**: Strategies not available in dropdown
**Solution**:
- Check `invoice_strategies.py` imports
- Verify strategy registration in `STRATEGIES` dict
- Check for syntax errors in strategy classes

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export STREAMLIT_DEBUG=true
streamlit run app.py
```

## Contributing

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for function parameters
- Add docstrings to all public functions
- Maintain test coverage above 80%

### Adding New Strategies
1. Create new strategy class inheriting from `InvoiceGenerationStrategy`
2. Implement required abstract methods
3. Register strategy in `STRATEGIES` dictionary
4. Add strategy-specific tests
5. Update documentation

### Workflow Modifications
1. Add new workflow step constant
2. Implement step UI and logic
3. Update session state management
4. Add navigation controls
5. Update tests and documentation

---

**Last Updated**: October 1, 2025
**Version**: 1.0
**Maintainer**: Development Team
**Related Files**:
- `invoice_strategies.py` - Strategy implementations
- `auth_wrapper.py` - Authentication system
- `tests/pages/test_0_Generate_Invoice.py` - Test suite