# Config Generator Integration Instructions

## Overview
This document describes how to integrate the config_and_template_gen_module into the Streamlit application to create a user-friendly interface for generating invoice configurations and templates for new companies.

## Purpose
When users encounter a company that doesn't have an existing configuration file in the invoice generation process, they need a way to create one. The Config Generator page provides a simple, step-by-step interface for non-technical users to:

1. Upload their company's Excel invoice template
2. Automatically analyze the template structure
3. Generate the necessary configuration files
4. Test and validate the configuration

## User Journey
1. **User tries to generate invoice** → Gets error "Company configuration not found"
2. **System directs user** → "Please visit the Company Setup Assistant to create configuration"
3. **User goes to Config Generator page** → Uploads Excel template
4. **System analyzes template** → Extracts structure, fonts, positions
5. **User reviews mapping** → Confirms or adjusts field mappings
6. **System generates config** → Creates working configuration files
7. **User returns to invoice generation** → Can now generate invoices

## Technical Implementation

### Page Name
- **Technical Name**: `2_Config_Generator.py`
- **User-Friendly Name**: "Company Setup Assistant" or "Invoice Template Setup"
- **Menu Label**: "🏢 Company Setup"

### Key Features to Implement

#### 1. File Upload Section
- Accept `.xlsx` files only
- Validate file format and structure
- Show preview of uploaded file

#### 2. Company Information
- Company name input
- Template type selection (Invoice, Packing List, Combined)
- Output directory selection

#### 3. Template Analysis
- Automatic structure analysis using `config_data_extractor/analyze_excel.py`
- Display found headers and positions
- Show analysis results in user-friendly format

#### 4. Field Mapping Interface
- Interactive mapping using `generate_config/interactive_mapping.py`
- Show suggested mappings with confidence scores
- Allow manual override of mappings
- Visual representation of Excel structure

#### 5. Configuration Generation
- Generate config using `generate_config/generate_config_ascii.py`
- Create both JSON config and processed XLSX template
- Validate generated configuration

#### 6. Testing & Preview
- Test configuration with sample data
- Show preview of generated invoice
- Allow fine-tuning if needed

#### 7. Save & Deploy
- Save configuration to `invoice_gen/config/` directory
- Save template to `invoice_gen/TEMPLATE/` directory
- Provide success confirmation

### Error Handling
- Clear error messages for non-technical users
- Guidance on fixing common issues
- Option to contact support

### Integration Points

#### From Generate Invoice Page
When config not found, show user-friendly message:
```
⚠️ Company Configuration Missing

This company's invoice template hasn't been set up yet. 

To generate invoices for this company, you'll need to:
1. Go to the 🏢 Company Setup page
2. Upload the company's Excel invoice template
3. Complete the setup process (takes 5-10 minutes)

[Go to Company Setup] [Contact Support]
```

#### Config File Naming Convention
- Config files: `{company_name}_{template_type}_config.json`
- Template files: `{company_name}_{template_type}_template.xlsx`
- Store in appropriate directories with proper naming

### Module Integration Points

#### Use Existing CLI Tools (No Modification)
1. **Analysis**: `config_data_extractor/analyze_excel.py`
2. **Interactive Mapping**: `generate_config/interactive_mapping.py`  
3. **Config Generation**: `generate_config/generate_config_ascii.py`
4. **Main Orchestrator**: `main.py`

#### Streamlit Adaptations Needed
- Convert CLI interactions to web forms
- Replace command-line prompts with Streamlit widgets
- Adapt file I/O for Streamlit's upload/download patterns
- Convert console output to progress indicators

### Success Criteria
1. **Non-technical users** can complete setup without IT support
2. **Process takes under 10 minutes** for a typical template
3. **Generated configs work immediately** with existing invoice generation
4. **Clear error messages** guide users through problems
5. **No modification needed** to the config_and_template_gen_module code

### Notes for Implementation
- The module is designed to work via CLI - wrap it with subprocess calls
- Use temporary directories for file processing
- Preserve all existing functionality of the config generator
- Focus on UI/UX improvements for non-technical users
- Provide clear progress indicators and helpful explanations

## Testing Checklist
- [ ] Upload various Excel formats
- [ ] Test with complex templates
- [ ] Verify generated configs work with invoice generation
- [ ] Test error scenarios and recovery
- [ ] Validate user experience flow
- [ ] Check file permissions and directory creation
