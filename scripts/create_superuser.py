# scripts/create_superuser.py

from sharesphere.auth import create_user
import getpass
import sys

def create_superuser():
    print("=== Create a Superuser ===")
    username = input("Enter admin username: ")
    password = getpass.getpass("Enter admin password: ")
    confirm_password = getpass.getpass("Confirm admin password: ")
    
    if password != confirm_password:
        print("❌ Passwords do not match. Please try again.")
        return
    
    user = create_user(username, password, is_admin=True)
    if user:
        print(f"✅ Superuser '{username}' created successfully.")
    else:
        print(f"❌ Superuser '{username}' already exists.")

if __name__ == "__main__":
    create_superuser()
