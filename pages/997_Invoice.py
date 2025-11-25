import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import math
import io
import csv
from zoneinfo import ZoneInfo
from app import setup_page_auth
from src.auth.login import log_business_activity

# --- Helper Functions for Change Tracking ---
def generate_change_description(original_data, edited_df, max_changes=3):
    """
    Generate a detailed description of what changed between original and edited data.
    
    Args:
        original_data: Original DataFrame or list of records
        edited_df: Edited DataFrame
        max_changes: Maximum number of changes to show in description
    
    Returns:
        str: Detailed description of changes
    """
    if original_data is None or edited_df is None:
        return f"Updated {len(edited_df)} invoice records"
    
    changes = []
    
    # Convert original_data to DataFrame if it's a list
    if isinstance(original_data, list):
        if original_data:
            original_df = pd.DataFrame(original_data)
        else:
            original_df = pd.DataFrame()
    else:
        original_df = original_data
    
    if original_df.empty:
        return f"Created {len(edited_df)} new invoice records"
    
    # Get common columns
    common_cols = set(original_df.columns) & set(edited_df.columns)
    
    # Track changes for each record
    for idx in range(min(len(original_df), len(edited_df))):
        original_row = original_df.iloc[idx] if idx < len(original_df) else None
        edited_row = edited_df.iloc[idx] if idx < len(edited_df) else None
        
        if original_row is None:
            changes.append(f"Added record {idx + 1}")
            continue
        elif edited_row is None:
            changes.append(f"Removed record {idx + 1}")
            continue
        
        # Compare each field
        record_changes = []
        for col in common_cols:
            if col in ['id', 'creating_date', 'status']:  # Skip system fields
                continue
                
            orig_val = original_row[col]
            edit_val = edited_row[col]
            
            # Handle NaN values
            if pd.isna(orig_val) and pd.isna(edit_val):
                continue
            elif pd.isna(orig_val) and not pd.isna(edit_val):
                record_changes.append(f"{col}: None → {edit_val}")
            elif not pd.isna(orig_val) and pd.isna(edit_val):
                record_changes.append(f"{col}: {orig_val} → None")
            elif str(orig_val) != str(edit_val):
                # Format numeric values nicely
                if isinstance(orig_val, (int, float)) and isinstance(edit_val, (int, float)):
                    record_changes.append(f"{col}: {orig_val} → {edit_val}")
                else:
                    record_changes.append(f"{col}: '{orig_val}' → '{edit_val}'")
        
        if record_changes:
            changes.append(f"Record {idx + 1}: {', '.join(record_changes[:3])}")  # Limit to 3 changes per record
    
    # Handle added/removed records
    if len(edited_df) > len(original_df):
        changes.append(f"Added {len(edited_df) - len(original_df)} new records")
    elif len(original_df) > len(edited_df):
        changes.append(f"Removed {len(original_df) - len(edited_df)} records")
    
    if not changes:
        return f"Updated {len(edited_df)} invoice records (no field changes detected)"
    
    # Format the description
    if len(changes) <= max_changes:
        change_text = "; ".join(changes)
    else:
        change_text = "; ".join(changes[:max_changes]) + f"; ... and {len(changes) - max_changes} more changes"
    
    return f"Updated {len(edited_df)} records: {change_text}"

# --- Enhanced Authentication Setup ---
user_info = setup_page_auth(
    page_title="Invoice Management Suite", 
    page_name="Invoice Explorer",
    layout="wide"
)

st.title("Invoice Management Suite 🧭")
st.info("Use the tabs to view the invoice summary, generate reports, or manage invoice status.")

# --- Shared Configuration ---
DATA_ROOT = "data"
DATA_DIRECTORY = os.path.join(DATA_ROOT, 'Invoice Record')
DATABASE_FILE = os.path.join(DATA_DIRECTORY, 'master_invoice_data.db')
TABLE_NAME = 'invoices'
CONTAINER_TABLE_NAME = 'invoice_containers'
SUMMARY_TABLE_NAME = 'invoice_summary'
# Use the FTS table for searching
FTS_TABLE_NAME = 'summary_fts'

# --- Check for Database ---
if not os.path.exists(DATABASE_FILE):
    st.error(f"Database file not found at '{DATABASE_FILE}'. Please add an invoice first.")
    st.stop()

# --- HELPER FUNCTIONS ---
@st.cache_data
def get_overall_grand_totals():
    """Calculates and caches the grand totals for all active invoices."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        query = f"""
            SELECT
                COALESCE(SUM(total_sqft), 0), COALESCE(SUM(total_amount), 0),
                COALESCE(SUM(total_pcs), 0), COALESCE(SUM(total_net), 0),
                COALESCE(SUM(total_gross), 0), COALESCE(SUM(total_cbm), 0)
            FROM {SUMMARY_TABLE_NAME}
            WHERE status = 'active'
        """
        return conn.execute(query).fetchone()

@st.cache_data
def find_active_invoices(search_mode, search_term):
    """Finds only active invoices for legacy support if needed elsewhere."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        query = f"SELECT DISTINCT inv_no, inv_ref FROM {TABLE_NAME} WHERE LOWER({search_mode}) LIKE LOWER(?) AND status = 'active' ORDER BY inv_no"
        return [{'inv_no': row[0], 'inv_ref': row[1]} for row in conn.cursor().execute(query, (f'%{search_term}%',)).fetchall()]

def get_invoice_line_items(inv_ref):
    with sqlite3.connect(DATABASE_FILE) as conn:
        # Try exact match first
        df = pd.read_sql_query(f"SELECT id, inv_no, inv_date, inv_ref, po, item, description, pcs, sqft, pallet_count, unit, amount, net, gross, cbm, production_order_no, creating_date FROM {TABLE_NAME} WHERE inv_ref = ?", conn, params=(inv_ref,))
        
        # If no results, try case-insensitive search
        if df.empty:
            df = pd.read_sql_query(f"SELECT id, inv_no, inv_date, inv_ref, po, item, description, pcs, sqft, pallet_count, unit, amount, net, gross, cbm, production_order_no, creating_date FROM {TABLE_NAME} WHERE LOWER(inv_ref) = LOWER(?)", conn, params=(inv_ref,))
        
        return df

def get_invoice_containers(inv_ref):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT container_description FROM {CONTAINER_TABLE_NAME} WHERE inv_ref = ?", (inv_ref,))
        return [row[0] for row in cursor.fetchall()]

def update_invoice_data(original_inv_ref, edited_df, container_list):
    """
    Updates invoice data, handling inv_ref changes properly.
    original_inv_ref: The original invoice reference (used to find existing records)
    edited_df: The edited dataframe (may contain new inv_ref values)
    """
    # Get original data for logging
    original_data = None
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            original_data = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} WHERE inv_ref = ?", conn, params=(original_inv_ref,))
    except Exception as e:
        st.warning(f"Could not retrieve original data for logging: {e}")
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        try:
            # Get the new inv_ref from the edited data (all rows should have the same inv_ref)
            new_inv_refs = edited_df['inv_ref'].unique()
            if len(new_inv_refs) != 1:
                raise ValueError("All rows must have the same invoice reference")
            new_inv_ref = new_inv_refs[0]
            
            # Check if the new inv_ref already exists (and it's not the same as original)
            if new_inv_ref != original_inv_ref:
                cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE inv_ref = ? AND inv_ref != ?", (new_inv_ref, original_inv_ref))
                if cursor.fetchone()[0] > 0:
                    raise ValueError(f"Invoice reference '{new_inv_ref}' already exists in the database")
            
            # Delete old records using original inv_ref
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE inv_ref = ?", (original_inv_ref,))
            cursor.execute(f"DELETE FROM {CONTAINER_TABLE_NAME} WHERE inv_ref = ?", (original_inv_ref,))
            cursor.execute(f"DELETE FROM {SUMMARY_TABLE_NAME} WHERE inv_ref = ?", (original_inv_ref,))
            
            # Insert new records with potentially new inv_ref
            df_to_save = edited_df.copy()
            df_to_save['status'] = 'active'
            df_to_save.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
            
            # Insert container data with new inv_ref
            if container_list:
                container_data = [(new_inv_ref, desc) for desc in container_list]
                cursor.executemany(f"INSERT INTO {CONTAINER_TABLE_NAME} (inv_ref, container_description) VALUES (?, ?)", container_data)
            
            # Update summary with new inv_ref
            summary_update_query = f"""
                REPLACE INTO {SUMMARY_TABLE_NAME} (inv_ref, inv_no, inv_date, status, total_sqft, total_amount, total_pcs, total_net, total_gross, total_cbm, creating_date, containers)
                SELECT
                    i.inv_ref, MAX(i.inv_no), MAX(i.inv_date), MAX(i.status),
                    COALESCE(SUM(CAST(i.sqft AS REAL)), 0), COALESCE(SUM(CAST(i.amount AS REAL)), 0),
                    COALESCE(SUM(CAST(i.pcs AS INTEGER)), 0), COALESCE(SUM(CAST(i.net AS REAL)), 0),
                    COALESCE(SUM(CAST(i.gross AS REAL)), 0), COALESCE(SUM(CAST(i.cbm AS REAL)), 0),
                    MAX(i.creating_date), (SELECT GROUP_CONCAT(c.container_description, ', ') FROM {CONTAINER_TABLE_NAME} c WHERE c.inv_ref = i.inv_ref)
                FROM {TABLE_NAME} i WHERE i.inv_ref = ? GROUP BY i.inv_ref """
            cursor.execute(summary_update_query, (new_inv_ref,))
            cursor.execute("COMMIT;")
            
            # Log the edit activity
            try:
                # Generate detailed change description
                detailed_description = generate_change_description(original_data, edited_df)
                
                log_business_activity(
                    user_id=user_info['user_id'],
                    description=f"Edited invoice {new_inv_ref} - {detailed_description}",
                    activity_type='INVOICE_EDIT',
                    username=user_info['username'],
                    target_invoice_ref=new_inv_ref,
                    target_invoice_no=edited_df['inv_no'].iloc[0] if 'inv_no' in edited_df.columns else None,
                    action_description=detailed_description,
                    old_values=original_data.to_dict('records')[:5] if original_data is not None else None,
                    new_values=edited_df.to_dict('records')[:5],
                    success=True
                )
            except Exception as e:
                st.warning(f"Activity logging failed: {e}")
            
            # Clear all relevant caches
            get_overall_grand_totals.clear()
            find_active_invoices.clear()
        except Exception as e:
            cursor.execute("ROLLBACK;")
            raise e

def void_invoice_action(inv_ref_to_void):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        try:
            cursor.execute(f"UPDATE {TABLE_NAME} SET status = 'voided' WHERE inv_ref = ?", (inv_ref_to_void,))
            cursor.execute(f"UPDATE {SUMMARY_TABLE_NAME} SET status = 'voided' WHERE inv_ref = ?", (inv_ref_to_void,))
            conn.commit()
            
            # Log the void activity
            try:
                # Get invoice number and details for logging
                cursor.execute(f"SELECT inv_no, COUNT(*) as record_count FROM {TABLE_NAME} WHERE inv_ref = ? LIMIT 1", (inv_ref_to_void,))
                inv_result = cursor.fetchone()
                inv_no = inv_result[0] if inv_result else None
                record_count = inv_result[1] if inv_result else 0
                
                detailed_desc = f"Voided invoice {inv_ref_to_void}"
                if inv_no:
                    detailed_desc += f" (Invoice No: {inv_no})"
                detailed_desc += f" - {record_count} records marked as void"
                
                log_business_activity(
                    user_id=user_info['user_id'],
                    description=detailed_desc,
                    activity_type='INVOICE_VOID',
                    username=user_info['username'],
                    target_invoice_ref=inv_ref_to_void,
                    target_invoice_no=inv_no,
                    action_description=detailed_desc,
                    success=True
                )
            except Exception as e:
                st.warning(f"Activity logging failed: {e}")
            
            # Clear all relevant caches
            get_overall_grand_totals.clear()
            find_active_invoices.clear()
        except Exception as e:
            cursor.execute("ROLLBACK;")
            raise e

def reactivate_invoice_action(inv_ref_to_reactivate):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        try:
            cursor.execute(f"UPDATE {TABLE_NAME} SET status = 'active' WHERE inv_ref = ?", (inv_ref_to_reactivate,))
            cursor.execute(f"UPDATE {SUMMARY_TABLE_NAME} SET status = 'active' WHERE inv_ref = ?", (inv_ref_to_reactivate,))
            conn.commit()
            
            # Log the reactivation activity
            try:
                # Get invoice number and details for logging
                cursor.execute(f"SELECT inv_no, COUNT(*) as record_count FROM {TABLE_NAME} WHERE inv_ref = ? LIMIT 1", (inv_ref_to_reactivate,))
                inv_result = cursor.fetchone()
                inv_no = inv_result[0] if inv_result else None
                record_count = inv_result[1] if inv_result else 0
                
                detailed_desc = f"Reactivated invoice {inv_ref_to_reactivate}"
                if inv_no:
                    detailed_desc += f" (Invoice No: {inv_no})"
                detailed_desc += f" - {record_count} records restored to active status"
                
                log_business_activity(
                    user_id=user_info['user_id'],
                    description=detailed_desc,
                    activity_type='INVOICE_REACTIVATE',
                    username=user_info['username'],
                    target_invoice_ref=inv_ref_to_reactivate,
                    target_invoice_no=inv_no,
                    action_description=detailed_desc,
                    success=True
                )
            except Exception as e:
                st.warning(f"Activity logging failed: {e}")
            
            # Clear all relevant caches
            get_overall_grand_totals.clear()
            find_active_invoices.clear()
        except Exception as e:
            cursor.execute("ROLLBACK;")
            raise e

def permanently_delete_invoice_action(inv_ref_to_delete):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        try:
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE inv_ref = ?", (inv_ref_to_delete,))
            cursor.execute(f"DELETE FROM {CONTAINER_TABLE_NAME} WHERE inv_ref = ?", (inv_ref_to_delete,))
            cursor.execute(f"DELETE FROM {SUMMARY_TABLE_NAME} WHERE inv_ref = ?", (inv_ref_to_delete,))
            conn.commit()
            
            # Log the deletion activity
            try:
                # Get invoice number and record count for logging (before deletion)
                cursor.execute(f"SELECT inv_no, COUNT(*) as record_count FROM {TABLE_NAME} WHERE inv_ref = ? GROUP BY inv_ref", (inv_ref_to_delete,))
                inv_result = cursor.fetchone()
                inv_no = inv_result[0] if inv_result else None
                record_count = inv_result[1] if inv_result else 0
                
                detailed_desc = f"Permanently deleted invoice {inv_ref_to_delete}"
                if inv_no:
                    detailed_desc += f" (Invoice No: {inv_no})"
                detailed_desc += f" - {record_count} records and all associated data removed"
                
                log_business_activity(
                    user_id=user_info['user_id'],
                    description=detailed_desc,
                    activity_type='INVOICE_DELETE',
                    username=user_info['username'],
                    target_invoice_ref=inv_ref_to_delete,
                    target_invoice_no=inv_no,
                    action_description=detailed_desc,
                    success=True
                )
            except Exception as e:
                st.warning(f"Activity logging failed: {e}")
            
            # Clear all relevant caches
            get_overall_grand_totals.clear()
            find_active_invoices.clear()
        except Exception as e:
            cursor.execute("ROLLBACK;")
            raise e

def cancel_edit_action(inv_ref):
    """Clears all session state related to editing a specific invoice."""
    st.session_state.pop('edit_details_ref', None)
    # Clear all editor-related keys for this invoice
    keys_to_remove = [key for key in st.session_state.keys() if 
                      key.startswith(f"data_editor_{inv_ref}") or 
                      key.startswith(f"container_text_{inv_ref}")]
    for key in keys_to_remove:
        st.session_state.pop(key, None)


# --- Tabs ---
tab1, tab2 = st.tabs(["Invoice Summary", "Report Generator"])

# ==============================================================================
# TAB 1 (OPTIMIZED with FTS and Filtered Totals)
# ==============================================================================
with tab1:
    st.header("Summarized Invoice View")

    summary_filter_keys = ['summary_ref_filter', 'summary_no_filter', 'summary_date_range']
    if 'summary_current_page' not in st.session_state:
        st.session_state.summary_current_page = 1

    def reset_summary_filters_and_page():
        for key in summary_filter_keys: st.session_state[key] = None if key == 'summary_date_range' else ""
        for key in ['view_details_ref', 'edit_details_ref', 'void_confirm_ref']:
            if key in st.session_state: del st.session_state[key]
        st.session_state.summary_current_page = 1

    with st.expander("🔍 Filters for Summary View", expanded=True):
        f_col1, f_col2 = st.columns(2)
        f_col1.text_input("Filter by Invoice Ref:", key='summary_ref_filter')
        f_col2.text_input("Filter by Invoice No:", key='summary_no_filter')

        # Use Cambodia timezone for today's date
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        today_date_summary = datetime.now(cambodia_tz).date()
        st.date_input("Filter by Creation Date Range:", value=st.session_state.get('summary_date_range'), key='summary_date_range')
        
        filter_button_col1, filter_button_col2 = st.columns(2)
        filter_button_col1.button("Reset Summary Filters", on_click=reset_summary_filters_and_page, use_container_width=True, key="reset_summary")
        
        # Add manual cache refresh button
        def clear_all_caches():
            get_overall_grand_totals.clear()
            find_active_invoices.clear()
            st.success("Cache refreshed! Totals updated.")
        
        filter_button_col2.button("🔄 Refresh Totals", on_click=clear_all_caches, use_container_width=True, key="refresh_cache", help="Click if totals seem outdated")

    # Initialize filtered_totals to None
    filtered_totals = None

    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            base_query = f"FROM {SUMMARY_TABLE_NAME}"
            conditions, params = [], []

            ref_filter = st.session_state.get('summary_ref_filter', "").strip()
            no_filter = st.session_state.get('summary_no_filter', "").strip()

            if ref_filter or no_filter:
                fts_query_parts = []
                if ref_filter: fts_query_parts.append(f'inv_ref : "{ref_filter}"*')
                if no_filter: fts_query_parts.append(f'inv_no : "{no_filter}"*')
                fts_match_query = " OR ".join(fts_query_parts)

                fts_cursor = conn.cursor()
                fts_cursor.execute(f"SELECT rowid FROM {FTS_TABLE_NAME} WHERE {FTS_TABLE_NAME} MATCH ?", (fts_match_query,))
                matching_rowids = [row[0] for row in fts_cursor.fetchall()]

                if not matching_rowids:
                    matching_rowids = [-1]

                placeholders = ','.join('?' for _ in matching_rowids)
                conditions.append(f"rowid IN ({placeholders})")
                params.extend(matching_rowids)

            if st.session_state.get('summary_date_range') and len(st.session_state.summary_date_range) == 2:
                start_date, end_date = st.session_state.summary_date_range
                start_dt = datetime.combine(start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
                end_dt = datetime.combine(end_date, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')
                conditions.append("creating_date BETWEEN ? AND ?")
                params.extend([start_dt, end_dt])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            count_query = f"SELECT COUNT(*) {base_query} {where_clause}"
            total_items = conn.execute(count_query, params).fetchone()[0]

            # --- NEW: FAST SUMMATION FOR FILTERED RESULTS (ACTIVE ONLY) ---
            if where_clause:
                # Add status = 'active' condition to filtered totals
                active_condition = "status = 'active'"
                if conditions:
                    where_clause_with_active = f"WHERE {' AND '.join(conditions)} AND {active_condition}"
                    params_with_active = params
                else:
                    where_clause_with_active = f"WHERE {active_condition}"
                    params_with_active = []
                
                sum_query = f"""
                    SELECT
                        COALESCE(SUM(total_sqft), 0), COALESCE(SUM(total_amount), 0),
                        COALESCE(SUM(total_pcs), 0), COALESCE(SUM(total_net), 0),
                        COALESCE(SUM(total_gross), 0), COALESCE(SUM(total_cbm), 0)
                    {base_query} {where_clause_with_active}
                """
                filtered_totals = conn.execute(sum_query, params_with_active).fetchone()

            ITEMS_PER_PAGE = 15
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
            if st.session_state.summary_current_page > total_pages: st.session_state.summary_current_page = total_pages

            start_idx = (st.session_state.summary_current_page - 1) * ITEMS_PER_PAGE
            paginated_query = f"SELECT * {base_query} {where_clause} ORDER BY inv_ref DESC LIMIT ? OFFSET ?"
            paginated_params = params + [ITEMS_PER_PAGE, start_idx]
            paginated_df = pd.read_sql_query(paginated_query, conn, params=paginated_params)

    except Exception as e:
        st.error(f"An error occurred while querying data: {e}")
        if "no such table: summary_fts" in str(e).lower():
            st.error("The search index (FTS table) is missing. Please run the `upgrade_database.py` script to fix this.")
        st.stop()

    if paginated_df.empty:
        st.warning("No invoices match your current filter criteria.")
    else:
        st.success(f"Found {total_items} matching invoices. Showing page {st.session_state.summary_current_page} of {total_pages}.")
        for row in paginated_df.itertuples():
            current_status = row.status
            status_indicator = "🔴 VOIDED" if current_status == 'voided' else ""
            expander_title = f"**Inv No:** {row.inv_no} | **Ref:** {row.inv_ref} | **Date:** {row.inv_date} {status_indicator}"

            with st.expander(expander_title):
                st.markdown("##### Invoice Totals"); col1, col2, col3 = st.columns(3); col1.metric("Total Amount", f"${row.total_amount:,.2f}"); col2.metric("Total Pcs", f"{row.total_pcs:,.0f}"); col3.metric("Total Sqft", f"{row.total_sqft:,.2f}"); col4, col5, col6 = st.columns(3); col4.metric("Net Weight (KG)", f"{row.total_net:,.2f}"); col5.metric("Gross Weight (KG)", f"{row.total_gross:,.2f}"); col6.metric("Total CBM", f"{row.total_cbm:,.3f}")
                st.markdown("**Containers / Trucks:**"); st.info(row.containers if row.containers else "N/A")

                b_col1, b_col2, b_col3 = st.columns(3)
                is_voided = (current_status == 'voided')

                # Action buttons (View, Edit, Void)
                if st.session_state.get("view_details_ref") == row.inv_ref: b_col1.button("🔼 Hide Line Items", key=f"hide_view_{row.inv_ref}", use_container_width=True, type="primary", on_click=lambda: st.session_state.pop('view_details_ref', None))
                else: b_col1.button("📄 View Line Items", key=f"view_btn_{row.inv_ref}", use_container_width=True, on_click=lambda r=row.inv_ref: st.session_state.update(view_details_ref=r, edit_details_ref=None), disabled=is_voided)

                if st.session_state.get("edit_details_ref") == row.inv_ref: b_col2.button("🔼 Cancel Edit", key=f"hide_edit_{row.inv_ref}", use_container_width=True, type="primary", on_click=cancel_edit_action, args=(row.inv_ref,))
                else: 
                    def start_edit_action(inv_ref):
                        # Clear any existing edit states
                        if 'edit_details_ref' in st.session_state:
                            old_ref = st.session_state['edit_details_ref']
                            if old_ref != inv_ref:
                                cancel_edit_action(old_ref)
                        
                        # Increment global edit session to force fresh widgets
                        st.session_state.global_edit_session = st.session_state.get('global_edit_session', 0) + 1
                        
                        # Set new edit state
                        st.session_state.update(edit_details_ref=inv_ref, view_details_ref=None)
                    
                    b_col2.button("✏️ Edit This Invoice", key=f"edit_btn_{row.inv_ref}", use_container_width=True, on_click=start_edit_action, args=(row.inv_ref,), disabled=is_voided)

                with b_col3:
                    if not is_voided:
                        if st.session_state.get('void_confirm_ref') == row.inv_ref:
                            st.warning("Are you sure? This is reversible.")
                            confirm_c1, confirm_c2 = st.columns(2)
                            if confirm_c1.button("✅ Yes, Confirm Void", key=f"void_confirm_btn_{row.inv_ref}", use_container_width=True, type="primary"):
                                void_invoice_action(row.inv_ref); st.success(f"Invoice '{row.inv_ref}' has been voided."); del st.session_state.void_confirm_ref; get_overall_grand_totals.clear(); find_active_invoices.clear(); st.rerun()
                            if confirm_c2.button("❌ No, Cancel", key=f"void_cancel_btn_{row.inv_ref}", use_container_width=True):
                                del st.session_state.void_confirm_ref; st.rerun()
                        else:
                            if st.button("🚫 Void Invoice", key=f"void_btn_{row.inv_ref}", use_container_width=True):
                                st.session_state.void_confirm_ref = row.inv_ref; st.rerun()

                # Details/Editor Display
                if not is_voided:
                    if st.session_state.get("view_details_ref") == row.inv_ref:
                        st.markdown("---"); st.write("##### Line Item Details"); st.dataframe(get_invoice_line_items(row.inv_ref), use_container_width=True)
                    
                    # --- FORM-BASED EDIT LOGIC ---
                    if st.session_state.get("edit_details_ref") == row.inv_ref:
                        st.markdown("---")
                        st.write("##### Edit Invoice Details")
                        
                        # Load fresh data from database
                        current_df = get_invoice_line_items(row.inv_ref)
                        current_containers = get_invoice_containers(row.inv_ref)
                        
                        if current_df.empty:
                            st.error(f"❌ No line items found for invoice '{row.inv_ref}'. This invoice may not have detailed records.")
                            if st.button("Close Editor", key=f"close_empty_{row.inv_ref}"):
                                cancel_edit_action(row.inv_ref)
                                st.rerun()
                        else:
                            # Use a form to encapsulate the editing - this avoids key conflicts
                            with st.form(key=f"edit_form_{row.inv_ref}"):
                                st.write(f"📝 Editing {len(current_df)} line items for invoice: **{row.inv_ref}**")
                                
                                # Data editor without dynamic key issues
                                edited_df = st.data_editor(
                                    current_df,
                                    num_rows="dynamic",
                                    use_container_width=True,
                                    disabled=['id'],
                                    hide_index=True
                                )
                                
                                st.subheader("Containers / Trucks (One per line)")
                                edited_containers_text = st.text_area(
                                    "Containers:",
                                    value="\n".join(current_containers),
                                    height=100
                                )
                                
                                # Form buttons
                                col1, col2 = st.columns(2)
                                save_clicked = col1.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                                cancel_clicked = col2.form_submit_button("❌ Cancel", use_container_width=True)
                                
                                if save_clicked:
                                    try:
                                        # Validate that all rows have the same inv_ref
                                        unique_refs = edited_df['inv_ref'].unique()
                                        if len(unique_refs) != 1:
                                            st.error("Error: All rows must have the same invoice reference.")
                                        else:
                                            new_inv_ref = unique_refs[0]
                                            containers_to_save = [line.strip() for line in edited_containers_text.split('\n') if line.strip()]
                                            
                                            # Use the updated function with original and new inv_ref
                                            update_invoice_data(row.inv_ref, edited_df, containers_to_save)
                                            
                                            if new_inv_ref != row.inv_ref:
                                                st.success(f"Invoice reference changed from '{row.inv_ref}' to '{new_inv_ref}' and data updated successfully!")
                                            else:
                                                st.success(f"Invoice '{row.inv_ref}' has been updated successfully!")

                                            # Clear caches and session state to reflect changes
                                            get_overall_grand_totals.clear()
                                            find_active_invoices.clear()
                                            cancel_edit_action(row.inv_ref) # Clear edit state
                                            st.rerun() # Rerun to show the updated, non-edit view

                                    except Exception as e:
                                        st.error(f"Failed to save changes. Error: {e}")
                                
                                if cancel_clicked:
                                    cancel_edit_action(row.inv_ref)
                                    st.rerun()
                        
                # Management area for voided invoices
                if is_voided:
                    st.markdown("---"); st.subheader("Manage Voided Invoice")
                    manage_col1, manage_col2 = st.columns(2)
                    with manage_col1:
                        st.info("This invoice can be restored to an active state.")
                        if st.button("✅ Restore Invoice", key=f"restore_btn_{row.inv_ref}", use_container_width=True, type="primary"):
                            reactivate_invoice_action(row.inv_ref); st.success(f"Invoice '{row.inv_ref}' has been restored to active status."); get_overall_grand_totals.clear(); find_active_invoices.clear(); st.rerun()
                    with manage_col2:
                        st.error("**DANGER ZONE: Permanent Deletion**")
                        if st.checkbox("I understand this cannot be undone.", key=f"del_check_{row.inv_ref}"):
                            if st.button("❌ DELETE FOREVER", key=f"del_btn_{row.inv_ref}", use_container_width=True):
                                permanently_delete_invoice_action(row.inv_ref); st.success(f"Invoice '{row.inv_ref}' was permanently deleted."); get_overall_grand_totals.clear(); find_active_invoices.clear(); st.rerun()

        # --- NEW: DISPLAY FILTERED TOTALS ---
        if filtered_totals:
            st.markdown("---")
            st.subheader("Totals for Filtered Results (Active Invoices Only)")
            ft_sqft, ft_amount, ft_pcs, ft_net, ft_gross, ft_cbm = filtered_totals
            ft_col1, ft_col2, ft_col3 = st.columns(3)
            ft_col1.metric("Total Sqft", f"{ft_sqft:,.2f}")
            ft_col2.metric("Total Amount", f"$ {ft_amount:,.2f}")
            ft_col3.metric("Total Pcs", f"{ft_pcs:,.0f}")
            ft_col4, ft_col5, ft_col6 = st.columns(3)
            ft_col4.metric("Total Net Weight (KG)", f"{ft_net:,.2f}")
            ft_col5.metric("Total Gross Weight (KG)", f"{ft_gross:,.2f}")
            ft_col6.metric("Total CBM", f"{ft_cbm:,.3f}")
            
            # Show last updated time
            current_time = datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"📊 Filtered totals calculated at: {current_time}")

        # Pagination controls
        st.markdown("---")
        p_col1, p_col2, p_col3, p_col4 = st.columns([3, 2, 2, 3])
        if p_col1.button("⬅️ Previous", use_container_width=True, disabled=(st.session_state.summary_current_page <= 1)): st.session_state.summary_current_page -= 1; st.rerun()
        page_selection = p_col2.number_input("Page", min_value=1, max_value=total_pages, value=st.session_state.summary_current_page, key="summary_page_selector", label_visibility="collapsed")
        p_col3.markdown(f"<div style='text-align: center; margin-top: 5px;'>of {total_pages}</div>", unsafe_allow_html=True)
        if page_selection != st.session_state.summary_current_page: st.session_state.summary_current_page = page_selection; st.rerun()
        if p_col4.button("Next ➡️", use_container_width=True, disabled=(st.session_state.summary_current_page >= total_pages)): st.session_state.summary_current_page += 1; st.rerun()

    # Overall Grand Totals (this is always visible)
    st.markdown("---")
    st.subheader("Overall Grand Totals (Active Invoices)")
    try:
        total_sqft_sum, total_amount_sum, total_pcs_sum, total_net_sum, total_gross_sum, total_cbm_sum = get_overall_grand_totals()
        gt_col1, gt_col2, gt_col3 = st.columns(3); gt_col1.metric("Total Sqft", f"{total_sqft_sum:,.2f}"); gt_col2.metric("Total Amount", f"$ {total_amount_sum:,.2f}"); gt_col3.metric("Total Pcs", f"{total_pcs_sum:,.0f}")
        gt_col4, gt_col5, gt_col6 = st.columns(3); gt_col4.metric("Total Net Weight (KG)", f"{total_net_sum:,.2f}"); gt_col5.metric("Total Gross Weight (KG)", f"{total_gross_sum:,.2f}"); gt_col6.metric("Total CBM", f"{total_cbm_sum:,.3f}")
        
        # Show cache status
        current_time = datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"📊 Grand totals last updated: {current_time} | Use 'Refresh Totals' button if data seems outdated")
    except Exception as e:
        st.error(f"Could not calculate grand totals: {e}")

# ==============================================================================
# TAB 2 (Report Generator - Unchanged)
# ==============================================================================
with tab2:
    st.header("📄 Report Generator")
    st.warning("This tool is for exporting large datasets directly to a CSV file.", icon="⚙️")
    
    # --- Step 1: Select Report Mode (Unchanged) ---
    st.subheader("1. Select Report Mode")
    export_mode = st.radio("Choose report format:", ('Summarized by Invoice', 'All Individual Rows'), horizontal=True, label_visibility="collapsed")

    # --- Step 2: Filter by Date (Unchanged) ---
    st.subheader("2. Filter Data for Report by Creation Date")
    col1, col2 = st.columns(2)
    start_date_filter = col1.date_input("Start Date", value=None, key="export_start_date")
    end_date_filter = col2.date_input("End Date", value=None, key="export_end_date")

    # --- Step 3: Generate and Download (Optimized) ---
    st.subheader("3. Generate and Download")
    if st.button("Generate Report", use_container_width=True, type="primary"):
        if not start_date_filter or not end_date_filter:
            st.error("Please select both a Start Date and an End Date to generate a report.")
            st.stop() 

        start_datetime_str = datetime.combine(start_date_filter, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
        end_datetime_str = datetime.combine(end_date_filter, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')
        params = [start_datetime_str, end_datetime_str]
        
        try:
            with sqlite3.connect(DATABASE_FILE) as conn:
                if export_mode == 'Summarized by Invoice':
                    query = f"SELECT * FROM {SUMMARY_TABLE_NAME} WHERE creating_date BETWEEN ? AND ? ORDER BY creating_date DESC"
                else:
                    query = f"SELECT * FROM {TABLE_NAME} WHERE creating_date BETWEEN ? AND ?"
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                column_names = [description[0] for description in cursor.description]
                
                first_row = cursor.fetchone()
                
                if not first_row:
                    st.warning("No data found for the selected criteria.")
                else:
                    string_io = io.StringIO()
                    csv_writer = csv.writer(string_io)
                    csv_writer.writerow(column_names)
                    csv_writer.writerow(first_row)
                    
                    # Optimized with a larger chunk size for faster processing
                    while True:
                        chunk = cursor.fetchmany(10000) # Increased chunk size
                        if not chunk:
                            break
                        csv_writer.writerows(chunk)
                        
                    csv_data = string_io.getvalue().encode('utf-8')
                    file_name_mode = "summarized" if export_mode == 'Summarized by Invoice' else "all_rows"
                    file_name = f"invoice_report_{file_name_mode}_{start_date_filter}_to_{end_date_filter}.csv"
                    
                    st.download_button( "📥 Download Full Report as CSV", csv_data, file_name, 'text/csv', use_container_width=True)
                        
        except Exception as e:
            st.error(f"Could not generate report. Error: {e}")
