import streamlit as st
import sqlite3
import hashlib
import secrets
import os
import json
from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database paths - use absolute paths based on script location
USER_DB_PATH = os.path.join(SCRIPT_DIR, "data", "user_database.db")
ACTIVITY_LOG_PATH = os.path.join(SCRIPT_DIR, "data", "activity_log.db")

def init_user_database():
    """Initialize the user database with required tables"""
    data_dir = os.path.join(SCRIPT_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Registration tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Security events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            description TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Business activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            activity_type TEXT NOT NULL,
            target_invoice_ref TEXT,
            target_invoice_no TEXT,
            action_description TEXT,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return hash_password(password) == password_hash

def log_security_event(user_id, event_type, description, ip_address=None, user_agent=None):
    """Log a security event"""
    try:
        # Get current time in Cambodia timezone
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        current_time = datetime.now(cambodia_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (user_id, event_type, description, ip_address, user_agent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, event_type, description, ip_address, user_agent, current_time))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging security event: {e}")

def log_business_activity(user_id, username, activity_type, target_invoice_ref=None, 
                         target_invoice_no=None, action_description=None, old_values=None, 
                         new_values=None, ip_address=None, user_agent=None, success=True, 
                         error_message=None, description=None):
    """Log a business activity"""
    try:
        # Convert complex data types to JSON strings for SQLite storage
        import json
        
        old_values_json = json.dumps(old_values) if old_values is not None else None
        new_values_json = json.dumps(new_values) if new_values is not None else None
        
        # Get current time in Cambodia timezone
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        current_time = datetime.now(cambodia_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO business_activities 
            (user_id, username, activity_type, target_invoice_ref, target_invoice_no, 
             action_description, old_values, new_values, ip_address, user_agent, 
             success, error_message, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, activity_type, target_invoice_ref, target_invoice_no,
              action_description, old_values_json, new_values_json, ip_address, user_agent,
              success, error_message, description, current_time))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging business activity: {e}")

def check_authentication():
    """Check if user is authenticated and return user info"""
    # Initialize database if it doesn't exist
    init_user_database()

    # Check if user is logged in via session state
    try:
        if 'user_info' in st.session_state:
            return st.session_state['user_info']
    except:
        # Handle case when running outside of Streamlit
        pass

    return None

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists and is not blocked
    cursor.execute('''
        SELECT id, password_hash, role, failed_attempts, locked_until, is_active
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    result = cursor.fetchone()
    
    if not result:
        log_security_event(None, 'LOGIN_FAILED', f'Login attempt with non-existent username: {username}', 
                          ip_address=get_client_ip(), user_agent=get_user_agent())
        conn.close()
        return False, "Invalid username or password"
    
    user_id, password_hash, role, failed_attempts, locked_until, is_active = result
    
    # Check if user is active
    if not is_active:
        log_security_event(user_id, 'LOGIN_FAILED', 'Login attempt on inactive account',
                          ip_address=get_client_ip(), user_agent=get_user_agent())
        conn.close()
        return False, "Account is inactive"
    
    # Check if user is locked
    if locked_until:
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        locked_until_dt = datetime.fromisoformat(locked_until)
        if datetime.now(cambodia_tz) < locked_until_dt:
            log_security_event(user_id, 'LOGIN_FAILED', 'Login attempt on locked account',
                              ip_address=get_client_ip(), user_agent=get_user_agent())
            conn.close()
            return False, f"Account is locked until {locked_until_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Verify password
    if verify_password(password, password_hash):
        # Reset failed attempts and update last login
        cursor.execute('''
            UPDATE users 
            SET failed_attempts = 0, locked_until = NULL, last_login = datetime('now')
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Log successful login
        log_security_event(user_id, 'LOGIN_SUCCESS', 'User logged in successfully',
                          ip_address=get_client_ip(), user_agent=get_user_agent())
        
        return True, {
            'user_id': user_id,
            'username': username,
            'role': role
        }
    else:
        # Increment failed attempts
        failed_attempts += 1
        lock_until = None
        
        # Lock account after 5 failed attempts for 1 hour
        if failed_attempts >= 5:
            cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
            lock_until = datetime.now(cambodia_tz) + timedelta(hours=1)
        
        cursor.execute('''
            UPDATE users 
            SET failed_attempts = ?, locked_until = ?
            WHERE id = ?
        ''', (failed_attempts, lock_until, user_id))
        
        conn.commit()
        conn.close()
        
        # Log failed login
        log_security_event(user_id, 'LOGIN_FAILED', f'Failed login attempt #{failed_attempts}',
                          ip_address=get_client_ip(), user_agent=get_user_agent())
        
        if lock_until:
            return False, f"Account locked for 1 hour due to {failed_attempts} failed attempts"
        else:
            return False, f"Invalid password. {5 - failed_attempts} attempts remaining before lockout"

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
                    success, result = authenticate_user(username, password)
                
                if success:
                    user_info = result
                    
                    # Store user info in session state (temporary, will be lost on refresh)
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
        if user_info:
            log_security_event(user_info['user_id'], 'LOGOUT', 'User logged out',
                              ip_address=get_client_ip(), user_agent=get_user_agent())
        
        # Clear user info from session state
        if 'user_info' in st.session_state:
            del st.session_state['user_info']
        
        st.success("✅ You have been logged out successfully!")
        st.rerun()

# Registration and token functions (keeping existing functionality)
def generate_registration_token(created_by_user_id, created_by_username, max_uses=1, expires_hours=24):
    """Generate a registration token"""
    token = secrets.token_urlsafe(32)
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    expires_at = datetime.now(cambodia_tz) + timedelta(hours=expires_hours)
    
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO registration_tokens (token, created_by, created_by_username, expires_at, max_uses)
        VALUES (?, ?, ?, ?, ?)
    ''', (token, created_by_user_id, created_by_username, expires_at, max_uses))
    
    conn.commit()
    conn.close()
    
    return token

def validate_registration_token(token):
    """Validate a registration token"""
    if not token:
        return False, "No token provided"
    
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, created_by, created_by_username, created_at, expires_at, max_uses, used_count, is_active
        FROM registration_tokens 
        WHERE token = ?
    ''', (token,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False, "Invalid token"
    
    token_id, created_by, created_by_username, created_at, expires_at, max_uses, used_count, is_active = result
    
    if not is_active:
        return False, "Token is inactive"
    
    if used_count >= max_uses:
        return False, "Token has reached maximum uses"
    
    # Check if token has expired
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    expires_at_dt = datetime.fromisoformat(expires_at)
    if datetime.now(cambodia_tz) > expires_at_dt:
        return False, "Token has expired"
    
    return True, {
        'token_id': token_id,
        'created_by': created_by,
        'created_by_username': created_by_username,
        'created_at': created_at,
        'expires_at': expires_at,
        'max_uses': max_uses,
        'used_count': used_count
    }

def use_registration_token(token):
    """Mark a registration token as used"""
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE registration_tokens 
        SET used_count = used_count + 1
        WHERE token = ?
    ''', (token,))
    
    conn.commit()
    conn.close()

def create_user(username, password, role='user', created_by_user_id=None):
    """Create a new user"""
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists"
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log user creation
        log_business_activity(created_by_user_id, username, 'USER_CREATED', 
                             description=f'New user "{username}" created with role "{role}"',
                             ip_address=get_client_ip(), user_agent=get_user_agent())
        
        return True, {
            'user_id': user_id,
            'username': username,
            'role': role
        }
        
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

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
                # Validate token
                token_valid, token_info = validate_registration_token(token)
                if not token_valid:
                    st.error(f"❌ {token_info}")
                else:
                    # Create user
                    success, result = create_user(username, password, 'user', token_info['created_by'])
                    if success:
                        # Use the token
                        use_registration_token(token)
                        st.success(f"✅ Account created successfully! Welcome, {username}!")
                        st.info("🚀 You can now log in with your new account.")
                    else:
                        st.error(f"❌ {result}")

def show_admin_panel():
    """Display admin panel for user management"""
    st.header("🛡️ Admin Panel")
    
    # Check if current user is admin
    user_info = st.session_state.get('user_info')
    if not user_info or user_info.get('role') != 'admin':
        st.error("🛡️ Admin privileges required")
        return
    
    st.subheader("👥 User Management")
    
    # Show existing users
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, role, created_at, last_login, failed_attempts, is_active
        FROM users ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
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
            token = generate_registration_token(user_info['user_id'], user_info['username'], max_uses, expires_hours)
            st.success(f"✅ Registration token generated!")
            st.code(token)
            st.info("🔑 Share this token with the person who needs to register.")

def get_security_stats():
    """Get security statistics for dashboard"""
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Failed logins in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) FROM security_events 
            WHERE event_type = 'LOGIN_FAILED' 
            AND timestamp > datetime('now', '-1 day')
        ''')
        failed_logins_24h = cursor.fetchone()[0]
        
        # Locked accounts
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE locked_until > datetime('now')
        ''')
        locked_accounts = cursor.fetchone()[0]
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'failed_logins_24h': failed_logins_24h,
            'locked_accounts': locked_accounts,
            'total_users': total_users
        }
        
    except Exception as e:
        print(f"Error getting security stats: {e}")
        return {
            'failed_logins_24h': 0,
            'locked_accounts': 0,
            'total_users': 0
        }

def get_business_activities(limit=100, days_back=7, activity_type=None, username=None, invoice_ref=None):
    """Get business activities with filtering options"""
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Build the query with filters
        query = '''
            SELECT 
                ba.id, ba.user_id, ba.username, ba.activity_type, 
                ba.target_invoice_ref, ba.target_invoice_no, ba.action_description,
                ba.old_values, ba.new_values, ba.ip_address, ba.user_agent,
                ba.success, ba.error_message, ba.timestamp, ba.description
            FROM business_activities ba
            WHERE ba.timestamp > datetime('now', '-{} days')
        '''.format(days_back)
        
        params = []
        
        if activity_type and activity_type != "All":
            query += " AND ba.activity_type = ?"
            params.append(activity_type)
        
        if username:
            query += " AND ba.username LIKE ?"
            params.append(f"%{username}%")
        
        if invoice_ref:
            query += " AND (ba.target_invoice_ref LIKE ? OR ba.target_invoice_no LIKE ?)"
            params.extend([f"%{invoice_ref}%", f"%{invoice_ref}%"])
        
        query += " ORDER BY ba.timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        activities = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = ['id', 'user_id', 'username', 'activity_type', 'target_invoice_ref', 
                  'target_invoice_no', 'action_description', 'old_values', 'new_values',
                  'ip_address', 'user_agent', 'success', 'error_message', 'timestamp', 
                  'description']
        
        result = []
        for activity in activities:
            activity_dict = dict(zip(columns, activity))
            
            # Deserialize JSON data back to Python objects
            import json
            if activity_dict['old_values']:
                try:
                    activity_dict['old_values'] = json.loads(activity_dict['old_values'])
                except:
                    pass  # Keep as string if JSON parsing fails
            if activity_dict['new_values']:
                try:
                    activity_dict['new_values'] = json.loads(activity_dict['new_values'])
                except:
                    pass  # Keep as string if JSON parsing fails
            
            result.append(activity_dict)
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error getting business activities: {e}")
        return []

def get_activity_summary(days_back=7):
    """Get summary statistics for business activities"""
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Total activities in time period
        cursor.execute('''
            SELECT COUNT(*) FROM business_activities 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days_back))
        total_activities = cursor.fetchone()[0]
        
        # Activities by type
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count 
            FROM business_activities 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY activity_type 
            ORDER BY count DESC
        '''.format(days_back))
        activities_by_type = cursor.fetchall()
        
        # Activities by user
        cursor.execute('''
            SELECT username, COUNT(*) as count 
            FROM business_activities 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY username 
            ORDER BY count DESC
        '''.format(days_back))
        activities_by_user = cursor.fetchall()
        
        # Success rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM business_activities 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days_back))
        success_stats = cursor.fetchone()
        success_rate = (success_stats[1] / success_stats[0] * 100) if success_stats[0] > 0 else 0
        
        conn.close()
        
        return {
            'total_activities': total_activities,
            'activities_by_type': dict(activities_by_type),
            'activities_by_user': dict(activities_by_user),
            'success_rate': round(success_rate, 1)
        }
        
    except Exception as e:
        print(f"Error getting activity summary: {e}")
        return {
            'total_activities': 0,
            'activities_by_type': {},
            'activities_by_user': {},
            'success_rate': 0
        }

def get_client_ip():
    """Get client IP address from Streamlit session state or request"""
    try:
        # Try to get from request headers (if available)
        if hasattr(st, 'request') and hasattr(st.request, 'headers'):
            # Check common IP headers
            for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
                if header in st.request.headers:
                    ip = st.request.headers[header].split(',')[0].strip()
                    if ip and ip != 'unknown':
                        return ip
            
            # Fallback to remote address
            if hasattr(st.request, 'remote_ip'):
                return st.request.remote_ip
        
        # Default fallback
        return "127.0.0.1"
    except:
        return "127.0.0.1"

def get_user_agent():
    """Get user agent from Streamlit request"""
    try:
        # Try to get from request headers
        if hasattr(st, 'request') and hasattr(st.request, 'headers'):
            if 'User-Agent' in st.request.headers:
                return st.request.headers['User-Agent']
        
        # Default fallback
        return "Streamlit/1.0"
    except:
        return "Streamlit/1.0"

# Initialize database on import
init_user_database()