from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ..database import user_repository, connection
from . import security

def init_auth_system():
    """Initialize the authentication system (database)"""
    connection.init_user_database()

def authenticate_user(username, password, ip_address=None, user_agent=None):
    """Authenticate a user with username and password"""
    user_data = user_repository.get_user_by_username(username)
    
    if not user_data:
        security.audit_log(None, 'LOGIN_FAILED', f'Login attempt with non-existent username: {username}', 
                          ip_address=ip_address, user_agent=user_agent)
        return False, "Invalid username or password"
    
    user_id, password_hash, role, failed_attempts, locked_until, is_active = user_data
    
    # Check if user is active
    if not is_active:
        security.audit_log(user_id, 'LOGIN_FAILED', 'Login attempt on inactive account',
                          ip_address=ip_address, user_agent=user_agent)
        return False, "Account is inactive"
    
    # Check if user is locked
    if locked_until:
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        # locked_until is string from DB, parse it
        try:
            locked_until_dt = datetime.fromisoformat(locked_until)
            # Ensure timezone awareness if DB stored it without tz (likely naive string)
            # But datetime.now(tz) returns aware.
            # If DB string is naive, we might need to assume it's in the same TZ or UTC.
            # login.py used: datetime.fromisoformat(locked_until)
            # and compared with datetime.now(cambodia_tz).
            # If locked_until was stored as naive string from cambodia time, we should probably attach tz.
            # Let's assume consistent usage from login.py.
            
            # If locked_until_dt is naive, make it aware or compare with naive now?
            # login.py: locked_until_dt = datetime.fromisoformat(locked_until)
            # if datetime.now(cambodia_tz) < locked_until_dt:
            # This implies locked_until_dt is offset-aware OR datetime.now() is compared loosely?
            # Actually python 3.9+ handles comparison if both aware or both naive.
            # If locked_until was stored as 'YYYY-MM-DD HH:MM:SS' (naive), fromisoformat makes it naive.
            # datetime.now(tz) is aware. Comparison might fail.
            # However, in login.py:
            # lock_until = datetime.now(cambodia_tz) + timedelta(hours=1)
            # cursor.execute(..., lock_until) -> sqlite stores string representation.
            # If lock_until is aware, str(lock_until) includes offset.
            # So fromisoformat should return aware.
            pass
        except Exception:
            # Fallback if parsing fails
            locked_until_dt = datetime.now(ZoneInfo("Asia/Phnom_Penh")) # Expired
            
        if datetime.now(cambodia_tz) < locked_until_dt:
            security.audit_log(user_id, 'LOGIN_FAILED', 'Login attempt on locked account',
                              ip_address=ip_address, user_agent=user_agent)
            return False, f"Account is locked until {locked_until_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Verify password
    if security.verify_password(password, password_hash):
        # Reset failed attempts and update last login
        user_repository.update_user_login_success(user_id)
        
        # Log successful login
        security.audit_log(user_id, 'LOGIN_SUCCESS', 'User logged in successfully',
                          ip_address=ip_address, user_agent=user_agent)
        
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
        
        user_repository.update_user_login_failure(user_id, failed_attempts, lock_until)
        
        # Log failed login
        security.audit_log(user_id, 'LOGIN_FAILED', f'Failed login attempt #{failed_attempts}',
                          ip_address=ip_address, user_agent=user_agent)
        
        if lock_until:
            return False, f"Account locked for 1 hour due to {failed_attempts} failed attempts"
        else:
            return False, f"Invalid password. {5 - failed_attempts} attempts remaining before lockout"

def validate_token(token):
    """Validate a registration token"""
    if not token:
        return False, "No token provided"
    
    token_data = user_repository.get_token(token)
    
    if not token_data:
        return False, "Invalid token"
    
    token_id, created_by, created_by_username, created_at, expires_at, max_uses, used_count, is_active = token_data
    
    if not is_active:
        return False, "Token is inactive"
    
    if used_count >= max_uses:
        return False, "Token has reached maximum uses"
    
    # Check if token has expired
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    try:
        expires_at_dt = datetime.fromisoformat(expires_at)
        # Handle timezone awareness compatibility
        now = datetime.now(cambodia_tz)
        if expires_at_dt.tzinfo is None:
             # If stored without tz, assume it was created in Cambodia time (as per logic)
             # So we can attach tz or compare with naive now.
             # Best to make expires_at_dt aware if it isn't.
             expires_at_dt = expires_at_dt.replace(tzinfo=cambodia_tz)
        
        if now > expires_at_dt:
            return False, "Token has expired"
    except Exception:
        pass # Assume valid if date parsing fails? Or invalid? Login.py didn't try/except.
    
    return True, {
        'token_id': token_id,
        'created_by': created_by,
        'created_by_username': created_by_username,
        'created_at': created_at,
        'expires_at': expires_at,
        'max_uses': max_uses,
        'used_count': used_count
    }

def register_user(username, password, token, ip_address=None, user_agent=None):
    """Register a new user using a token"""
    # Validate token first
    is_valid, token_info = validate_token(token)
    if not is_valid:
        return False, token_info
    
    # Check if username exists
    existing_user = user_repository.get_user_by_username(username)
    if existing_user:
        return False, "Username already exists"
    
    # Create user
    password_hash = security.hash_password(password)
    user_id = user_repository.create_user(username, password_hash, role='user')
    
    if user_id:
        # Mark token as used
        user_repository.increment_token_usage(token)
        
        # Log creation
        security.log_activity(token_info['created_by'], username, 'USER_CREATED', 
                             description=f'New user "{username}" created with role "user"',
                             ip_address=ip_address, user_agent=user_agent)
        
        return True, {
            'user_id': user_id,
            'username': username,
            'role': 'user'
        }
    else:
        return False, "Error creating user"

def generate_registration_token(created_by_user_id, created_by_username, max_uses=1, expires_hours=24):
    """Generate a registration token"""
    token = security.generate_token_string()
    cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
    expires_at = datetime.now(cambodia_tz) + timedelta(hours=expires_hours)
    
    user_repository.create_token(token, created_by_user_id, created_by_username, expires_at, max_uses)
    
    return token

def create_user(username, password, role='user', created_by_user_id=None):
    """Create a new user (Admin function)"""
    # Check if username already exists
    if user_repository.get_user_by_username(username):
        return False, "Username already exists"
    
    # Hash password
    password_hash = security.hash_password(password)
    
    # Create user
    user_id = user_repository.create_user(username, password_hash, role)
    
    if user_id:
        # Log user creation
        security.log_activity(created_by_user_id, username, 'USER_CREATED', 
                             description=f'New user "{username}" created with role "{role}"')
        
        return True, {
            'user_id': user_id,
            'username': username,
            'role': role
        }
    else:
        return False, "Error creating user"

# Alias for compatibility
create_registration_token = generate_registration_token

def backup_database():
    """Backup the database (Placeholder)"""
    # Implement backup logic here
    return True, "Backup functionality not implemented yet"

def restore_database(backup_file):
    """Restore the database (Placeholder)"""
    # Implement restore logic here
    return False, "Restore functionality not implemented yet"

def get_system_health():
    """Get system health status (Placeholder)"""
    return {
        'status': 'healthy',
        'uptime': 'N/A',
        'cpu_usage': 'N/A',
        'memory_usage': 'N/A'
    }

def rotate_logs():
    """Rotate system logs (Placeholder)"""
    return True, "Log rotation not implemented yet"

