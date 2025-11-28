import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import shutil
import json
import time
from zoneinfo import ZoneInfo
from app.components.auth_ui import setup_page_auth
from core.database.user_repository import log_business_activity

# --- Enhanced Authentication Setup ---
user_info = setup_page_auth(
    page_title="Add Invoice", 
    page_name="Add Invoice",
    layout="wide"
)

st.title("Add / Amend Invoice ➕")

# --- Configuration ---
DATA_ROOT = Path("database")
INVOICE_ROOT = DATA_ROOT / 'invoice'
JSON_DIRECTORY = INVOICE_ROOT / 'invoices_to_process'
FAILED_DIRECTORY = INVOICE_ROOT / 'failed_invoices'
AMENDMENT_ARCHIVE_DIRECTORY = INVOICE_ROOT / 'amendment_archive'
DB_DIRECTORY = INVOICE_ROOT
DATABASE_FILE = DB_DIRECTORY / 'master_invoice_data.db'
TABLE_NAME = 'invoices'
CONTAINER_TABLE_NAME = 'invoice_containers'
SUMMARY_TABLE_NAME = 'invoice_summary' # Added for summary updates
FINAL_COLUMNS = [
    'inv_no', 'inv_date', 'inv_ref', 'po', 'item', 'description', 'pcs',
    'sqft', 'pallet_count', 'unit', 'amount', 'net', 'gross', 'cbm',
    'production_order_no', 'creating_date', 'status'
]

# --- Helper Functions ---
def setup_directories():
    """Create all necessary directories if they don't exist."""
    for directory in [JSON_DIRECTORY, FAILED_DIRECTORY, AMENDMENT_ARCHIVE_DIRECTORY, DB_DIRECTORY]:
        directory.mkdir(exist_ok=True)

def get_existing_invoice_data(inv_ref, inv_no):
    """Gets all data for a specific invoice based on an EXACT match of inv_ref or inv_no."""
    if not os.path.exists(DATABASE_FILE):
        return None
    with sqlite3.connect(DATABASE_FILE) as conn:
        query = f"""
        SELECT i.*,
               (SELECT GROUP_CONCAT(c.container_description, ', ')
                FROM {CONTAINER_TABLE_NAME} c
                WHERE c.inv_ref = i.inv_ref) AS containers
        FROM {TABLE_NAME} i
        WHERE (LOWER(i.inv_ref) = LOWER(?) AND i.inv_ref != '') OR (LOWER(i.inv_no) = LOWER(?) AND i.inv_no != '')
        """
        df = pd.read_sql_query(query, conn, params=(inv_ref, inv_no))
        return df if not df.empty else None

def process_json_file(file_path):
    """Processes JSON focusing on 'processed_tables_data' and extracts container info."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_tables = data.get('processed_tables_data')
    if not processed_tables:
        if 'aggregated_summary' in data:
            df = pd.DataFrame([data['aggregated_summary']])
        else:
            raise ValueError("File does not contain 'processed_tables_data' or 'aggregated_summary'.")
    else:
        all_dfs = [pd.DataFrame(table_data) for table_data in processed_tables.values()]
        df = pd.concat(all_dfs, ignore_index=True)

    df['inv_no'] = df['inv_no'].apply(lambda x: x if isinstance(x, str) and x.strip() and not x.startswith('0') else pd.NA).ffill()
    df['inv_ref'] = df['inv_ref'].apply(lambda x: str(x).strip() if isinstance(x, str) and x.strip() else pd.NA).ffill()
    df['inv_date'] = pd.to_datetime(df['inv_date'], errors='coerce').ffill().dt.strftime('%Y-%m-%d')
    manual_containers = []
    if 'container_type' in df.columns:
        container_str = df['container_type'].dropna().astype(str).unique()
        if len(container_str) > 0:
            manual_containers = [c.strip() for c in container_str[0].split(',') if c.strip()]
    # Use Cambodia timezone for creating_date
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    df['creating_date'] = datetime.now(cambodia_tz).strftime('%Y-%m-%d %H:%M:%S')
    df['status'] = 'active'
    
    # Define columns that should NOT be converted to numeric
    string_columns = ['inv_no', 'inv_ref', 'po', 'item', 'description', 'unit', 'production_order_no', 'status', 'creating_date', 'inv_date']
    
    # Convert only the appropriate columns to numeric types
    for col in df.columns:
        if col not in string_columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
            
    return df.reindex(columns=FINAL_COLUMNS), manual_containers

def update_summary_for_invoice(conn, inv_ref_to_update):
    """
    Calculates and saves a summary record for a given invoice reference.
    This function is the key to keeping the explorer page synchronized.
    """
    cursor = conn.cursor()
    summary_update_query = f"""
        REPLACE INTO {SUMMARY_TABLE_NAME} (inv_ref, inv_no, inv_date, status, total_sqft, total_amount, total_pcs, total_net, total_gross, total_cbm, creating_date, containers)
        SELECT
            i.inv_ref, MAX(i.inv_no), MAX(i.inv_date), MAX(i.status),
            COALESCE(SUM(CAST(i.sqft AS REAL)), 0), COALESCE(SUM(CAST(i.amount AS REAL)), 0),
            COALESCE(SUM(CAST(i.pcs AS INTEGER)), 0), COALESCE(SUM(CAST(i.net AS REAL)), 0),
            COALESCE(SUM(CAST(i.gross AS REAL)), 0), COALESCE(SUM(CAST(i.cbm AS REAL)), 0),
            MAX(i.creating_date), (SELECT GROUP_CONCAT(c.container_description, ', ') FROM {CONTAINER_TABLE_NAME} c WHERE c.inv_ref = i.inv_ref)
        FROM {TABLE_NAME} i WHERE i.inv_ref = ? GROUP BY i.inv_ref
    """
    cursor.execute(summary_update_query, (inv_ref_to_update,))
    conn.commit()
    st.write(f"Updated summary for invoice ref: `{inv_ref_to_update}`")

def display_containers(container_list):
    """Displays a list of containers as colorful, styled tags."""
    if not container_list:
        st.markdown("`None`")
        return
    colors = ["#FFC107", "#03A9F4", "#4CAF50", "#F44336", "#9C27B0", "#FF9800"]
    html_tags = "".join(
        f'<span style="background-color: {colors[i % len(colors)]}; color: white; padding: 5px 10px; margin: 3px; border-radius: 5px; display: inline-block;">{container}</span>'
        for i, container in enumerate(container_list)
    )
    st.markdown(html_tags, unsafe_allow_html=True)

def handle_amendment(source_file_path, new_df, existing_df, manual_containers):
    """UI for approving an amendment, now with summary update."""
    st.warning(f"This Invoice Ref **'{new_df['inv_ref'].iloc[0]}'** or Invoice No **'{new_df['inv_no'].iloc[0]}'** already exists. Review and approve the amendment.", icon="⚠️")

    st.header("Review Changes")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Data in Database")
        st.dataframe(existing_df.drop(columns=['containers'], errors='ignore'))
    with col2:
        st.subheader("New Data from File")
        st.dataframe(new_df)

    st.subheader("Containers / Trucks")
    display_containers(manual_containers)
    st.header("Approve Amendment?")
    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("✅ Accept Changes", use_container_width=True):
        inv_refs_to_delete = existing_df['inv_ref'].unique().tolist()
        new_inv_ref = new_df['inv_ref'].iloc[0]
        
        # Log the amendment activity
        try:
            log_business_activity(
                user_id=user_info['user_id'],
                description=f"Amended invoice data from file '{source_file_path.name}' - Replaced {len(existing_df)} records with {len(new_df)} new records",
                activity_type='DATA_AMENDMENT',
                username=user_info['username'],
                target_invoice_ref=str(new_inv_ref),
                target_invoice_no=str(new_df['inv_no'].iloc[0]) if 'inv_no' in new_df.columns and pd.notna(new_df['inv_no'].iloc[0]) else None,
                action_description=f"Amended invoice data from '{source_file_path.name}' - Replaced {len(existing_df)} records with {len(new_df)} new records",
                old_values=existing_df.to_dict('records')[:5],  # Store first 5 records as sample
                new_values=new_df.to_dict('records')[:5],  # Store first 5 records as sample
                success=True
            )
        except Exception as e:
            st.warning(f"Activity logging failed: {e}")
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            st.write(f"Deleting all records for matched Invoice Refs: `{', '.join(inv_refs_to_delete)}`...")
            for ref in inv_refs_to_delete:
                cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE inv_ref = ?", (ref,))
                cursor.execute(f"DELETE FROM {CONTAINER_TABLE_NAME} WHERE inv_ref = ?", (ref,))
            st.write("Inserting new records...")
            new_df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
            if manual_containers:
                st.write("Saving container info...")
                for container in manual_containers:
                    cursor.execute(f"INSERT INTO {CONTAINER_TABLE_NAME} (inv_ref, container_description) VALUES (?, ?)", (new_inv_ref, container))
            conn.commit()
            # --- UPDATE SUMMARY ---
            update_summary_for_invoice(conn, new_inv_ref)
        os.remove(source_file_path)
        st.success("Amendment approved! Old data replaced, summary updated, and source file deleted.")
        st.rerun()

    if c2.button("❌ Reject Changes", use_container_width=True):
        # Log the rejection
        try:
            log_business_activity(
                user_id=user_info['user_id'],
                description=f"Rejected amendment proposal from file '{source_file_path.name}'",
                activity_type='DATA_AMENDMENT',
                username=user_info['username'],
                target_invoice_ref=str(new_df['inv_ref'].iloc[0]) if 'inv_ref' in new_df.columns and pd.notna(new_df['inv_ref'].iloc[0]) else None,
                target_invoice_no=str(new_df['inv_no'].iloc[0]) if 'inv_no' in new_df.columns and pd.notna(new_df['inv_no'].iloc[0]) else None,
                action_description=f"Rejected amendment proposal from '{source_file_path.name}'",
                old_values=existing_df.to_dict('records')[:5],
                new_values=new_df.to_dict('records')[:5],
                success=True
            )
        except Exception as e:
            st.warning(f"Activity logging failed: {e}")
        
        os.remove(source_file_path)
        st.warning("Amendment rejected. The source JSON file has been permanently deleted.")
        st.rerun()

def handle_new_invoice(source_file_path, new_df, manual_containers):
    """UI for adding a new invoice, now with summary update."""
    st.info(f"Now verifying new invoice: **{source_file_path.name}**")
    new_inv_ref = new_df['inv_ref'].iloc[0]

    st.dataframe(new_df)
    st.subheader("Containers / Trucks")
    display_containers(manual_containers)

    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("✅ Accept", use_container_width=True):
        # Log the new invoice verification
        try:
            log_business_activity(
                user_id=user_info['user_id'],
                description=f"Verified and inserted new invoice from file '{source_file_path.name}' - {len(new_df)} records added",
                activity_type='DATA_VERIFICATION',
                username=user_info['username'],
                target_invoice_ref=str(new_inv_ref),
                target_invoice_no=str(new_df['inv_no'].iloc[0]) if 'inv_no' in new_df.columns and pd.notna(new_df['inv_no'].iloc[0]) else None,
                action_description=f"Verified and inserted new invoice from '{source_file_path.name}' - {len(new_df)} records added",
                new_values=new_df.to_dict('records')[:5],  # Store first 5 records as sample
                success=True
            )
        except Exception as e:
            st.warning(f"Activity logging failed: {e}")
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            new_df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
            if manual_containers:
                cursor = conn.cursor()
                st.write("Saving container info...")
                for container in manual_containers:
                    cursor.execute(f"INSERT INTO {CONTAINER_TABLE_NAME} (inv_ref, container_description) VALUES (?, ?)", (new_inv_ref, container))
            conn.commit()
            # --- UPDATE SUMMARY ---
            update_summary_for_invoice(conn, new_inv_ref)
        os.remove(source_file_path)
        st.success(f"Invoice '{new_inv_ref}' added, summary updated, and source file deleted.")
        st.rerun()

    if c2.button("❌ Reject", use_container_width=True):
        # Log the rejection
        try:
            log_business_activity(
                user_id=user_info['user_id'],
                description=f"Rejected new invoice proposal from file '{source_file_path.name}'",
                activity_type='DATA_VERIFICATION',
                username=user_info['username'],
                target_invoice_ref=str(new_inv_ref),
                target_invoice_no=str(new_df['inv_no'].iloc[0]) if 'inv_no' in new_df.columns and pd.notna(new_df['inv_no'].iloc[0]) else None,
                action_description=f"Rejected new invoice proposal from '{source_file_path.name}'",
                new_values=new_df.to_dict('records')[:5],
                success=True
            )
        except Exception as e:
            st.warning(f"Activity logging failed: {e}")
        
        os.remove(source_file_path)
        st.warning(f"Invoice '{new_inv_ref}' rejected and source file deleted.")
        st.rerun()

def extract_invoice_info_from_filename(filename):
    """
    Extract invoice reference and number from filename.
    Looks for patterns like 'TH25003', 'JLFHM25004', 'MOTO25042E', etc.
    """
    import re
    from pathlib import Path
    
    # Get filename without extension
    stem = Path(filename).stem
    
    # Common patterns for invoice references
    # Pattern 1: Letters followed by numbers (e.g., TH25003, JLFHM25004, MOTO25042E)
    pattern1 = re.search(r'([A-Z]+[0-9]+[A-Z]*)', stem.upper())
    if pattern1:
        candidate = pattern1.group(1)
        # If it looks like a valid invoice ref (letters + numbers), return it
        if len(candidate) >= 4 and any(c.isdigit() for c in candidate):
            return candidate
    
    # Pattern 2: Numbers with letters (e.g., 25042E)
    pattern2 = re.search(r'(\d+[A-Z]+)', stem.upper())
    if pattern2:
        candidate = pattern2.group(1)
        if len(candidate) >= 4:
            return candidate
    
    # Pattern 3: Just numbers that look like invoice numbers
    pattern3 = re.search(r'(\d{5,})', stem)
    if pattern3:
        candidate = pattern3.group(1)
        if len(candidate) >= 5:
            return candidate
    
    return None

def get_invoice_ref_and_no(df, filename):
    """
    Get the best available invoice reference and number.
    Priority: DataFrame values > extracted from filename > None
    """
    # Try to get from DataFrame first
    inv_ref = None
    inv_no = None
    
    if 'inv_ref' in df.columns and not df['inv_ref'].isna().all():
        first_ref = df['inv_ref'].iloc[0]
        if pd.notna(first_ref) and str(first_ref).strip() and not str(first_ref).startswith(('aklsdfj', 'dsfj')):
            inv_ref = str(first_ref).strip()
    
    if 'inv_no' in df.columns and not df['inv_no'].isna().all():
        first_no = df['inv_no'].iloc[0]
        if pd.notna(first_no) and str(first_no).strip() and not str(first_no).startswith(('dsfj', 'aklsdfj')):
            inv_no = str(first_no).strip()
    
    # If we don't have good values from DataFrame, try to extract from filename
    if not inv_ref:
        extracted = extract_invoice_info_from_filename(filename)
        if extracted:
            inv_ref = extracted
    
# --- Main Application Logic ---
setup_directories()
json_files = sorted(JSON_DIRECTORY.glob('*.json'))

if not json_files:
    st.success("✅ No new invoices to process.")
    st.stop()

file_to_process = json_files[0]

try:
    new_invoice_df, manual_containers = process_json_file(file_to_process)
    if new_invoice_df.empty:
        raise ValueError("Processing the file resulted in an empty dataset.")

    inv_ref = str(new_invoice_df['inv_ref'].iloc[0]).strip()
    inv_no = str(new_invoice_df['inv_no'].iloc[0]).strip()
    if not inv_ref and not inv_no:
        raise ValueError("Could not determine a valid Invoice Ref or Invoice No from the file.")

    existing_invoice_df = get_existing_invoice_data(inv_ref, inv_no)
    if existing_invoice_df is not None:
        handle_amendment(file_to_process, new_invoice_df, existing_invoice_df, manual_containers)
    else:
        handle_new_invoice(file_to_process, new_invoice_df, manual_containers)

except Exception as e:
    st.error("An Error Occurred While Processing a File", icon="🚨")
    st.subheader("Problematic File Name:")
    st.code(file_to_process.name, language=None)
    st.subheader("Error Details:")
    st.exception(e)
    failed_file_path = FAILED_DIRECTORY / file_to_process.name
    st.warning("This file will be moved to the `failed_invoices` folder.")
    if st.button("Move File and Continue ➡️", use_container_width=True, key="continue_after_error"):
        # Log the failed file processing
        try:
            log_business_activity(
                user_id=user_info['user_id'],
                username=user_info['username'],
                activity_type='DATA_VERIFICATION',
                description=f"Failed to process invoice file '{file_to_process.name}' - moved to failed folder",
                action_description=f"File processing failed for '{file_to_process.name}' due to: {str(e)}",
                success=False,
                error_message=str(e)
            )
        except Exception as log_e:
            st.warning(f"Activity logging failed: {log_e}")
        
        shutil.move(str(file_to_process), str(failed_file_path))
        st.success(f"File '{file_to_process.name}' moved. Loading next file...")
        time.sleep(2)
        st.rerun()
    st.stop()
