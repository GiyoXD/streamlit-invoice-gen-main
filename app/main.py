import streamlit as st
import sys
import os

# Add project root to sys.path so we can import from app and core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.components.auth_ui import (
    check_authentication, show_logout_button, show_user_info,
    show_login_form, get_client_ip, get_user_agent,
    require_authentication, setup_page_auth, create_admin_check_decorator
)
from core.auth.service import validate_token as validate_registration_token
from core.auth.service import register_user

# --- Authentication Functions ---
# Imported from app.components.auth_ui

# --- Page Configuration ---
st.set_page_config(
    page_title="Invoice Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Authentication Check ---
user_info = check_authentication()

# If not authenticated, show login/register page with enhanced UX
if not user_info:
    # Show a friendly message about accessing the dashboard
    st.info("🔒 Please log in to access the Invoice Dashboard. If you don't have an account, you can register with an invitation token.")
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        st.header("📝 Create New Account")
        st.info("Register a new account using an invitation token.")
        
        # Token validation section (outside form)
        st.subheader("🔍 Token Validation")
        token_input = st.text_input(
            "🔑 Invitation Token",
            placeholder="Enter your invitation token",
            help="You need a valid invitation token to register. Contact your administrator to get one.",
            key="token_input"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔍 Validate Token", use_container_width=True):
                if not token_input:
                    st.warning("Please enter a token first")
                else:
                    with st.spinner("Validating token..."):
                        is_valid, token_info = validate_registration_token(token_input)
                    
                    if is_valid:
                        st.success("✅ Token is valid!")
                        st.session_state.validated_token = token_input
                        st.session_state.token_info = token_info
                        
                        # Display token information
                        with st.expander("📋 Token Information", expanded=True):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.write("**Token Details:**")
                                st.write(f"• Created by: {token_info.get('created_by_username', 'Unknown')}")
                                st.write(f"• Created at: {token_info['created_at']}")
                                st.write(f"• Expires at: {token_info['expires_at']}")
                            
                            with col_b:
                                st.write("**Usage Information:**")
                                st.write(f"• Used: {token_info['used_count']} times")
                                st.write(f"• Max uses: {token_info['max_uses']}")
                                st.write(f"• Status: Available")
                                
                                # Calculate time remaining
                                cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
                                expiry_time = datetime.fromisoformat(token_info['expires_at'])
                                time_remaining = expiry_time - datetime.now(cambodia_tz)
                                
                                if time_remaining.total_seconds() > 0:
                                    days = time_remaining.days
                                    hours = time_remaining.seconds // 3600
                                    st.write(f"• Time remaining: {days} days, {hours} hours")
                                else:
                                    st.write("• Time remaining: Expired")
                    else:
                        st.error(f"❌ Token is invalid: {token_info}")
                        if 'validated_token' in st.session_state:
                            del st.session_state.validated_token
                        if 'token_info' in st.session_state:
                            del st.session_state.token_info
        
        with col2:
            if st.button("🗑️ Clear Token", use_container_width=True):
                if 'token_input' in st.session_state:
                    del st.session_state.token_input
                if 'validated_token' in st.session_state:
                    del st.session_state.validated_token
                if 'token_info' in st.session_state:
                    del st.session_state.token_info
                st.rerun()
        
        # Show validation status
        if 'validated_token' in st.session_state:
            st.success(f"✅ Token validated: {st.session_state.validated_token[:16]}...")
        
        st.divider()
        
        # Registration form
        with st.form("registration_form"):
            st.subheader("Enter Registration Details")
            
            # Show token status in form
            if 'validated_token' in st.session_state:
                st.info(f"🎫 Using validated token: {st.session_state.validated_token[:16]}...")
                token = st.session_state.validated_token
            else:
                st.warning("⚠️ Please validate your token above before registering")
                token = token_input
            
            # Username and password
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input(
                    "👤 Username",
                    placeholder="Choose a username",
                    help="Username must be unique and at least 3 characters long"
                )
            
            with col2:
                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    placeholder="Choose a password",
                    help="Password must be at least 6 characters long"
                )
            
            # Confirm password
            confirm_password = st.text_input(
                "🔒 Confirm Password",
                type="password",
                placeholder="Confirm your password",
                help="Must match the password above"
            )
            
            # Terms and conditions
            agree_terms = st.checkbox(
                "I agree to the terms and conditions",
                help="You must agree to the terms and conditions to register"
            )
            
            # Submit button
            if st.form_submit_button("🚀 Create Account"):
                # Validation
                errors = []
                
                if not token:
                    errors.append("❌ Invitation token is required")
                
                if not username or len(username) < 3:
                    errors.append("❌ Username must be at least 3 characters long")
                
                if not password or len(password) < 6:
                    errors.append("❌ Password must be at least 6 characters long")
                
                if password != confirm_password:
                    errors.append("❌ Passwords do not match")
                
                if not agree_terms:
                    errors.append("❌ You must agree to the terms and conditions")
                
                # Show errors if any
                if errors:
                    st.error("Please fix the following errors:")
                    for error in errors:
                        st.write(error)
                else:
                    # Validate token first
                    is_valid, token_info = validate_registration_token(token)
                    
                    if not is_valid:
                        st.error(f"❌ Invalid token: {token_info}")
                    else:
                        # Token is valid, proceed with registration
                        with st.spinner("Creating your account..."):
                            # Use register_user from service which handles token usage and creation
                            success, message = register_user(
                                username, password, token, 
                                ip_address=get_client_ip(), 
                                user_agent=get_user_agent()
                            )
                        
                        if success:
                            st.success("✅ Account created successfully!")
                            
                            st.info("You can now login with your new account.")
                            
                            # Show token info
                            with st.expander("📋 Token Information"):
                                st.write(f"**Token created by:** {token_info['created_by']}")
                                st.write(f"**Token expires:** {token_info['expires_at']}")
                                st.write(f"**Token uses:** {token_info['used_count'] + 1}/{token_info['max_uses']}")
                            
                            # Show login link
                            st.info("Click the button below to go to login:")
                            # Store success state to show button outside form
                            st.session_state.registration_success = True
                        else:
                            st.error(f"❌ Registration failed: {message}")

        # Show login button outside the form if registration was successful
        if st.session_state.get('registration_success', False):
            if st.button("🔐 Go to Login", key="reg_success_login"):
                # Clear the success state and rerun
                st.session_state.registration_success = False
                st.rerun()
    
    # Stop here if not authenticated
    st.stop()

# --- User Interface (Only shown when authenticated) ---
st.title("📊 Invoice Dashboard")
st.info("This is the main dashboard. Select other actions from the sidebar.")

# Show user info and logout button in sidebar
show_user_info()
show_logout_button()

# Add registration link for admins
if user_info and user_info['role'] == 'admin':
    st.sidebar.markdown("---")
    st.sidebar.info("**Admin Tools:**")
    if st.sidebar.button("🔑 Generate Registration Token"):
        st.info("Please use the Admin Dashboard to generate registration tokens.")
        st.info("You can access it from the sidebar navigation.")

# --- Configuration ---
# All data-related folders are now located inside the main 'data' directory.
DATA_ROOT = "data"
DATA_DIRECTORY = os.path.join(DATA_ROOT, 'Invoice Record')
DATABASE_FILE = os.path.join(DATA_DIRECTORY, 'master_invoice_data.db')
TABLE_NAME = 'invoices'

if not os.path.exists(DATABASE_FILE):
    st.error(f"Database file not found at '{DATABASE_FILE}'.")
    st.info("Please add an invoice first by navigating to the 'Add New Invoice' page from the sidebar.")
    st.stop()

# --- Load Data ---
try:
    with sqlite3.connect(DATABASE_FILE) as conn:
        # Only select active invoices for the dashboard
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} WHERE status = 'active'", conn)

    # --- Data Cleaning and Preparation ---
    if 'creating_date' in df.columns:
        df['creating_date'] = pd.to_datetime(df['creating_date'], errors='coerce')
    else:
        st.warning("Warning: 'creating_date' column not found.")
        df['creating_date'] = pd.NaT # Add dummy column to prevent errors

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['sqft'] = pd.to_numeric(df['sqft'], errors='coerce')
    df.dropna(subset=['creating_date', 'amount'], inplace=True)

except Exception as e:
    st.error(f"Could not read or process data. Error: {e}")
    st.exception(e) # Show full traceback for debugging
    st.stop()

# --- Date Range Filter ---
st.header("Filter by Creation Date")

if df.empty:
    st.warning("No active invoice data found in the database to build a dashboard.")
    st.stop()

# Handle NaT values in date columns
min_date = df['creating_date'].min()
max_date = df['creating_date'].max()

# Check if we have valid dates and provide defaults if not
if pd.isna(min_date) or pd.isna(max_date):
    # Use current date as default if no valid dates found
    from datetime import date
    today = date.today()
    start_date_default = today
    end_date_default = today
    st.warning("No valid dates found in the database. Using current date as default.")
else:
    start_date_default = min_date.date()
    end_date_default = max_date.date()

col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", start_date_default)
end_date = col2.date_input("End Date", end_date_default)

# Ensure start_date is not after end_date
if start_date > end_date:
    st.error("Error: Start date cannot be after end date.")
    st.stop()

start_datetime = datetime.combine(start_date, datetime.min.time())
end_datetime = datetime.combine(end_date, datetime.max.time())

filtered_df = df[(df['creating_date'] >= start_datetime) & (df['creating_date'] <= end_datetime)]

if filtered_df.empty:
    st.warning("No invoice data found for the selected date range. Try expanding the date filter.")
    st.stop()

# --- Display KPIs ---
st.header("Key Performance Indicators")
total_amount = filtered_df['amount'].sum()
total_sqft = filtered_df['sqft'].sum()
invoice_count = filtered_df['inv_ref'].nunique()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total Invoiced Amount", value=f"${total_amount:,.2f}")
kpi2.metric(label="Total Square Feet", value=f"{total_sqft:,.0f}")
kpi3.metric(label="Unique Invoices Added", value=invoice_count)

st.divider()

# --- Visualizations ---
st.header("Visualizations")

# Invoiced Amount Over Time (by month)
monthly_data = filtered_df.set_index('creating_date').resample('ME')['amount'].sum().reset_index()
monthly_data['creating_date'] = monthly_data['creating_date'].dt.strftime('%b %Y')
st.subheader("Total Amount by Month Added")
st.bar_chart(monthly_data.set_index('creating_date')['amount'])

# Top 10 Items by Amount, grouped by the 'item' field
st.subheader("Top 10 Products by Invoiced Amount (by Item Code)")
top_items = filtered_df.groupby('item')['amount'].sum().nlargest(10)
st.bar_chart(top_items)

# --- Admin Dashboard (Admin Only) ---
if user_info and user_info['role'] == 'admin':
        st.divider()
        st.header("🛡️ Admin Dashboard")
        st.info("Comprehensive system monitoring, security, and storage management")
        
        # Quick system overview
        try:
            from core.database.user_repository import (
                get_security_events_data as get_security_events, 
                get_business_activities_data as get_business_activities, 
                get_storage_stats_data as get_storage_stats
            )
            
            # Get quick stats
            security_events = get_security_events(limit=50)
            business_activities = get_business_activities(limit=50)
            storage_stats = get_storage_stats()
            
            # System health overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if security_events:
                    failed_logins = len([e for e in security_events if e.get('action') == 'LOGIN_FAILED'])
                    st.metric("Failed Logins", failed_logins)
                else:
                    st.metric("Failed Logins", 0)
            
            with col2:
                if business_activities:
                    recent_activities = len([a for a in business_activities 
                                           if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(days=1)])
                    st.metric("Today's Activities", recent_activities)
                else:
                    st.metric("Today's Activities", 0)
            
            with col3:
                if storage_stats:
                    total_size = storage_stats.get('total_size_kb', 0)
                    st.metric("DB Size (MB)", f"{total_size/1024:.1f}")
                else:
                    st.metric("DB Size (MB)", "N/A")
            
            with col4:
                if security_events and business_activities:
                    # Simple health indicator
                    health_score = 100
                    if failed_logins > 5:
                        health_score -= 20
                    if total_size > 5000:
                        health_score -= 20
                    
                    if health_score >= 80:
                        st.success(f"Health: {health_score}/100")
                    elif health_score >= 60:
                        st.warning(f"Health: {health_score}/100")
                    else:
                        st.error(f"Health: {health_score}/100")
                else:
                    st.info("Health: N/A")
            
            # Quick actions
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🛡️ Open Admin Dashboard"):
                    st.info("Please use the sidebar navigation to access the Admin Dashboard.")
            
            with col2:
                st.info("**Features:**")
                st.write("• 📊 System Overview & Health")
                st.write("• 🔒 Security Monitoring")
                st.write("• 📋 Activity Tracking")
                st.write("• 💾 Storage Management")
                
        except Exception as e:
            st.error(f"Could not load admin overview: {e}")
            if st.button("🛡️ Open Admin Dashboard"):
                st.info("Please use the sidebar navigation to access the Admin Dashboard.")
