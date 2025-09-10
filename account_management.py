import json
import os
import sys
from cryptography.fernet import Fernet, InvalidToken
import re

# Step 2.1: Load encryption key
def load_encryption_key():
    try:
        if not os.path.exists("encryption_key.key"):
            print("Error: encryption_key.key not found. Please run setup_environment.py first.")
            sys.exit(1)
        with open("encryption_key.key", "rb") as key_file:
            return key_file.read()
    except Exception as e:
        print(f"Error loading encryption key: {e}")
        sys.exit(1)

# Step 2.2: Load and decrypt credentials
def load_credentials():
    try:
        fernet = Fernet(load_encryption_key())
        if not os.path.exists("fb_credentials.enc"):
            print("Error: fb_credentials.enc not found. Please run setup_environment.py first.")
            sys.exit(1)
        with open("fb_credentials.enc", "rb") as enc_file:
            encrypted_data = enc_file.read()
        decrypted_data = fernet.decrypt(encrypted_data)
        credentials = json.loads(decrypted_data.decode())
        return credentials
    except InvalidToken:
        print("Error: Invalid encryption key or corrupted credentials file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        sys.exit(1)

# Step 2.3: Validate credentials
def validate_credentials(credentials):
    valid_credentials = []
    email_phone_regex = re.compile(r"^(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[0-9]{10})$")
    
    for index, cred in enumerate(credentials, 1):
        email = cred.get("email", "")
        password = cred.get("password", "")
        
        # Check if email/phone and password are present
        if not email or not password:
            print(f"Account {index}: Missing email/phone or password. Skipping.")
            continue
        
        # Validate email (basic email format) or phone (10 digits for Thai numbers)
        if not email_phone_regex.match(email):
            print(f"Account {index}: Invalid email/phone format ({email}). Skipping.")
            continue
        
        # Basic password length check (Facebook requires at least 6 characters)
        if len(password) < 6:
            print(f"Account {index}: Password too short for {email}. Skipping.")
            continue
        
        valid_credentials.append({"email": email, "password": password})
        print(f"Account {index}: Valid credentials for {email}.")
    
    if not valid_credentials:
        print("Error: No valid credentials found.")
        sys.exit(1)
    
    return valid_credentials

# Main account management function
def manage_accounts():
    print("Starting account management...")
    credentials = load_credentials()
    print(f"Loaded {len(credentials)} account(s) from encrypted storage.")
    
    valid_credentials = validate_credentials(credentials)
    print(f"Validated {len(valid_credentials)} account(s) ready for use.")
    
    # Save validated credentials back to encrypted file (optional, for consistency)
    try:
        fernet = Fernet(load_encryption_key())
        encrypted_credentials = fernet.encrypt(json.dumps(valid_credentials).encode())
        with open("fb_credentials.enc", "wb") as enc_file:
            enc_file.write(encrypted_credentials)
        print("Updated encrypted credentials file with validated accounts.")
    except Exception as e:
        print(f"Warning: Failed to update credentials file: {e}")
    
    return valid_credentials

# Test the account management
if __name__ == "__main__":
    try:
        accounts = manage_accounts()
        print("\nAccount Management Summary:")
        for i, account in enumerate(accounts, 1):
            print(f"Account {i}: {account['email']}")
        print("\nAccount management complete. Ready to proceed to browser automation.")
    except Exception as e:
        print(f"Account management failed: {e}")
        sys.exit(1)