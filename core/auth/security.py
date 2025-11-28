import hashlib
import secrets
from ..database import user_repository

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return hash_password(password) == password_hash

def generate_token_string(length=32):
    """Generate a secure random token string"""
    return secrets.token_urlsafe(length)

def audit_log(user_id, event_type, description, ip_address=None, user_agent=None):
    """Log a security event"""
    user_repository.log_security_event(user_id, event_type, description, ip_address, user_agent)

def log_activity(user_id, username, activity_type, **kwargs):
    """Log a business activity"""
    # Extract optional arguments with defaults
    target_invoice_ref = kwargs.get('target_invoice_ref')
    target_invoice_no = kwargs.get('target_invoice_no')
    action_description = kwargs.get('action_description')
    old_values = kwargs.get('old_values')
    new_values = kwargs.get('new_values')
    ip_address = kwargs.get('ip_address')
    user_agent = kwargs.get('user_agent')
    success = kwargs.get('success', True)
    error_message = kwargs.get('error_message')
    description = kwargs.get('description')

    # Convert complex data types to JSON strings if needed (repository handles it? 
    # No, repository expects strings for JSON fields based on my implementation of repository?
    # Let's check repository. It takes old_values_json. So I should serialize here.)
    
    import json
    old_values_json = json.dumps(old_values) if old_values is not None else None
    new_values_json = json.dumps(new_values) if new_values is not None else None

    user_repository.log_business_activity(
        user_id, username, activity_type, target_invoice_ref, target_invoice_no,
        action_description, old_values_json, new_values_json, ip_address, user_agent,
        success, error_message, description
    )
