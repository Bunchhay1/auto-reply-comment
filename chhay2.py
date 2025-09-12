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

# List of all your Firefox profile paths
FIREFOX_PROFILE_PATHS = [
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/fqqqrdxh.facebook-bot',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/dytaciao.fb_account_1',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/jb46ve7w.fb_account_2',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/hibyib3f.fb_account_3',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/hzo15kws.fb_account_4',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/yu5xht6f.fb_account_5',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/esi1h3w4.fb_account_6',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/1nupfsvi.fb_account_7',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/ixhx2chl.fb_account_8',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/nyktgcfy.fb_account_10',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/t2fe4dhu.fb_account_11',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/vk3ph3b9.fb_account_12',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/r0yrnobw.fb_account_13',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/28ub8efj.fb_account_14',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/0g5y48yu.fb_account_15',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/ymqbjokf.fb_account_16',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/ozfq4shm.fb_account_17',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/mlr5m5lo.fb_account_18',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/qkbpkwpr.fb_account_19',
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/qbnbbioe.fb_account_20',
]

# Configure logging
logging.basicConfig(filename='final_bot_logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def scan_and_reply(driver, config, comments_to_skip):
    """Scans for new Thai users, skips a certain number, and replies to the next 10."""
    post_url = config["post_url"]
    replies_list = config["replies"]
    thai_regex = re.compile(r'[\u0e00-\u0e7f]')

    print(f"Navigating to post. This account will SKIP the first {comments_to_skip} users and reply to the next 10.")
    driver.get(post_url)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")))
        print("Post page loaded successfully.")
    except TimeoutException:
        print("ERROR: Failed to load the post page.")
        return 0

    sort_comments_by_newest(driver)
    
    found_thai_users = []
    found_usernames = set()
    
    required_users_to_find = comments_to_skip + 10
    
    scroll_attempts = 0
    max_scrolls = 10 # Increased safety limit for very long comment sections

    while len(found_usernames) < required_users_to_find and scroll_attempts < max_scrolls:
        scroll_attempts += 1
        print(f"Scrolling... (Attempt {scroll_attempts}/{max_scrolls}) | Found {len(found_usernames)}/{required_users_to_find} unique users")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # === CHANGE: Faster scrolling delay ===
        time.sleep(random.uniform(1.5, 2.5)) 

        comment_containers = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Comment by')] | //div[@aria-label='Comment']")
        for container in comment_containers:
            try:
                username_element = container.find_element(By.XPATH, ".//a[contains(@href, 'facebook.com/') and @role='link']")
                username = username_element.text
                
                if username in found_usernames:
                    continue

                comment_text = container.find_element(By.XPATH, ".//div[@dir='auto']").text
                is_thai = bool(thai_regex.search(username)) or bool(thai_regex.search(comment_text))

                if is_thai:
                    found_thai_users.append(container)
                    found_usernames.add(username)
            except Exception:
                continue
    
    if scroll_attempts == max_scrolls:
        print("Warning: Reached max scroll attempts. May not have found enough users to reply to.")

    print(f"Finished searching. Found a total of {len(found_thai_users)} unique Thai users.")

    users_to_reply_to = found_thai_users[comments_to_skip : comments_to_skip + 10]
    
    print(f"This account will now reply to {len(users_to_reply_to)} users.")
    replies_made = 0

    for container in users_to_reply_to:
        try:
            username = container.find_element(By.XPATH, ".//a[contains(@href, 'facebook.com/') and @role='link']").text
            print(f"   -> Replying to user: '{username}'")
            
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
            print(f"      -> Reply #{replies_made} for this account posted.")
            logging.info(f"Successfully posted reply to '{username}'.")
            
            reply_delay = random.uniform(8, 12)
            print(f"      -> Waiting for {reply_delay:.0f} seconds...")
            time.sleep(reply_delay)

        except Exception as e:
            logging.warning(f"Failed to reply to '{username}': {e}")
            continue
            
    print(f"Finished. Total replies made by this account: {replies_made}")
    return replies_made

# --- 3. MAIN EXECUTION SCRIPT ---

def main():
    config = load_config()
    
    while True: # Loop indefinitely
        comments_to_skip = 0
        print("\n" + "="*80)
        print("STARTING A NEW CYCLE. Comment counter reset to 0.")
        print("="*80)

        for i, profile_path in enumerate(FIREFOX_PROFILE_PATHS, 1):
            print("\n" + "="*80)
            print(f"--- Starting Bot for Account #{i} ---")
            
            driver = setup_persistent_firefox_driver(profile_path)
            if not driver:
                print(f"Skipping account #{i} due to driver setup failure.")
                time.sleep(3)
                continue

            try:
                driver.get("https://www.facebook.com")
                time.sleep(4)
                
                if "login" in driver.current_url:
                    print(f"ERROR: Account #{i} is not logged in.")
                    logging.warning(f"Session for profile {profile_path} is invalid.")
                else:
                    print(f"Successfully started session for Account #{i}.")
                    replies_made = scan_and_reply(driver, config, comments_to_skip)
                    comments_to_skip += replies_made

            except Exception as e:
                logging.error(f"A critical error occurred for account #{i}: {e}")
                print(f"A critical error occurred. Check logs for details.")
            finally:
                if driver:
                    driver.quit()
                print(f"Session for Account #{i} finished. Browser is closed.")
                
                delay = random.uniform(1, 3)
                print(f"Waiting for {delay:.1f} seconds before next account...")
                time.sleep(delay)
        
        print("\n" + "="*80)
        print("Completed a full loop through all accounts.")
        loop_delay = random.uniform(300, 600)
        print(f"Waiting for {loop_delay/60:.1f} minutes before starting the next cycle...")
        time.sleep(loop_delay)

if __name__ == "__main__":
    main()
