import bcrypt
import json
from pathlib import Path

def create_user_entry():
    # Get username and password
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    # Hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Create or load the auth store file
    auth_file = Path('data/auth_store.json')
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    
    if auth_file.exists():
        with auth_file.open('r') as f:
            data = json.load(f)
    else:
        data = {"users": {}}
    
    # Add the new user
    data["users"][username] = {
        "password_hash": hashed.decode('utf-8')
    }
    
    # Save the file
    with auth_file.open('w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nUser {username} created successfully!")
    print(f"Password hash: {hashed.decode('utf-8')}")

if __name__ == "__main__":
    create_user_entry()