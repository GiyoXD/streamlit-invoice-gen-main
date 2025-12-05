import streamlit as st
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.bulk_generator import BulkGenerator

# Constants
BASE_DIR = Path(__file__).parent.parent.parent
TEMPLATE_DIR = BASE_DIR / "database" / "template"
CONFIG_DIR = BASE_DIR / "database" / "config" / "bundled"

st.set_page_config(page_title="Bulk Generate", page_icon="🏭", layout="wide")

st.title("🏭 Bulk Invoice Generator")
st.markdown("Generate hundreds of invoices automatically from a single list.")

# --- Sidebar ---
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1.  **Prepare Data**: Excel/CSV with headers matching your placeholders (e.g., `INVOICE_NUM`).
    2.  **Select Assets**: Choose an existing Template and Config from the database.
    3.  **Upload Info**: Upload your data list.
    4.  **Go**: Click Generate.
    """)

# --- Helper Functions ---
def get_files(directory: Path, extensions: list) -> list:
    if not directory.exists():
        return []
    return [f.name for f in directory.iterdir() if f.is_file() and any(f.name.endswith(ext) for ext in extensions)]

# --- Main Interface ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Data List")
    data_file = st.file_uploader("Upload Excel or CSV List", type=["xlsx", "csv"])
    
    if data_file:
        try:
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            st.success(f"Loaded {len(df)} rows.")
            st.dataframe(df.head(3))
        except Exception as e:
            st.error(f"Error reading file: {e}")

with col2:
    st.subheader("2. Select Assets")
    
    # Template Selection
    template_files = get_files(TEMPLATE_DIR, ['.xlsx'])
    selected_template = st.selectbox("Select Template", options=["Upload New..."] + template_files, index=1 if template_files else 0)
    
    template_path = None
    if selected_template == "Upload New...":
        uploaded_template = st.file_uploader("Upload Template File", type=["xlsx"])
        if uploaded_template:
            # We'll save this to temp later
            template_path = "UPLOADED" 
    else:
        template_path = TEMPLATE_DIR / selected_template

    # Config Selection
    config_files = get_files(CONFIG_DIR, ['.json'])
    selected_config = st.selectbox("Select Configuration", options=["Upload New..."] + config_files, index=1 if config_files else 0)
    
    config_path = None
    if selected_config == "Upload New...":
        uploaded_config = st.file_uploader("Upload Bundle Config", type=["json"])
        if uploaded_config:
            # We'll save this to temp later
            config_path = "UPLOADED"
    else:
        config_path = CONFIG_DIR / selected_config

# --- Generation ---
# Check if ready
is_ready = data_file is not None
if selected_template == "Upload New...":
    is_ready = is_ready and (uploaded_template is not None)
else:
    is_ready = is_ready and (template_path is not None)

if selected_config == "Upload New...":
    is_ready = is_ready and (uploaded_config is not None)
else:
    is_ready = is_ready and (config_path is not None)


if st.button("🚀 Generate All Invoices", type="primary", disabled=not is_ready):
    
    # Create temporary directory for processing outputs and uploads
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_dir = temp_path / "output"
        
        # 1. Handle Data File
        data_path = temp_path / data_file.name
        with open(data_path, "wb") as f:
            f.write(data_file.getbuffer())
            
        # 2. Handle Template
        final_template_path = None
        if selected_template == "Upload New...":
            # Save uploaded
            t_path = temp_path / uploaded_template.name
            with open(t_path, "wb") as f:
                f.write(uploaded_template.getbuffer())
            final_template_path = t_path
            current_template_dir = temp_path # If uploaded, the dir is temp
        else:
            final_template_path = template_path
            current_template_dir = TEMPLATE_DIR # If selected, dir is database
            
        # 3. Handle Config
        final_config_path = None
        if selected_config == "Upload New...":
            c_path = temp_path / uploaded_config.name
            with open(c_path, "wb") as f:
                f.write(uploaded_config.getbuffer())
            final_config_path = c_path
            current_config_dir = temp_path
        else:
            final_config_path = config_path
            current_config_dir = CONFIG_DIR
            
        
        # Initialize Generator
        # Note: bulk_generator needs directories to resolve relative paths if they exist
        # But we are passing explicit paths too. 
        # For 'template_dir' and 'config_dir', we should pass the ones that contain the assets.
        
        generator = BulkGenerator(
            template_dir=current_template_dir,
            config_dir=current_config_dir,
            output_dir=output_dir
        )
        
        # Run
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Starting generation...")
        
        generated_files, errors = generator.process_bulk_file(data_path, final_config_path, final_template_path)
        
        progress_bar.progress(100)
        
        # Results
        if generated_files:
            st.success(f"✅ Successfully generated {len(generated_files)} invoices!")
            
            # Create Zip
            zip_path = generator.create_zip_archive(generated_files)
            
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="📦 Download All Invoices (ZIP)",
                    data=f,
                    file_name="Bulk_Invoices.zip",
                    mime="application/zip"
                )
        
        if errors:
            st.error(f"❌ Encountered {len(errors)} errors.")
            with st.expander("View Errors"):
                for err in errors:
                    st.write(err)
