import os
import sys
import time
import json
import logging
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from cryptography.fernet import Fernet, InvalidToken

# Setup logging
logging.basicConfig(
    filename='auto_comment_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
def load_config():
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        logging.error(f"Error loading config.json: {e}")
        sys.exit(1)

# Step 1: Load encryption key
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

# Step 2: Load and decrypt credentials
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

# Step 3: Setup Chrome driver
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

# Step 4: Login to Facebook
def login_to_facebook(driver, email, password, account_index, max_retries=3):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting login for account {account_index} ({email}), attempt {attempt + 1}")
            driver.get("https://www.facebook.com/login")
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            
            email_field = driver.find_element(By.ID, "email")
            password_field = driver.find_element(By.ID, "pass")
            login_button = driver.find_element(By.ID, "loginbutton")
            
            email_field.send_keys(email)
            password_field.send_keys(password)
            time.sleep(1 + (account_index % 3))
            login_button.click()
            time.sleep(10)  # Increased delay to stabilize session
            
            current_url = driver.current_url
            logging.info(f"After login, current URL: {current_url}")
            
            if "login" in current_url:
                error_message = "Unknown error"
                try:
                    error_element = driver.find_element(By.CLASS_NAME, "_9ay7")
                    error_message = error_element.text
                    logging.error(f"Login failed for account {account_index} ({email}): {error_message}")
                    return False
                except:
                    logging.error(f"Login failed for account {account_index} ({email}): {error_message}")
                    return False
            
            if "checkpoint" in current_url:
                logging.warning(f"Account {account_index} ({email}) requires two-factor authentication or captcha.")
                return False
            
            logging.info(f"Login successful for account {account_index} ({email})")
            return True
        
        except Exception as e:
            logging.error(f"Login error for account {account_index} ({email}), attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return False

# Step 5: Scan comments for Thai users
def scan_comments(driver, post_url):
    thai_regex = re.compile(r'[\u0E00-\u0E7F]')
    comments_data = []
    
    try:
        logging.info(f"Navigating to post: {post_url}")
        driver.get(post_url)
        time.sleep(15)  # Increased delay for page and comments to load
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']"))
            )
            logging.info(f"Post page loaded successfully: {post_url}")
        except:
            current_url = driver.current_url
            logging.error(f"Failed to load post page: {post_url}. Current URL: {current_url}")
            print(f"Error: Could not load post page ({post_url}). Current URL is {current_url}. Check permissions or network.")
            return []
        
        # Load all comments
        while True:
            try:
                more_comments = driver.find_element(By.XPATH, "//span[contains(text(), 'View more comments')]")
                more_comments.click()
                time.sleep(5)  # Increased delay for dynamic loading
            except:
                try:
                    more_comments = driver.find_element(By.XPATH, "//span[contains(text(), 'See more')]")
                    more_comments.click()
                    time.sleep(5)
                except:
                    logging.info("No more comments to load.")
                    break
        
        # Alternative selectors for comments
        comment_selectors = [
            "div[aria-label='Comment']",
            "div[data-testid='comment']",  # Common Facebook comment container
            "div[role='feed'] div[role='article']"  # Broader feed/article check
        ]
        
        for selector in comment_selectors:
            try:
                comment_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if comment_elements:
                    logging.info(f"Found {len(comment_elements)} comments with selector: {selector}")
                    break
            except:
                continue
        else:
            logging.warning("No comment elements found with any selector.")
            print("Warning: No comments found on the page. Check post accessibility or UI changes.")
            return []
        
        for index, comment in enumerate(comment_elements, 1):
            try:
                username_element = comment.find_element(By.CSS_SELECTOR, "a[href*='facebook.com']")
                username = username_element.text.strip()
                
                profile_name = username
                try:
                    profile_name_element = comment.find_element(By.CSS_SELECTOR, "span[class*='d2edcug0']")
                    profile_name = profile_name_element.text.strip()
                except:
                    pass
                
                is_thai = bool(thai_regex.search(username) or thai_regex.search(profile_name))
                
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
                logging.warning(f"Error processing comment {index} with selector {selector}: {e}")
                continue
        
        logging.info(f"Total Thai comments found: {len(comments_data)}")
        return comments_data
    
    except Exception as e:
        logging.error(f"Error scanning comments: {e}")
        return []

# Step 6: Post reply to a comment
def post_reply(driver, comment_id, reply_text, max_retries=3):
    for attempt in range(max_retries):
        try:
            reply_box_selector = f"div[data-testid='{comment_id}'] + div [aria-label='Write a reply...']"
            reply_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, reply_box_selector))
            )
            reply_box.click()
            time.sleep(1)
            
            reply_box.send_keys(reply_text)
            time.sleep(1 + random.uniform(0.5, 1.5))
            
            reply_box.send_keys(Keys.ENTER)
            time.sleep(2)
            
            logging.info(f"Successfully posted reply to comment {comment_id}: {reply_text}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to post reply to comment {comment_id}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return False

# Step 7: Verify posted replies
def verify_replies(driver, post_url, replies, account_email):
    try:
        logging.info(f"Verifying replies for account {account_email}")
        driver.get(post_url)
        time.sleep(5)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']"))
        )
        
        verified_replies = []
        for reply in replies:
            comment_id = reply["comment_id"]
            reply_text = reply["reply_text"]
            try:
                reply_selector = f"div[data-testid='{comment_id}'] + div [aria-label='Comment reply']"
                reply_elements = driver.find_elements(By.CSS_SELECTOR, reply_selector)
                for element in reply_elements:
                    if reply_text in element.text:
                        logging.info(f"Verified reply to comment {comment_id}: {reply_text}")
                        verified_replies.append(reply)
                        break
                else:
                    logging.warning(f"Reply not found for comment {comment_id}: {reply_text}")
            except Exception as e:
                logging.warning(f"Error verifying reply to comment {comment_id}: {e}")
        
        return verified_replies
    
    except Exception as e:
        logging.error(f"Error verifying replies: {e}")
        return []

# Main automation function
def auto_comment_reply():
    config = load_config()
    post_url = config["post_url"]
    replies_list = config["replies"]
    max_retries = config.get("max_retries", 3)
    min_delay = config.get("min_delay", 2)
    max_delay = config.get("max_delay", 5)
    
    # Validate URL
    url_pattern = re.compile(r'https?://(www\.)?facebook\.com/(story\.php\?story_fbid=\d+&id=\d+|.+/posts/.+)')
    if not url_pattern.match(post_url):
        print("Error: Invalid URL in config.json. Must match page post format (e.g., https://facebook.com/story.php?story_fbid=[id]&id=[page_id])")
        logging.error(f"Invalid URL in config: {post_url}")
        sys.exit(1)
    
    print("Starting automated comment reply tool...")
    credentials = load_credentials()
    if not credentials:
        logging.error("No credentials available.")
        sys.exit(1)
    
    driver = setup_chrome_driver(headless=False)  # Non-headless for debugging
    all_comments = []
    all_replies = []
    
    try:
        for index, cred in enumerate(credentials, 1):
            email = cred.get("email")
            password = cred.get("password")
            
            if login_to_facebook(driver, email, password, index, max_retries):
                print(f"Account {index} ({email}): Logged in successfully.")
                
                # Navigate to post URL after login
                logging.info(f"Navigating to {post_url} after login")
                driver.get(post_url)
                time.sleep(15)  # Increased delay to ensure navigation
                current_url = driver.current_url
                logging.info(f"Current URL after navigation: {current_url}")
                if "login" in current_url or "checkpoint" in current_url:
                    logging.error(f"Failed to navigate to {post_url}. Stuck at: {current_url}")
                    print(f"Error: Failed to navigate to {post_url}. Check account permissions or network.")
                    continue
                
                # Scan comments
                comments = scan_comments(driver, post_url)
                all_comments.append({"account": email, "comments": comments})
                print(f"Account {index} ({email}): Found {len(comments)} Thai comments.")
                
                # Post replies
                replied_comments = []
                for comment in comments:
                    if not comment.get("is_thai"):
                        continue
                    reply_text = random.choice(replies_list)
                    if post_reply(driver, comment["comment_id"], reply_text, max_retries):
                        replied_comments.append({
                            "comment_id": comment["comment_id"],
                            "username": comment["username"],
                            "profile_name": comment["profile_name"],
                            "reply_text": reply_text
                        })
                        print(f"Account {email}: Replied to {comment['profile_name']} ({comment['comment_id']}): {reply_text}")
                    time.sleep(random.uniform(min_delay, max_delay))
                
                # Verify replies
                verified_replies = verify_replies(driver, post_url, replied_comments, email)
                all_replies.append({"account": email, "replies": verified_replies})
                print(f"Account {index} ({email}): Verified {len(verified_replies)} of {len(replied_comments)} replies.")

            
            else:
                print(f"Account {index} ({email}): Login failed. Check auto_comment_logs.txt.")
            
            driver.delete_all_cookies()
            time.sleep(1)
        
        # Summarize results
        print(f"\nAutomation Summary:")
        total_comments = sum(len(acc["comments"]) for acc in all_comments)
        total_replies = sum(len(acc["replies"]) for acc in all_replies)
        print(f"Total accounts processed: {len(credentials)}")
        print(f"Total Thai comments found: {total_comments}")
        print(f"Total replies posted and verified: {total_replies}")
        for acc in all_replies:
            print(f"Account {acc['account']}: {len(acc['replies'])} verified replies")
            for reply in acc["replies"]:
                print(f"  Replied to {reply['profile_name']} ({reply['comment_id']}): {reply['reply_text']}")
    
    finally:
        driver.quit()
        print("Browser closed.")
        print("Automation process complete.")

if __name__ == "__main__":
    try:
        auto_comment_reply()
    except Exception as e:
        logging.error(f"Automation failed: {e}")
        print(f"Error: Automation failed. Check auto_comment_logs.txt for details.")
        sys.exit(1)