import os
import sys
import time
import json
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cryptography.fernet import Fernet, InvalidToken

# Setup logging
logging.basicConfig(
    filename='comment_scan_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Step 4.1: Load encryption key
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

# Step 4.2: Load and decrypt credentials
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

# Step 4.3: Setup Chrome driver
def setup_chrome_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to setup Chrome driver: {e}")
        sys.exit(1)

# Step 4.4: Login to Facebook
def login_to_facebook(driver, email, password, account_index):
    try:
        logging.info(f"Attempting login for account {account_index} ({email})")
        driver.get("https://www.facebook.com/login")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        
        email_field = driver.find_element(By.ID, "email")
        password_field = driver.find_element(By.ID, "pass")
        login_button = driver.find_element(By.ID, "loginbutton")
        
        email_field.send_keys(email)
        password_field.send_keys(password)
        time.sleep(1 + (account_index % 3))  # Fixed syntax error
        login_button.click()
        time.sleep(5)
        
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
        
        if "checkpoint" in driver.current_url:
            logging.warning(f"Account {account_index} ({email}) requires two-factor authentication or captcha.")
            return False
        
        logging.info(f"Login successful for account {account_index} ({email})")
        return True
    
    except Exception as e:
        logging.error(f"Login error for account {account_index} ({email}): {e}")
        return False

# Step 4.5: Scan comments for Thai users
def scan_comments(driver, post_url):
    thai_regex = re.compile(r'[\u0E00-\u0E7F]')
    comments_data = []
    
    try:
        logging.info(f"Navigating to post: {post_url}")
        driver.get(post_url)
        time.sleep(5)  # Increased for page posts
        
        # Check if page loaded successfully
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']"))
            )
        except:
            logging.error(f"Failed to load post page: {post_url}")
            print(f"Error: Could not load post page ({post_url}). Check URL, account permissions, or network.")
            return []
        
        # Click "View more comments" until no more are available
        while True:
            try:
                more_comments = driver.find_element(By.XPATH, "//span[contains(text(), 'View more comments')]")
                more_comments.click()
                time.sleep(3)
            except:
                logging.info("No more comments to load.")
                break
        
        # Find all comment elements
        comment_elements = driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Comment']")
        logging.info(f"Found {len(comment_elements)} comments.")
        
        for index, comment in enumerate(comment_elements, 1):
            try:
                # Extract username (often in a link)
                username_element = comment.find_element(By.CSS_SELECTOR, "a[href*='facebook.com']")
                username = username_element.text.strip()
                
                # Extract profile name (may be same as username or in a different element)
                profile_name = username  # Fallback to username
                try:
                    profile_name_element = comment.find_element(By.CSS_SELECTOR, "span[class*='d2edcug0']")
                    profile_name = profile_name_element.text.strip()
                except:
                    pass
                
                # Check for Thai script in username or profile name
                is_thai = bool(thai_regex.search(username) or thai_regex.search(profile_name))
                
                # Get comment ID (data-testid or fallback to index)
                comment_id = comment.get_attribute("data-testid") or f"comment_{index}"
                
                if is_thai:
                    comments_data.append({
                        "comment_id": comment_id,
                        "username": username,
                        "profile_name": profile_name,
                        "is_thai": True
                    })
                    logging.info(f"Comment {index}: Thai user detected (Username: {username}, Profile: {profile_name})")
                else:
                    logging.info(f"Comment {index}: Non-Thai user skipped (Username: {username}, Profile: {profile_name})")
            
            except Exception as e:
                logging.warning(f"Error processing comment {index}: {e}")
                continue
        
        return comments_data
    
    except Exception as e:
        logging.error(f"Error scanning comments: {e}")
        return []

# Main comment scanning function
def scan_comments_for_accounts(post_url):
    print("Starting comment scanning...")
    credentials = load_credentials()
    if not credentials:
        logging.error("No credentials available.")
        sys.exit(1)
    
    driver = setup_chrome_driver(headless=False)  # Non-headless for debugging
    all_comments = []
    
    try:
        for index, cred in enumerate(credentials, 1):
            email = cred.get("email")
            password = cred.get("password")
            
            if login_to_facebook(driver, email, password, index):
                print(f"Account {index} ({email}): Logged in successfully.")
                comments = scan_comments(driver, post_url)
                all_comments.append({
                    "account": email,
                    "comments": comments
                })
                print(f"Account {index} ({email}): Found {len(comments)} comments from Thai users.")
            else:
                print(f"Account {index} ({email}): Login failed. Check comment_scan_logs.txt.")
            
            driver.delete_all_cookies()
            time.sleep(1)
        
        # Summarize results
        print(f"\nComment Scanning Summary:")
        total_thai_comments = sum(len(acc["comments"]) for acc in all_comments)
        print(f"Total accounts processed: {len(credentials)}")
        print(f"Total Thai comments found: {total_thai_comments}")
        for acc in all_comments:
            print(f"Account {acc['account']}: {len(acc['comments'])} Thai comments")
        
        return all_comments
    
    finally:
        driver.quit()
        print("Browser closed.")

# Test comment scanning
if __name__ == "__main__":
    try:
        # Input and validate Facebook post URL
        post_url = input("Enter the Facebook page post URL to scan: ").strip()
        if not (post_url.startswith("https://www.facebook.com") or post_url.startswith("https://facebook.com")):
            print("Error: Invalid Facebook post URL. It must start with https://www.facebook.com or https://facebook.com")
            logging.error(f"Invalid URL entered: {post_url}")
            sys.exit(1)
        
        # Basic URL format check for page posts
        url_pattern = re.compile(r'https?://(www\.)?facebook\.com/.+/posts/.+')
        if not url_pattern.match(post_url):
            print("Error: URL does not match expected page post format (e.g., https://www.facebook.com/[page]/posts/[post_id])")
            logging.error(f"URL format invalid: {post_url}")
            sys.exit(1)
        
        comments_data = scan_comments_for_accounts(post_url)
        print("Comment scanning complete. Ready for reply automation.")
    except Exception as e:
        logging.error(f"Comment scanning failed: {e}")
        print(f"Error: Comment scanning failed. Check comment_scan_logs.txt for details.")
        sys.exit(1)