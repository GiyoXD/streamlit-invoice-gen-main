import streamlit as st
from app import setup_page_auth
import os
import sys
from pathlib import Path
import pandas as pd
import re
import time
import subprocess
import json
import shutil
from src.auth.login import log_business_activity

# --- Authentication ---
user_info = setup_page_auth(
    page_title="Template Generator",
    page_name="Template Generator",
    layout="wide"
)
if not user_info:
    st.warning("Please log in to access this page.")
    st.stop()

st.title("✨ New Invoice Template Generator")

# --- Path Setup ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CONFIG_GEN_DIR = PROJECT_ROOT / "src" / "config_manager"
    TEMP_DIR = PROJECT_ROOT / "data" / "temp_uploads"
    CONFIG_OUTPUT_DIR = PROJECT_ROOT / "src" / "invoice_generator" / "src" / "config_bundled"
    TEMPLATE_OUTPUT_DIR = PROJECT_ROOT / "src" / "invoice_generator" / "src" / "template"
    MAPPING_CONFIG_PATH = CONFIG_GEN_DIR / "mapping_config.json" # Added for local functions
    
    # Create necessary directories
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

except Exception as e:
    st.error(f"Failed to set up paths. Error: {e}")
    st.stop()

# --- Backend Logic (Local Implementations) ---
# Critical Constraint: These functions call the generator scripts as external
# processes and do not modify any code within config_template_cli.

def run_command(command, verbose=False, cwd=None):
    """Executes a command in a subprocess and handles Streamlit output."""
    try:
        if verbose:
            st.write(f"Executing: `{' '.join(command)}`")
        
        # Using st.spinner to show command execution
        with st.spinner(f"Running command: `{command[2].split('/')[-1]}`..."):
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                st.error(f"Command failed: {' '.join(command)}")
                st.text_area("Stderr", stderr, height=150)
                return False
            
            if verbose:
                st.text_area("Stdout", stdout, height=100)
            
        return True
    except Exception as e:
        st.error(f"An exception occurred while running the command: {e}")
        return False

def analyze_excel_file(excel_file_path: str, output_path: str, verbose: bool = False):
    """Analyzes an Excel file by calling the external analysis script."""
    analyze_script_path = CONFIG_GEN_DIR / "config_data_extractor" / "analyze_excel.py"
    if not analyze_script_path.exists():
        st.error(f"Analysis script not found at: {analyze_script_path}")
        return False
        
    analyze_command = [
        sys.executable, '-X', 'utf8', str(analyze_script_path),
        excel_file_path, '--json', '--quantity-mode', '-o', output_path
    ]
    return run_command(analyze_command, verbose, cwd=str(CONFIG_GEN_DIR))

def get_missing_headers(analysis_file_path: str):
    """Extracts headers from the analysis file and identifies missing mappings."""
    try:
        with open(analysis_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
            
        current_mappings = {}
        if MAPPING_CONFIG_PATH.exists():
            with open(MAPPING_CONFIG_PATH, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                current_mappings = mapping_data.get('header_text_mappings', {}).get('mappings', {})
        
        all_found_headers = {
            header.get('keyword', 'Unknown')
            for sheet in analysis_data.get('sheets', [])
            for header in sheet.get('header_positions', [])
        }

        missing_headers = []
        for header in all_found_headers:
            # Check for exact match first
            if header in current_mappings:
                continue
            
            # Check for case-insensitive match
            header_lower = header.lower()
            mapping_found = False
            for mapped_header in current_mappings:
                if mapped_header.lower() == header_lower:
                    mapping_found = True
                    break
            
            if not mapping_found:
                missing_headers.append({"text": header, "suggestion": get_header_suggestions(header)})
        
        return missing_headers
    except Exception as e:
        st.error(f"Error getting missing headers: {e}")
        return []

def get_header_suggestions(header_text: str) -> str:
    """Suggests a column ID based on header text content."""
    header_lower = header_text.lower()
    suggestions = {
        "col_po": ['p.o', 'po'], "col_item": ['item', 'no.'], "col_desc": ['description', 'desc'],
        "col_qty_sf": ['quantity', 'qty'], "col_unit_price": ['unit', 'price'], "col_amount": ['amount', 'total', 'value'],
        "col_net": ['n.w', 'net'], "col_gross": ['g.w', 'gross'], "col_cbm": ['cbm'],
        "col_pallet": ['pallet'], "col_remarks": ['remarks', 'notes'], "col_static": ['mark', 'note', 'nº']
    }
    for col_id, keywords in suggestions.items():
        if any(word in header_lower for word in keywords):
            return col_id
    return "col_unknown"

def update_mapping_config(new_mappings: dict):
    """Adds new header mappings to the global mapping_config.json."""
    try:
        mapping_data = {"header_text_mappings": {"mappings": {}}}
        if MAPPING_CONFIG_PATH.exists():
            with open(MAPPING_CONFIG_PATH, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
        
        if "header_text_mappings" not in mapping_data: mapping_data["header_text_mappings"] = {"mappings": {}}
        if "mappings" not in mapping_data["header_text_mappings"]: mapping_data["header_text_mappings"]["mappings"] = {}

        mapping_data["header_text_mappings"]["mappings"].update(new_mappings)

        with open(MAPPING_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error updating mapping config: {e}")
        return False

# --- System Headers ---
# This list represents the target fields the system knows how to process.
SYSTEM_HEADERS = [
    "col_po", "col_item", "col_desc", "col_qty_pcs", "col_qty_sf", 
    "col_unit_price", "col_amount", "col_net", "col_gross", "col_cbm", 
    "col_pallet", "col_remarks", "col_static", "col_dc"
]

# --- Session State Check ---
# This page is now independent of the invoice generation page's session state.
# A user can directly upload an invoice here to create a template.

st.info(
    "**Instructions:**\n"
    "1. Upload a sample **invoice** (not a shipping list) from a new company.\n"
    "2. The system will analyze its structure.\n"
    "3. You will define a unique prefix and map any unrecognized columns.\n"
    "4. A new template and configuration will be saved, enabling future processing."
)
st.markdown("---")

# --- Main Page Logic ---
invoice_template_file = st.file_uploader(
    "Upload a sample INVOICE XLSX file", 
    type="xlsx", 
    key="template_uploader"
)

if invoice_template_file:
    file_name = invoice_template_file.name
    file_bytes = invoice_template_file.getvalue()

    st.info(f"**File to Analyze:** `{file_name}`")
    st.markdown("---")

    # Use an expander to keep the UI clean
    with st.expander("Show Uploaded Excel Data Preview"):
        try:
            df = pd.read_excel(file_bytes, header=None)
            st.dataframe(df.head(20))
        except Exception as e:
            st.error(f"Could not read or display the Excel file. Error: {e}")
            st.stop()

    st.markdown("---")
    st.subheader("Step 1: Analyze Headers")
    st.write("The system will analyze the headers from your uploaded invoice to find any it doesn't recognize.")

    if st.button("Analyze File Headers", use_container_width=True):
        # Save the uploaded file temporarily to be accessed by the analysis script
        temp_excel_path = TEMP_DIR / file_name
        file_prefix_for_temp = re.match(r'([A-Za-z]+)', file_name).group(1) if re.match(r'([A-Za-z]+)', file_name) else file_name.split('.')[0]
        temp_analysis_output_path = TEMP_DIR / f"{file_prefix_for_temp}_analysis.json"
        
        with open(temp_excel_path, 'wb') as f:
            f.write(file_bytes)

        try:
            with st.spinner("Analyzing... This may take a moment."):
                # 1. Run analysis script
                success = analyze_excel_file(str(temp_excel_path), str(temp_analysis_output_path), verbose=True)
                if not success:
                    st.error("Failed to analyze the Excel file. Please check the file format.")
                    st.stop()

                # 2. Get missing headers
                missing_headers = get_missing_headers(str(temp_analysis_output_path))
                
                # Store results in session state
                st.session_state['analysis_path'] = str(temp_analysis_output_path)
                st.session_state['missing_headers'] = missing_headers
                st.session_state['analysis_complete'] = True
                st.session_state['original_file_bytes_for_template'] = file_bytes # Store for final step
            
            # Log successful template analysis
            try:
                log_business_activity(
                    user_id=user_info['user_id'],
                    username=user_info['username'],
                    activity_type='TEMPLATE_ANALYSIS',
                    description=f"Analyzed Excel file: {file_name}",
                    action_description=f"Analyzed invoice template from '{file_name}', found {len(missing_headers)} unmapped headers",
                    success=True
                )
            except Exception as e:
                st.warning(f"Activity logging failed: {e}")
            
            st.success("Analysis complete! Please proceed to the next step.")
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")
            st.exception(e)
        finally:
            # Clean up the temporary excel file
            if temp_excel_path.exists():
                temp_excel_path.unlink()


    if st.session_state.get('analysis_complete'):
        missing_headers = st.session_state.get('missing_headers', [])
        
        st.subheader("Step 2: Define Template Prefix & Map Headers")
        
        file_prefix_suggestion = re.match(r'([A-Za-z]+)', file_name).group(1) if re.match(r'([A-Za-z]+)', file_name) else file_name.split('.')[0]
        
        st.session_state['file_prefix'] = st.text_input(
            "**Enter a unique prefix for this template**", 
            value=file_prefix_suggestion,
            help="This prefix (e.g., 'MOTO', 'JLFHM') will be used to name the config and template files."
        )

        st.write("For each unrecognized header from your file, select the correct system field it corresponds to. The system has made its best guess.")
        
        if not missing_headers:
            st.success("✅ All headers were automatically recognized!")
            st.session_state['user_mappings'] = {} # Ensure user_mappings is initialized
        else:
            st.warning(f"Found {len(missing_headers)} headers that need mapping.")
            
            mapping_selections = {}
            for header_info in missing_headers:
                header_text = header_info['text']
                suggestion = header_info['suggestion']
                
                # Find the index for the selectbox, default to the last item (col_static) if guess is not in the list
                try:
                    guess_index = SYSTEM_HEADERS.index(suggestion)
                except ValueError:
                    guess_index = len(SYSTEM_HEADERS) - 1

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**`{header_text}`**")
                with col2:
                    selection = st.selectbox(
                        f"Map '{header_text}' to:",
                        options=SYSTEM_HEADERS,
                        index=guess_index,
                        key=f"map_{header_text}"
                    )
                    mapping_selections[header_text] = selection
            
            st.session_state['user_mappings'] = mapping_selections

        st.markdown("---")
        st.subheader("Step 3: Generate and Save New Template")
        
        # Add checkbox for Bundle Format
        use_bundle_format = st.checkbox("Use New Bundle Format (Recommended)", value=True, help="Generates configuration in the new, more robust bundle format.")

        if st.button("Generate New Template & Config", use_container_width=True, type="primary"):
            file_prefix = st.session_state.get('file_prefix', '').strip()
            if not file_prefix:
                st.error("Template prefix cannot be empty. Please enter a unique prefix.")
                st.stop()

            with st.spinner("Generating configuration and template files..."):
                # 1. Update the global mapping config with the user's choices first.
                # The main.py script will read this updated file.
                user_mappings = st.session_state.get('user_mappings', {})
                if user_mappings:
                    if not update_mapping_config(user_mappings):
                        st.error("Failed to update the master mapping configuration. Aborting.")
                        st.stop()
                    
                    # Log mapping update activity
                    try:
                        log_business_activity(
                            user_id=user_info['user_id'],
                            username=user_info['username'],
                            activity_type='MAPPING_UPDATED',
                            description=f"Updated header mappings for template {file_prefix} from file: {file_name}",
                            action_description=f"Added {len(user_mappings)} new header mappings to global configuration from '{file_name}'",
                            success=True
                        )
                    except Exception as e:
                        st.warning(f"Activity logging failed: {e}")
                
                # 2. Define paths for the single, correct command.
                temp_invoice_path = TEMP_DIR / file_name
                with open(temp_invoice_path, 'wb') as f:
                    f.write(st.session_state['original_file_bytes_for_template'])

                # Determine output filename based on format
                config_suffix = "_bundle_config.json" if use_bundle_format else "_config.json"
                config_output_path = CONFIG_OUTPUT_DIR / f"{file_prefix}{config_suffix}"
                template_output_path = TEMPLATE_OUTPUT_DIR / f"{file_prefix}.xlsx"
                main_script_path = CONFIG_GEN_DIR / "main.py"

                # 3. Build and run the single, correct command.
                command = [
                    sys.executable,
                    "-X", "utf8", # Force UTF-8 mode to handle emojis in script output on Windows
                    str(main_script_path),
                    str(temp_invoice_path),
                    "-o", str(config_output_path),
                    "--generate-xlsx",
                    "--xlsx-output", str(template_output_path)
                ]

                if use_bundle_format:
                    command.append("--bundle")
                
                # This command now handles everything: analysis, config gen, and template gen.
                if not run_command(command, verbose=True, cwd=str(CONFIG_GEN_DIR)):
                    st.error("The main generation script failed. Please check the logs above.")
                    st.stop()

                # 4. Clean up temporary files
                if temp_invoice_path.exists():
                    temp_invoice_path.unlink()
                
                # Also clean up the temporary analysis file if it exists from the old workflow
                if 'analysis_path' in st.session_state and Path(st.session_state['analysis_path']).exists():
                    Path(st.session_state['analysis_path']).unlink()

                # 5. Display success and clear state
                st.success(f"Successfully created new template and configuration for `{file_prefix}`!")
                st.balloons()
                
                # Log successful template creation
                try:
                    log_business_activity(
                        user_id=user_info['user_id'],
                        username=user_info['username'],
                        activity_type='TEMPLATE_CREATED',
                        description=f"Created new invoice template for {file_prefix} from file: {file_name}",
                        action_description=f"Generated config file: {config_output_path.name}, Template file: {template_output_path.name} from '{file_name}'",
                        success=True
                    )
                except Exception as e:
                    st.warning(f"Activity logging failed: {e}")
                
                # Clean up session state
                for key in ['analysis_path', 'missing_headers', 'analysis_complete', 'user_mappings', 'file_prefix', 'original_file_bytes_for_template']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.info("You can now process shipping lists from this company on the 'Generate Invoice' page.")
                # No longer redirecting, user can create another template if they wish.

    # --- Cleanup ---
    # Consider adding a button to clear the state and start over
    if st.button("Start Over / Cancel"):
        # Clean up temporary analysis file if it exists
        if 'analysis_path' in st.session_state and Path(st.session_state['analysis_path']).exists():
            Path(st.session_state['analysis_path']).unlink()
            
        for key in ['analysis_path', 'missing_headers', 'analysis_complete', 'user_mappings', 'file_prefix', 'original_file_bytes_for_template']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
