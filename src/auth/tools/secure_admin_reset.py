#!/usr/bin/env python3
"""
Secure admin password reset with custom password
"""

import sys
import getpass
sys.path.append('.')
from login import hash_password, USER_DB_PATH
import sqlite3

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