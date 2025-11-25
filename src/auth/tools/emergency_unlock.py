#!/usr/bin/env python3
"""
Emergency Account Unlock Script
Use this if you get locked out of the admin account
"""

import sqlite3
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get to the main app directory
APP_DIR = os.path.dirname(SCRIPT_DIR)

def unlock_admin_account():
    """Unlock the admin account by resetting failed attempts"""
    
    # Database path - use absolute path
    db_path = os.path.join(APP_DIR, "data", "user_database.db")
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Make sure the application has been run at least once.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Reset failed attempts and unlock admin account
        cursor.execute('''
            UPDATE users 
            SET failed_attempts = 0, locked_until = NULL
            WHERE username = 'menchayheng'
        ''')
        
        # Check if admin account exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('menchayheng',))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("❌ Admin account 'menchayheng' not found in database.")
            return False
        
        conn.commit()
        conn.close()
        
        print("✅ Admin account 'menchayheng' has been unlocked!")
        print("🔑 You can now login with:")
        print("   Username: menchayheng")
        print("   Password: hengh428")
        return True
        
    except Exception as e:
        print(f"❌ Error unlocking account: {e}")
        return False

def show_account_status():
    """Show current account status"""
    
    db_path = os.path.join(APP_DIR, "data", "user_database.db")
    
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
    print("1. Unlock admin account")
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