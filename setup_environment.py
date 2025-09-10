import os
import json
import subprocess
import sys
import getpass

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Error: 'cryptography' module not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        from cryptography.fernet import Fernet
        print("'cryptography' installed successfully.")
    except Exception as e:
        print(f"Failed to install 'cryptography': {e}")
        print("Please install it manually with: python3 -m pip install cryptography")
        sys.exit(1)

# Step 1: Generate encryption key for securing credentials
def generate_encryption_key():
    key = Fernet.generate_key()
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)
    return key

# Step 2: Load encryption key
def load_encryption_key():
    if not os.path.exists("encryption_key.key"):
        return generate_encryption_key()
    with open("encryption_key.key", "rb") as key_file:
        return key_file.read()

# Step 3: Create or update credentials file
def setup_credentials():
    fernet = Fernet(load_encryption_key())
    credentials = []

    # Prompt user to input up to 20 account credentials
    print("Enter Facebook account credentials (email/phone and password). Enter blank email to stop.")
    while len(credentials) < 20:
        email = input(f"Enter email/phone for account {len(credentials) + 1} (or leave blank to finish): ").strip()
        if not email:
            break
        password = getpass.getpass(f"Enter password for account {len(credentials) + 1}: ").strip()
        credentials.append({"email": email, "password": password})

    # Encrypt and save credentials
    try:
        encrypted_credentials = fernet.encrypt(json.dumps(credentials).encode())
        with open("fb_credentials.enc", "wb") as enc_file:
            enc_file.write(encrypted_credentials)
        print(f"Saved {len(credentials)} account credentials securely.")
    except Exception as e:
        print(f"Error saving credentials: {e}")
        sys.exit(1)

# Step 4: Install required dependencies
def install_dependencies():
    print("Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "cryptography"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Please install manually with: python3 -m pip install selenium cryptography")
        sys.exit(1)

# Step 5: Verify Chrome installation
def verify_chrome():
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome_path):
        print("Google Chrome is installed.")
    else:
        print("Google Chrome not found. Please install it from https://www.google.com/chrome/")
        sys.exit(1)

# Main setup function
def main():
    print("Setting up environment for Automated Facebook Comment Reply Tool...")
    verify_chrome()
    install_dependencies()
    setup_credentials()
    print("Environment setup complete. Ready to proceed to next steps.")

if __name__ == "__main__":
    main()