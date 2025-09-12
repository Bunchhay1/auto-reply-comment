import os
import sys
import time
import json
import logging
import random
import re
import pyperclip
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 1. CONFIGURATION ---

# Your Firefox profile path
FIREFOX_PROFILE_PATH = r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/fqqqrdxh.facebook-bot'


# Configure logging
logging.basicConfig(filename='final_bot_logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Loads the configuration from config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config.json: {e}")
        logging.error(f"Error loading config.json: {e}")
        sys.exit(1)

def setup_persistent_firefox_driver(profile_path):
    """Creates a Firefox driver session using a persistent user profile."""
    if not os.path.isdir(profile_path):
        print("="*60)
        print("!!! ERROR: FIREFOX PROFILE PATH NOT FOUND !!!")
        print(f"The path you provided does not exist: {profile_path}")
        print("="*60)
        logging.error(f"Firefox profile path not found at: {profile_path}")
        return None

    print("Starting Firefox with your saved login session...")
    options = FirefoxOptions()
    options.profile = profile_path
    
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1280, 800)
        return driver
    except Exception as e:
        print(f"FATAL: Failed to start Firefox driver with the specified profile: {e}")
        logging.error(f"Failed to setup Firefox driver: {e}")
        return None

# --- 2. CORE BOT ACTION ---

def handle_popups(driver):
    """Attempts to find and close common cookie or login pop-ups."""
    try:
        cookie_button_selectors = [
            "//div[@aria-label='Allow all cookies']",
            "//button[contains(., 'Allow all')]",
            "//button[contains(., 'Accept all')]"
        ]
        for selector in cookie_button_selectors:
            try:
                button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, selector)))
                print("Cookie pop-up detected. Clicking to accept...")
                button.click()
                time.sleep(2)
                return
            except TimeoutException:
                continue
    except Exception as e:
        print(f"Could not handle pop-up: {e}")


def sort_comments_by_newest(driver):
    """Finds the comment filter and sorts by 'Newest'."""
    try:
        print("Attempting to sort comments by 'Newest'...")
        # This robust selector finds the filter button by looking for its text or a known icon
        filter_button_xpath = "//div[@role='button'][contains(., 'Most relevant')] | //span[text()='Most relevant']"
        
        # Wait up to 15 seconds for the filter button to be clickable
        filter_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, filter_button_xpath))
        )
        # Scroll the button into view to ensure it can be clicked
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_button)
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", filter_button)
        print("   -> Clicked the comment filter button.")
        time.sleep(2)

        # This robust selector finds the "Newest" option. Also looks for "All comments" as a fallback.
        newest_option_xpath = "//div[@role='menuitem'][.//span[contains(text(), 'Newest')]] | //div[@role='menuitem'][.//span[contains(text(), 'All comments')]]"
        
        newest_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, newest_option_xpath))
        )
        driver.execute_script("arguments[0].click();", newest_option)
        print("   -> Selected 'Newest'. Waiting 10 seconds for comments to reload...")
        time.sleep(10) # Increased wait time for comments to fully re-sort
        print("   -> Comment sorting complete. Proceeding to scan.")
    except Exception as e:
        print(f"   -> WARNING: Could not sort comments by 'Newest'. Continuing with default order. (Error: {e})")


def scan_and_reply(driver, config):
    """Scans for Thai comments on the target post and replies."""
    post_url = config["post_url"]
    replies_list = config["replies"]
    thai_regex = re.compile(r'[\u0e00-\u0e7f]')

    print(f"Navigating to the target post: {post_url}")
    driver.get(post_url)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")))
        print("Post page loaded successfully.")
    except TimeoutException:
        print("ERROR: Failed to load the post page.")
        logging.warning(f"Timeout loading post URL: {post_url}")
        return
    
    # Sort comments to 'Newest' before scrolling and replying
    sort_comments_by_newest(driver)

    for i in range(5): 
        print(f"Scrolling down to load newest comments... (Attempt {i+1}/5)")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3.0, 4.5))

    comment_selectors_to_try = [
        "//div[.//a/img[@alt] and .//div[@dir='auto']]",
        "//div[contains(@aria-label, 'Comment by')]",
        "//div[@aria-label='Comment']"
    ]
    
    comment_containers = []
    for selector in comment_selectors_to_try:
        try:
            print(f"Searching for comments using method: '{selector}'")
            comment_containers = driver.find_elements(By.XPATH, selector)
            if comment_containers:
                print(f"Success! Found {len(comment_containers)} potential comment containers.")
                break
        except Exception:
            print("Method failed. Trying the next one...")
            continue
    
    if not comment_containers:
        print("ERROR: Could not find any comments after trying all methods.")
        return

    replies_made = 0
    max_replies = 10

    for i, container in enumerate(comment_containers):
        if replies_made >= max_replies:
            print(f"Reply limit of {max_replies} reached for this session.")
            break

        try:
            username = ""
            comment_text = ""
            try:
                username_element = container.find_element(By.XPATH, ".//a[contains(@href, 'facebook.com/') and @role='link']")
                username = username_element.text
                comment_text_element = container.find_element(By.XPATH, ".//div[@dir='auto']")
                comment_text = comment_text_element.text
            except Exception:
                continue
            
            is_thai_user = bool(thai_regex.search(username))
            is_thai_comment = bool(thai_regex.search(comment_text))

            if is_thai_user or is_thai_comment:
                reason = "Thai username" if is_thai_user else "Thai comment text"
                print(f"Processing comment #{i+1} by '{username}'. Reason: {reason}. Attempting to reply.")
                
                reply_button = container.find_element(By.XPATH, ".//div[@role='button' and contains(., 'Reply')]")
                driver.execute_script("arguments[0].click();", reply_button)
                time.sleep(random.uniform(1.5, 2.5))
                
                reply_box = driver.switch_to.active_element
                reply_text = random.choice(replies_list)
                
                print("   -> Pasting full reply from clipboard...")
                pyperclip.copy(reply_text)
                
                paste_key = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL
                reply_box.send_keys(paste_key, 'v')
                
                print("   -> Pausing to ensure text is processed...")
                time.sleep(random.uniform(1.0, 2.0))
                
                reply_box.send_keys(Keys.ENTER)
                
                replies_made += 1
                print(f"   -> Reply #{replies_made} posted successfully.")
                logging.info(f"Successfully posted reply #{replies_made} to '{username}'.")
                time.sleep(random.uniform(4, 7))
            else:
                print(f"Skipping comment #{i+1} by '{username}' (Not Thai).")
                
        except Exception as e:
            logging.warning(f"Could not process a comment: {e}")
            continue
            
    print(f"Finished scan. Total replies made in this session: {replies_made}")

# --- 3. MAIN EXECUTION SCRIPT ---

def main():
    if 'PASTE_YOUR_FIREFOX_PROFILE_PATH_HERE' in FIREFOX_PROFILE_PATH:
        print("="*60)
        print("!!! CONFIGURATION NEEDED !!!")
        print("Please open 'chhay.py' and paste your Firefox profile path.")
        print("="*60)
        sys.exit(1)

    config = load_config()
    
    print("\n" + "="*60)
    print("Starting new automation session...")
    
    driver = setup_persistent_firefox_driver(FIREFOX_PROFILE_PATH)
    if not driver:
        sys.exit(1)

    try:
        driver.get("https://www.facebook.com")
        time.sleep(2)
        
        handle_popups(driver)

        logged_in_element_xpath = "//a[@aria-label='Home'] | //div[@role='feed'] | //a[@aria-label='Watch']"
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, logged_in_element_xpath)))
        print("Successfully started browser and confirmed you are logged in.")
        
        scan_and_reply(driver, config)

    except TimeoutException:
        print("ERROR: Could not confirm login. Please manually log in to Facebook using your 'facebook-bot' profile.")
    except Exception as e:
        logging.error(f"A critical error occurred: {e}")
        print(f"A critical error occurred. Check final_bot_logs.txt for details.")
    finally:
        driver.quit()
        print("Session finished. Browser is closed.")
    
    print("\nAutomation process complete.")

if __name__ == "__main__":
    main()