import sys
import os
import sqlite3
import hashlib
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up 2 levels: tools -> app -> root
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def unlock_admin_account():
    """Unlocks the admin account by resetting failed attempts and locked_until status."""
    
    # Database path - use absolute path
    db_path = os.path.join(PROJECT_ROOT, "database", "auth", "user_database.db")
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Make sure the application has been run at least once.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if admin account exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('menchayheng',))
        count = cursor.fetchone()[0]
        
        # Use SHA-256 hashing as defined in core/auth/security.py
        password = "admin"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if count == 0:
            print("⚠️ Admin account 'menchayheng' not found. Creating it now...")
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, is_active, created_at, failed_attempts)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', ('menchayheng', hashed_password, 'admin', 1, datetime.now()))
            
            print("✅ Admin account 'menchayheng' created!")
            print(f"🔑 Password: {password}")
            
        else:
            # Reset failed attempts and unlock admin account
            # Also reset password to 'admin' to ensure access
            
            cursor.execute('''
                UPDATE users 
                SET failed_attempts = 0, locked_until = NULL, password_hash = ?
                WHERE username = 'menchayheng'
            ''', (hashed_password,))
            
            print("✅ Admin account 'menchayheng' has been unlocked!")
            print(f"🔑 Password has been reset to: {password}")

        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error unlocking/creating account: {e}")
        return False

def show_account_status():
    """Show current account status"""
    
    db_path = os.path.join(PROJECT_ROOT, "database", "auth", "user_database.db")
    
    if not os.path.exists(db_path):
        print("❌ Database not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, failed_attempts, locked_until, role
            FROM users
            ORDER BY username
        ''')
        
        users = cursor.fetchall()
        
        print("\n📊 Current Account Status:")
        print("=" * 50)
        
        for user in users:
            username, failed_attempts, locked_until, role = user
            status = "🔒 LOCKED" if locked_until else "✅ ACTIVE"
            print(f"👤 {username} ({role}) - {status}")
            print(f"   Failed attempts: {failed_attempts}")
            if locked_until:
                print(f"   Locked until: {locked_until}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking account status: {e}")

def main():
    """Main function"""
    print("🚨 Emergency Account Unlock Tool")
    print("=" * 40)
    
    # Show current status
    show_account_status()
    
    # Ask user what to do
    print("Options:")
    print("1. Unlock/Reset admin account")
    print("2. Show account status only")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🔓 Unlocking admin account...")
        if unlock_admin_account():
            print("\n🎉 Success! You can now login to the application.")
        else:
            print("\n❌ Failed to unlock account. Check the error message above.")
    
    elif choice == "2":
        print("\n📊 Showing account status...")
        show_account_status()
    
    elif choice == "3":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()