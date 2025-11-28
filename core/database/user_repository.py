import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from .connection import get_db_connection

def get_user_by_username(username):
    """Retrieve user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, password_hash, role, failed_attempts, locked_until, is_active
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def update_user_login_success(user_id):
    """Reset failed attempts and update last login"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET failed_attempts = 0, locked_until = NULL, last_login = datetime('now')
        WHERE id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def update_user_login_failure(user_id, failed_attempts, lock_until):
    """Increment failed attempts and optionally lock account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET failed_attempts = ?, locked_until = ?
        WHERE id = ?
    ''', (failed_attempts, lock_until, user_id))
    
    conn.commit()
    conn.close()

def create_user(username, password_hash, role='user'):
    """Create a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def update_user_role(user_id, new_role):
    """Update user role"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    """Delete a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    """Get all users for admin panel"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, role, created_at, last_login, failed_attempts, is_active
        FROM users ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    return users

# --- Token Management ---

def create_token(token, created_by_user_id, created_by_username, expires_at, max_uses):
    """Create a registration token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO registration_tokens (token, created_by, created_by_username, expires_at, max_uses)
        VALUES (?, ?, ?, ?, ?)
    ''', (token, created_by_user_id, created_by_username, expires_at, max_uses))
    
    conn.commit()
    conn.close()

def get_active_tokens():
    """Get all active tokens"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, token, created_by, created_by_username, created_at, expires_at, max_uses, used_count
        FROM registration_tokens 
        WHERE is_active = 1 AND expires_at > datetime('now')
    ''')
    tokens = cursor.fetchall()
    conn.close()
    return tokens

def revoke_token(token_id):
    """Revoke a token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE registration_tokens SET is_active = 0 WHERE id = ?', (token_id,))
    conn.commit()
    conn.close()

def get_token(token):
    """Retrieve token details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, created_by, created_by_username, created_at, expires_at, max_uses, used_count, is_active
        FROM registration_tokens 
        WHERE token = ?
    ''', (token,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def increment_token_usage(token):
    """Increment token usage count"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE registration_tokens 
        SET used_count = used_count + 1
        WHERE token = ?
    ''', (token,))
    
    conn.commit()
    conn.close()

# --- Logging ---

def log_security_event(user_id, event_type, description, ip_address, user_agent):
    """Log a security event"""
    try:
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        current_time = datetime.now(cambodia_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (user_id, event_type, description, ip_address, user_agent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, event_type, description, ip_address, user_agent, current_time))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging security event: {e}")

def log_business_activity(user_id, username, activity_type, target_invoice_ref, 
                         target_invoice_no, action_description, old_values_json, 
                         new_values_json, ip_address, user_agent, success, 
                         error_message, description):
    """Log a business activity"""
    try:
        cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
        current_time = datetime.now(cambodia_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
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

# --- Analytics ---

def get_security_stats_data():
    """Get security statistics data"""
    try:
        conn = get_db_connection()
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
        return {'failed_logins_24h': 0, 'locked_accounts': 0, 'total_users': 0}

def get_business_activities_data(limit, days_back, activity_type, username, invoice_ref):
    """Get business activities with filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        conn.close()
        return activities
    except Exception as e:
        print(f"Error getting business activities: {e}")
        return []

def get_security_events_data(limit):
    """Get security events"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, event_type, description, ip_address, user_agent, timestamp
            FROM security_events
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        events = cursor.fetchall()
        
        # Convert to list of dicts
        columns = ['id', 'user_id', 'event_type', 'description', 'ip_address', 'user_agent', 'timestamp']
        result = [dict(zip(columns, event)) for event in events]
        
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting security events: {e}")
        return []

def get_storage_stats_data():
    """Get storage statistics"""
    try:
        # Get size of user database
        if os.path.exists(USER_DB_PATH):
            user_db_size = os.path.getsize(USER_DB_PATH)
        else:
            user_db_size = 0
            
        # Get size of activity log (if it exists separately, though we use user_db for logs now)
        # login.py defined ACTIVITY_LOG_PATH but didn't seem to use it for SQL?
        # It used USER_DB_PATH for everything.
        # We'll just return user db size.
        
        return {
            'total_size_kb': user_db_size / 1024,
            'user_db_path': USER_DB_PATH
        }
    except Exception as e:
        print(f"Error getting storage stats: {e}")
        return {'total_size_kb': 0}

def get_activity_summary_data(days_back):
    """Get summary statistics for business activities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total activities
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
        
        conn.close()
        
        return {
            'total_activities': total_activities,
            'activities_by_type': activities_by_type,
            'activities_by_user': activities_by_user,
            'success_stats': success_stats
        }
    except Exception as e:
        print(f"Error getting activity summary: {e}")
        return None
