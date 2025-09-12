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

# --- IMPORTANT ---
# Paste the path to the ONE Firefox profile you want to use here
FIREFOX_PROFILE_PATH = r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/fqqqrdxh.facebook-bot'

# Configure logging
logging.basicConfig(filename='reply_bot_logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Loads the configuration from config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config.json: {e}")
        sys.exit(1)

def setup_persistent_firefox_driver(profile_path):
    """Creates a Firefox driver session using a persistent user profile."""
    if not os.path.isdir(profile_path):
        print(f"!!! ERROR: FIREFOX PROFILE PATH NOT FOUND: {profile_path} !!!")
        return None
    print(f"Starting Firefox with profile: {os.path.basename(profile_path)}")
    options = FirefoxOptions()
    options.profile = profile_path
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1280, 800)
        return driver
    except Exception as e:
        print(f"FATAL: Failed to start Firefox driver: {e}")
        return None

# --- 2. CORE BOT ACTION ---

def sort_comments_by_newest(driver):
    """Finds the comment filter and sorts by 'Newest'."""
    try:
        print("Attempting to sort comments by 'Newest'...")
        filter_button_xpath = "//div[@role='button'][contains(., 'Most relevant')] | //span[text()='Most relevant']"
        filter_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, filter_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", filter_button)
        time.sleep(2)
        newest_option_xpath = "//div[@role='menuitem'][.//span[contains(text(), 'Newest')]] | //div[@role='menuitem'][.//span[contains(text(), 'All comments')]]"
        newest_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, newest_option_xpath)))
        driver.execute_script("arguments[0].click();", newest_option)
        print("   -> Selected 'Newest'. Waiting 10 seconds for comments to reload...")
        time.sleep(10)
    except Exception as e:
        print(f"   -> WARNING: Could not sort comments. Continuing with default order. (Error: {e})")

def scan_and_reply_all(driver, config):
    """Scans for all Thai comments on the post and replies to them."""
    post_url = config["post_url"]
    replies_list = config["replies"]
    thai_regex = re.compile(r'[\u0e00-\u0e7f]')

    print(f"Navigating to post. The goal is to reply to ALL Thai comments.")
    driver.get(post_url)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")))
        print("Post page loaded successfully.")
    except TimeoutException:
        print("ERROR: Failed to load the post page.")
        return

    sort_comments_by_newest(driver)
    
    # === CHANGE: Improved auto-scrolling method ===
    print("Loading all comments by scrolling...")
    body = driver.find_element(By.TAG_NAME, 'body')
    for i in range(30): # Scroll 30 times
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(random.uniform(1.5, 2.5))
        if (i + 1) % 5 == 0:
            print(f"  ...scrolled {i + 1} times.")

    print("Finished scrolling. Finding all comments to reply to...")
    comment_containers = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Comment by')] | //div[@aria-label='Comment']")
    
    print(f"Found {len(comment_containers)} potential comments.")
    replies_made = 0

    for container in comment_containers:
        try:
            username_element = container.find_element(By.XPATH, ".//a[contains(@href, 'facebook.com/') and @role='link']")
            username = username_element.text
            comment_text = container.find_element(By.XPATH, ".//div[@dir='auto']").text
            is_thai = bool(thai_regex.search(username)) or bool(thai_regex.search(comment_text))

            if is_thai:
                print(f"   -> Found Thai comment by '{username}'. Attempting to reply.")
                
                reply_button = container.find_element(By.XPATH, ".//div[@role='button' and contains(., 'Reply')]")
                driver.execute_script("arguments[0].click();", reply_button)
                time.sleep(random.uniform(1.5, 2.5))
                
                reply_box = driver.switch_to.active_element
                reply_text = random.choice(replies_list)
                
                pyperclip.copy(reply_text)
                paste_key = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL
                reply_box.send_keys(paste_key, 'v')
                time.sleep(random.uniform(1.0, 2.0))
                reply_box.send_keys(Keys.ENTER)
                
                replies_made += 1
                print(f"      -> Reply #{replies_made} posted.")
                logging.info(f"Successfully posted reply to '{username}'.")
                
                reply_delay = random.uniform(8, 12)
                print(f"      -> Waiting for {reply_delay:.0f} seconds...")
                time.sleep(reply_delay)

        except Exception as e:
            logging.warning(f"Could not reply to a comment. Error: {e}")
            continue
            
    print(f"Finished. Total replies made: {replies_made}")

# --- 3. MAIN EXECUTION SCRIPT ---

def main():
    config = load_config()
    
    print("\n" + "="*80)
    print(f"--- Starting Bot for Single Account ---")
    
    driver = setup_persistent_firefox_driver(FIREFOX_PROFILE_PATH)
    if not driver:
        print(f"Exiting due to driver setup failure.")
        sys.exit(1)

    try:
        driver.get("https://www.facebook.com")
        time.sleep(4)
        
        if "login" in driver.current_url:
            print(f"ERROR: The account in the specified profile is not logged in.")
            logging.warning(f"Session for profile {FIREFOX_PROFILE_PATH} is invalid.")
        else:
            print(f"Successfully started session.")
            scan_and_reply_all(driver, config)

    except Exception as e:
        logging.error(f"A critical error occurred: {e}")
        print(f"A critical error occurred. Check logs for details.")
    finally:
        if driver:
            driver.quit()
        print(f"Session finished. Browser is closed.")
    
    print("\n" + "="*80)
    print("Bot has completed its task.")

if __name__ == "__main__":
    main()
