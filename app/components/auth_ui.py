import streamlit as st
from core.auth import service
from core.database import user_repository
from datetime import datetime

def get_client_ip():
    """Get client IP address from Streamlit session state or request"""
    try:
        if hasattr(st, 'request') and hasattr(st.request, 'headers'):
            for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
                if header in st.request.headers:
                    ip = st.request.headers[header].split(',')[0].strip()
                    if ip and ip != 'unknown':
                        return ip
            if hasattr(st.request, 'remote_ip'):
                return st.request.remote_ip
        return "127.0.0.1"
    except:
        return "127.0.0.1"

def get_user_agent():
    """Get user agent from Streamlit request"""
    try:
        if hasattr(st, 'request') and hasattr(st.request, 'headers'):
            if 'User-Agent' in st.request.headers:
                return st.request.headers['User-Agent']
        return "Streamlit/1.0"
    except:
        return "Streamlit/1.0"

def check_authentication():
    """Check if user is authenticated and return user info"""
    # Initialize database if it doesn't exist
    service.init_auth_system()

    # Check if user is logged in via session state
    try:
        if 'user_info' in st.session_state:
            return st.session_state['user_info']
    except:
        pass

    return None

def show_login_form():
    """Display the login form"""
    st.header("🔐 Login to Invoice Dashboard")
    
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        login_button = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if login_button:
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                with st.spinner("Authenticating..."):
                    success, result = service.authenticate_user(
                        username, password, 
                        ip_address=get_client_ip(), 
                        user_agent=get_user_agent()
                    )
                
                if success:
                    user_info = result
                    st.session_state['user_info'] = user_info
                    st.success(f"✅ Welcome back, {user_info['username']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")

def show_user_info():
    """Display user information in sidebar"""
    user_info = st.session_state.get('user_info')
    if user_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**👤 User Information**")
        st.sidebar.write(f"**Username:** {user_info['username']}")
        st.sidebar.write(f"**Role:** {user_info['role'].title()}")
        st.sidebar.warning("⚠️ **Note:** You will need to log in again after refreshing the page")

def show_logout_button():
    """Display logout button in sidebar"""
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_button"):
        user_info = st.session_state.get('user_info')
        # We could log logout here if we want, but service doesn't have explicit logout.
        # login.py logged it directly.
        # Let's add a log call via service or security?
        # security.audit_log is available if we import security, or just skip it as it's minor.
        # login.py did: log_security_event(..., 'LOGOUT', ...)
        # I'll skip for brevity or add it if I import security.
        # Let's import security to be complete.
        from core.auth import security
        if user_info:
            security.audit_log(user_info['user_id'], 'LOGOUT', 'User logged out',
                              ip_address=get_client_ip(), user_agent=get_user_agent())
        
        if 'user_info' in st.session_state:
            del st.session_state['user_info']
        
        st.success("✅ You have been logged out successfully!")
        st.rerun()

def show_registration_form():
    """Display the registration form"""
    st.header("📝 User Registration")
    st.info("🔑 You need a valid registration token to create an account.")
    
    with st.form("registration_form"):
        token = st.text_input("🎫 Registration Token", placeholder="Enter your registration token")
        username = st.text_input("👤 Username", placeholder="Choose a username")
        password = st.text_input("🔒 Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
        
        register_button = st.form_submit_button("📝 Register", use_container_width=True)
        
        if register_button:
            if not all([token, username, password, confirm_password]):
                st.error("❌ Please fill in all fields")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
            else:
                # Register user (validates token internally)
                success, result = service.register_user(
                    username, password, token,
                    ip_address=get_client_ip(),
                    user_agent=get_user_agent()
                )
                
                if success:
                    st.success(f"✅ Account created successfully! Welcome, {username}!")
                    st.info("🚀 You can now log in with your new account.")
                else:
                    st.error(f"❌ {result}")

def show_admin_panel():
    """Display admin panel for user management"""
    st.header("🛡️ Admin Panel")
    
    user_info = st.session_state.get('user_info')
    if not user_info or user_info.get('role') != 'admin':
        st.error("🛡️ Admin privileges required")
        return
    
    st.subheader("👥 User Management")
    
    users = user_repository.get_all_users()
    
    if users:
        st.write("**Current Users:**")
        for user in users:
            user_id, username, role, created_at, last_login, failed_attempts, is_active = user
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{username}** ({role})")
            with col2:
                if is_active:
                    st.success("✅ Active")
                else:
                    st.error("❌ Inactive")
            with col3:
                if failed_attempts > 0:
                    st.warning(f"⚠️ {failed_attempts} failed attempts")
    
    st.subheader("🎫 Generate Registration Token")
    
    with st.form("admin_token_form"):
        max_uses = st.number_input("Maximum Uses", min_value=1, max_value=10, value=1)
        expires_hours = st.number_input("Expires in (hours)", min_value=1, max_value=168, value=24)
        
        if st.form_submit_button("🎫 Generate Token"):
            token = service.generate_registration_token(
                user_info['user_id'], user_info['username'], max_uses, expires_hours
            )
            st.success(f"✅ Registration token generated!")
            st.code(token)
            st.info("🔑 Share this token with the person who needs to register.")

# --- Authentication Functions ---
def require_authentication(page_name=None, admin_required=False):
    """
    Authentication wrapper that provides enhanced redirect functionality

    Args:
        page_name: Name of the current page for better redirect messages
        admin_required: Whether admin privileges are required

    Returns:
        user_info if authenticated, None otherwise (and stops execution)
    """
    # Check authentication
    user_info = check_authentication()

    if not user_info:
        # Show custom redirect message based on page
        if page_name:
            st.error(f"🔒 Authentication required to access {page_name}")
            st.info("👆 Please log in using the main page to continue.")
        else:
            st.error("🔒 Authentication required")
            st.info("👆 Please log in to continue.")

        # Provide a link back to main page
        if st.button("🏠 Go to Login Page", use_container_width=True):
            try:
                from streamlit.source_util import get_pages
                import os
                # Try to find the main script path
                main_script = os.path.join(os.getcwd(), "app", "main.py")
                pages = get_pages(main_script)
                print(f"DEBUG: Available pages: {pages}")
                st.write(f"DEBUG: Available pages: {pages}")
            except Exception as e:
                print(f"DEBUG: Error getting pages: {e}")
            
            st.switch_page("main.py")

        st.stop()

    # Check admin privileges if required
    if admin_required and user_info and user_info.get('role') != 'admin':
        st.error("🛡️ Admin privileges required to access this page")
        st.info("Contact your administrator if you need access to this feature.")

        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.switch_page("app/main.py")

        st.stop()

    return user_info

def setup_page_auth(page_title, page_name=None, admin_required=False, layout="wide"):
    """
    Complete page setup with authentication, user info, and logout button

    Args:
        page_title: Title for the page configuration
        page_name: Display name for the page (for redirect messages)
        admin_required: Whether admin privileges are required
        layout: Streamlit page layout

    Returns:
        user_info if authenticated
    """
    # Set page config
    st.set_page_config(page_title=page_title, layout=layout)

    # Require authentication
    user_info = require_authentication(page_name, admin_required)

    # Show user info and logout button in sidebar
    show_user_info()
    show_logout_button()

    return user_info

def create_admin_check_decorator(func):
    """Decorator to check admin privileges for specific functions"""
    def wrapper(*args, **kwargs):
        user_info = st.session_state.get('user_info')
        if not user_info or user_info.get('role') != 'admin':
            st.error("🛡️ Admin privileges required for this action")
            return None
        return func(*args, **kwargs)
    return wrapper
