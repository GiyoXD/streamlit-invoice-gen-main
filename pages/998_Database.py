import streamlit as st
import os
import shutil
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from app import setup_page_auth

# --- Enhanced Authentication Setup ---
user_info = setup_page_auth(
    page_title="Database Manager", 
    page_name="Database Manager",
    admin_required=True,
    layout="wide"
)

st.title("Database Admin Tools 🛡️")
st.info("Use the tabs below to switch between Backup/Restore and a full Database Reset.")

# --- General Configuration ---
DATA_ROOT = "data"
DATA_DIRECTORY = os.path.join(DATA_ROOT, 'Invoice Record')
DATABASE_FILE = os.path.join(DATA_DIRECTORY, 'master_invoice_data.db')
BACKUP_DIRECTORY = 'backups'

# Confirmation phrases and passwords
RESTORE_CONFIRM_PHRASE = "overwrite my live data"
DELETE_CONFIRM_PHRASE = "delete this backup forever"
NUKE_PASSWORD = "hengh428"  # IMPORTANT: Use st.secrets in a real application

# --- Helper Functions ---

def create_backup():
    """Creates a timestamped backup of the live database file."""
    if not os.path.exists(DATABASE_FILE):
        st.error("Database file not found. Cannot perform backup.")
        return
    os.makedirs(BACKUP_DIRECTORY, exist_ok=True)
    # Use Cambodia timezone for backup timestamp
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    timestamp = datetime.now(cambodia_tz).strftime('%Y-%m-%d_%H-%M-%S')
    backup_file_name = f"master_invoice_data_{timestamp}.db"
    backup_file_path = os.path.join(BACKUP_DIRECTORY, backup_file_name)
    try:
        shutil.copy2(DATABASE_FILE, backup_file_path)
        st.success(f"Successfully created backup: **{backup_file_name}**")
    except Exception as e:
        st.error(f"Failed to create backup. Error: {e}")

def get_existing_backups():
    """Returns a sorted list of available database backups."""
    if not os.path.exists(BACKUP_DIRECTORY):
        return []
    files = [f for f in os.listdir(BACKUP_DIRECTORY) if f.endswith('.db')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIRECTORY, x)), reverse=True)
    return files

def restore_from_backup(backup_file_name):
    """Overwrites the live database with a selected backup file."""
    backup_file_path = os.path.join(BACKUP_DIRECTORY, backup_file_name)
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    shutil.copy2(backup_file_path, DATABASE_FILE)

def delete_backup_file(backup_file_name):
    """Permanently deletes a backup file."""
    backup_file_path = os.path.join(BACKUP_DIRECTORY, backup_file_name)
    os.remove(backup_file_path)

def initialize_empty_database():
    """
    Drops all existing tables, triggers, and indexes, creates the new
    schema from scratch, and reclaims unused disk space.
    """
    try:
        os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()

            # --- Drop all existing objects to ensure a clean slate ---
            # Drop triggers first
            cursor.execute("DROP TRIGGER IF EXISTS summary_au;")
            cursor.execute("DROP TRIGGER IF EXISTS summary_ad;")
            cursor.execute("DROP TRIGGER IF EXISTS summary_ai;")
            
            # Drop tables (associated indexes/FTS data are dropped automatically)
            cursor.execute("DROP TABLE IF EXISTS summary_fts;")
            cursor.execute("DROP TABLE IF EXISTS invoice_summary;")
            cursor.execute("DROP TABLE IF EXISTS invoice_containers;")
            cursor.execute("DROP TABLE IF EXISTS invoices;")

            # --- Create new schema ---
            # Create 'invoices' table
            cursor.execute("""
                CREATE TABLE invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, inv_no TEXT, inv_date TEXT,
                    inv_ref TEXT, po TEXT, item TEXT, description TEXT, pcs TEXT,
                    sqft TEXT, pallet_count TEXT, unit TEXT, amount TEXT, net TEXT,
                    gross TEXT, cbm TEXT, production_order_no TEXT, creating_date TEXT,
                    status TEXT DEFAULT 'active'
                );
            """)

            # Create 'invoice_containers' table
            cursor.execute("""
                CREATE TABLE invoice_containers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, inv_ref TEXT NOT NULL,
                    container_description TEXT NOT NULL,
                    FOREIGN KEY (inv_ref) REFERENCES invoices (inv_ref)
                );
            """)

            # Create 'invoice_summary' table
            cursor.execute("""
                CREATE TABLE invoice_summary (
                    inv_ref TEXT PRIMARY KEY, inv_no TEXT, inv_date TEXT,
                    status TEXT, total_sqft REAL, total_amount REAL,
                    total_pcs INTEGER, total_net REAL, total_gross REAL,
                    total_cbm REAL, creating_date TEXT, containers TEXT
                );
            """)

            # Create FTS5 virtual table for searching the summary
            cursor.execute("""
                CREATE VIRTUAL TABLE summary_fts USING fts5(
                    inv_ref, inv_no, containers,
                    content='invoice_summary',
                    content_rowid='rowid'
                );
            """)

            # --- Create Triggers to keep FTS table synchronized ---
            cursor.execute("""
                CREATE TRIGGER summary_ai AFTER INSERT ON invoice_summary BEGIN
                    INSERT INTO summary_fts(rowid, inv_ref, inv_no, containers)
                    VALUES (new.rowid, new.inv_ref, new.inv_no, new.containers);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER summary_ad AFTER DELETE ON invoice_summary BEGIN
                    INSERT INTO summary_fts(summary_fts, rowid, inv_ref, inv_no, containers)
                    VALUES ('delete', old.rowid, old.inv_ref, old.inv_no, old.containers);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER summary_au AFTER UPDATE ON invoice_summary BEGIN
                    INSERT INTO summary_fts(summary_fts, rowid, inv_ref, inv_no, containers)
                    VALUES ('delete', old.rowid, old.inv_ref, old.inv_no, old.containers);
                    INSERT INTO summary_fts(rowid, inv_ref, inv_no, containers)
                    VALUES (new.rowid, new.inv_ref, new.inv_no, new.containers);
                END;
            """)
            
            # --- Create Indexes for performance ---
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_inv_ref ON invoices (inv_ref);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_containers_inv_ref ON invoice_containers (inv_ref);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_inv_ref ON invoice_summary (inv_ref);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_inv_no ON invoice_summary(inv_no);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_creating_date ON invoice_summary(creating_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_containers ON invoice_summary(containers);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_lower_inv_ref ON invoices (LOWER(inv_ref));")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_lower_inv_no ON invoices (LOWER(inv_no));")

            # --- Reclaim Unused Space to Shrink File Size ---
            st.info("Reclaiming unused disk space... This may take a moment.")
            cursor.execute("VACUUM;")

        return True, "Database re-initialized and file size reclaimed successfully."
    except Exception as e:
        return False, f"An error occurred during database initialization: {e}"

# --- Callback Functions for UI State ---

def handle_restore_callback(backup_file):
    restore_from_backup(backup_file)
    st.session_state.confirm_restore = False
    st.session_state.typed_restore = ""
    st.success(f"Successfully restored database from **{backup_file}**.")
    st.balloons()

def handle_delete_callback(backup_file):
    delete_backup_file(backup_file)
    st.session_state.confirm_delete = False
    st.session_state.typed_delete = ""
    st.success(f"Successfully deleted backup file: **{backup_file}**")

# --- UI Layout with Tabs ---
tab1, tab2 = st.tabs(["Backup & Restore", "🔥 DANGER ZONE: Reset 🔥"])

# --- Tab 1: Backup and Restore ---
with tab1:
    st.header("Create a New Backup")
    st.markdown("Click the button below to create a safe, timestamped copy of your current database.")
    if st.button("➕ Create Backup Now", use_container_width=True, key="create_backup_btn"):
        with st.spinner("Creating backup..."):
            create_backup()

    st.divider()

    st.header("Manage Existing Backups")
    existing_backups = get_existing_backups()

    if not existing_backups:
        st.info("No backups available. Create one to get started.")
    else:
        selected_backup = st.selectbox(
            "Select a backup file to manage:",
            options=existing_backups,
            key="selected_backup"
        )
        if selected_backup:
            # --- Restore Sub-section ---
            with st.expander("Restore From This Backup"):
                st.warning(
                    f"Restoring from **{selected_backup}** will overwrite your live data. "
                    f"All changes made since this backup was created will be **permanently lost**."
                )
                st.checkbox("I understand I will lose current data.", key="confirm_restore")
                st.text_input("Confirm by typing:", key="typed_restore", placeholder=f"Type '{RESTORE_CONFIRM_PHRASE}' to confirm")
                is_restore_disabled = (st.session_state.get('typed_restore', '').strip() != RESTORE_CONFIRM_PHRASE or not st.session_state.get('confirm_restore', False))
                st.button("Restore From This Backup", on_click=handle_restore_callback, args=(selected_backup,), disabled=is_restore_disabled, use_container_width=True)
            
            # --- Delete Sub-section ---
            with st.expander("Delete This Backup"):
                st.error(f"**Danger:** You are about to permanently delete the backup file **{selected_backup}**. This cannot be undone.", icon="⚠️")
                st.checkbox("I understand this backup will be deleted forever.", key="confirm_delete")
                st.text_input("Confirm by typing:", key="typed_delete", placeholder=f"Type '{DELETE_CONFIRM_PHRASE}' to confirm")
                is_delete_disabled = (st.session_state.get('typed_delete', '').strip() != DELETE_CONFIRM_PHRASE or not st.session_state.get('confirm_delete', False))
                st.button("Permanently Delete This Backup", type="primary", on_click=handle_delete_callback, args=(selected_backup,), disabled=is_delete_disabled, use_container_width=True)

# --- Tab 2: Database Reset (Danger Zone) ---
with tab2:
    st.header("Permanent Database Reset")
    st.warning(
        "**CRITICAL WARNING:** This action will permanently delete all invoice and container data from the live database "
        "and shrink the database file. This is irreversible and should only be done if you are absolutely certain. "
        "Creating a backup first is highly recommended."
    )
    
    st.subheader("Authorization Required")
    st.markdown("To prevent accidental deletion, please enter the special database reset password.")
    
    password_input = st.text_input("Enter Reset Password:", type="password", key="nuke_password")
    
    password_is_correct = (password_input == NUKE_PASSWORD)

    if st.button("🔥 NUKE DATABASE AND START OVER 🔥", type="primary", disabled=not password_is_correct, use_container_width=True):
        with st.spinner("Nuking database... Please wait."):
            try:
                success, message = initialize_empty_database()
                if success:
                    st.success("✅✅✅ DATABASE RESET COMPLETE! ✅✅✅")
                    st.info("The database has been cleared, re-initialized, and the file size has been reclaimed.")
                    st.balloons()
                else:
                    st.error(f"Failed to reset the database. Error: {message}")
            except Exception as e:
                st.error(f"A critical error occurred during the reset process: {e}")
                st.error("The database may be in an unstable state. Please check application logs.")

    if not password_is_correct and st.session_state.get('nuke_password', ''):
        st.error("Incorrect password. The nuke button remains disabled.")
    elif not password_is_correct:
         st.info("The reset button is disabled until the correct password is provided.")
