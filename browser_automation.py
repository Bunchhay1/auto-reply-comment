import os
import sys
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cryptography.fernet import Fernet, InvalidToken

# Setup logging
logging.basicConfig(
    filename='login_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Step 3.1: Load encryption key
def load_encryption_key():
    try:
        if not os.path.exists("encryption_key.key"):
            logging.error("Encryption key file not found.")
            sys.exit(1)
        with open("encryption_key.key", "rb") as key_file:
            return key_file.read()
    except Exception as e:
        logging.error(f"Error loading encryption key: {e}")
        sys.exit(1)

# Step 3.2: Load and decrypt credentials
def load_credentials():
    try:
        fernet = Fernet(load_encryption_key())
        if not os.path.exists("fb_credentials.enc"):
            logging.error("Credentials file not found.")
            sys.exit(1)
        with open("fb_credentials.enc", "rb") as enc_file:
            encrypted_data = enc_file.read()
        decrypted_data = fernet.decrypt(encrypted_data)
        credentials = json.loads(decrypted_data.decode())
        return credentials
    except InvalidToken:
        logging.error("Invalid encryption key or corrupted credentials file.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading credentials: {e}")
        sys.exit(1)

# Step 3.3: Setup Chrome driver
def setup_chrome_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Assumes chromedriver is in PATH (installed via brew install chromedriver)
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to setup Chrome driver: {e}")
        sys.exit(1)

# Step 3.4: Automate Facebook login
def login_to_facebook(driver, email, password, account_index):
    try:
        logging.info(f"Attempting login for account {account_index} ({email})")
        driver.get("https://www.facebook.com/login")
        
        # Wait for login form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        
        # Enter credentials
        email_field = driver.find_element(By.ID, "email")
        password_field = driver.find_element(By.ID, "pass")
        login_button = driver.find_element(By.ID, "loginbutton")
        
        email_field.send_keys(email)
        password_field.send_keys(password)
        
        # Random delay to mimic human behavior
        time.sleep(1 + (account_index % 3))  # 1-3 seconds
        login_button.click()
        
        # Wait for potential redirect or error
        time.sleep(3)
        
        # Check for login errors (e.g., wrong password)
        if "login" in driver.current_url:
            error_message = "Unknown error"
            try:
                error_element = driver.find_element(By.CLASS_NAME, "_9ay7")
                error_message = error_element.text
                logging.error(f"Login failed for account {account_index} ({email}): {error_message}")
                return False
            except:
                logging.error(f"Login failed for account {account_index} ({email}): {error_message}")
                return False
        
        # Check for two-factor authentication or captcha
        if "checkpoint" in driver.current_url:
            logging.warning(f"Account {account_index} ({email}) requires two-factor authentication or captcha. Manual intervention needed.")
            return False
        
        logging.info(f"Login successful for account {account_index} ({email})")
        return True
    
    except Exception as e:
        logging.error(f"Login error for account {account_index} ({email}): {e}")
        return False

# Main browser automation function
def automate_login():
    print("Starting browser automation for login...")
    credentials = load_credentials()
    if not credentials:
        logging.error("No credentials available for login.")
        sys.exit(1)
    
    successful_logins = []
    driver = setup_chrome_driver(headless=True)  # Set headless=False for debugging
    
    try:
        for index, cred in enumerate(credentials, 1):
            email = cred.get("email")
            password = cred.get("password")
            
            if login_to_facebook(driver, email, password, index):
                successful_logins.append({"email": email, "password": password})
            else:
                print(f"Account {index} ({email}): Login failed. Check login_logs.txt for details.")
            
            # Clear cookies to ensure clean state for next login
            driver.delete_all_cookies()
            time.sleep(1)
        
        print(f"\nLogin Summary:")
        print(f"Total accounts attempted: {len(credentials)}")
        print(f"Successful logins: {len(successful_logins)}")
        for i, account in enumerate(successful_logins, 1):
            print(f"Account {i}: {account['email']} - Login successful")
        
        if not successful_logins:
            print("Error: No successful logins. Check login_logs.txt for details.")
            sys.exit(1)
        
        return successful_logins
    
    finally:
        driver.quit()
        print("Browser closed.")

# Test browser automation
if __name__ == "__main__":
    try:
        automate_login()
        print("Browser automation complete. Ready for comment scanning.")
    except Exception as e:
        logging.error(f"Browser automation failed: {e}")
        print(f"Error: Browser automation failed. Check login_logs.txt for details.")
        sys.exit(1)