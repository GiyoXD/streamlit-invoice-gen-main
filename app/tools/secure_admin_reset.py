#!/usr/bin/env python3
"""
Secure admin password reset with custom password
"""

import os
import sys
import getpass
import sqlite3

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from core.auth.security import hash_password
from core.database.connection import USER_DB_PATH

def secure_admin_reset():
    """Reset admin password with user input"""
    print("🔐 Secure Admin Password Reset")
    print("=" * 40)
    
    # Get new password from user
    while True:
        new_password = getpass.getpass("Enter new admin password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            print("❌ Passwords don't match. Please try again.")
            continue
        
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters long.")
            continue
        
        break
    
    # Hash the password
    hashed_password = hash_password(new_password)
    
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Reset password and clear failed attempts
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, failed_attempts = 0, locked_until = NULL 
            WHERE username = 'menchayheng'
        ''', (hashed_password,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ Admin password reset successfully!")
            print("Username: menchayheng")
            print("Password: [hidden for security]")
        else:
            print("❌ Admin user not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")

if __name__ == "__main__":
    secure_admin_reset()