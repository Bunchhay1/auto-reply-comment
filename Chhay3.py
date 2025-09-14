import os
import sys
import time
import json
import logging
import random
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 1. CONFIGURATION ---

# --- IMPORTANT ---
# List of all Firefox profiles you want to use.
# Make sure these paths are correct for your system.
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
    r'/Users/bunchhay/Library/Application Support/Firefox/Profiles/nyktgcfy.fb_account_10', # NOTE: You are missing account 9
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

# --- IMPORTANT ---
# List of 10 links to share on Facebook.
LINKS_TO_SHARE = [
    "https://facebook.com/story.php?story_fbid=1069315942062112&id=100069511484329&mibextid=wwXIfr&rdid=RWnAo7qIKtj33BTh",
    "https://facebook.com/story.php?story_fbid=1065633622430344&id=100069511484329&mibextid=wwXIfr&rdid=Lq5Wn50Qy0fkIEFh",
    "https://facebook.com/story.php?story_fbid=1065705735756466&id=100069511484329&mibextid=wwXIfr&rdid=DnBg40nSTQpBEc03",
    "https://facebook.com/story.php?story_fbid=1065860025741037&id=100069511484329&mibextid=wwXIfr&rdid=tMrHdM4D4F6qR29T",
    "https://facebook.com/story.php?story_fbid=1066609772332729&id=100069511484329&mibextid=wwXIfr&rdid=NP69Z73Spi7GA3PF",
    "https://facebook.com/story.php?story_fbid=1067654108894962&id=100069511484329&mibextid=wwXIfr&rdid=TeDQ7Wpok2tXA5gS",
    "https://facebook.com/story.php?story_fbid=1067929965534043&id=100069511484329&mibextid=wwXIfr&rdid=reEn3hNFT5LPGtbc",
    "https://facebook.com/100069511484329/posts/1068319325495107/?mibextid=wwXIfr&rdid=GA3P12laFaxS2ziH",
    "https://facebook.com/story.php?story_fbid=1068872435439796&id=100069511484329&mibextid=wwXIfr&rdid=TCPPlrv3nVovu3C6",
    "https://facebook.com/story.php?story_fbid=1069083242085382&id=100069511484329&mibextid=wwXIfr&rdid=EQVREWNZScdsIXK3",
]


# Configure logging
logging.basicConfig(filename='chhay3_share_logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_persistent_firefox_driver(profile_path):
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

def extract_post_id(url):
    """Extracts the unique post ID from a Facebook URL."""
    match = re.search(r'story_fbid=([0-9]+)|/posts/([0-9]+)', url)
    if match:
        return match.group(1) or match.group(2)
    return None

def share_specific_post(driver, post_url, times_to_share):
    print(f"  -> Locating and sharing post: {post_url}")
    post_id = extract_post_id(post_url)
    if not post_id:
        print(f"     -> ERROR: Could not find a valid ID in URL: {post_url}")
        return

    for i in range(times_to_share):
        try:
            print(f"     -> Share {i+1}/{times_to_share}")
            # Go to the profile page to find the post
            driver.get("https://www.facebook.com/me")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(@href, '/profile.php?id=')] | //*[contains(@href, '/about')]"))) # Wait for profile to load
            
            # Scroll down to find the post
            post_container = None
            for _ in range(10): # Scroll up to 10 times
                try:
                    # Find the specific post container by looking for a link that contains the post ID
                    post_link_xpath = f"//a[contains(@href, '{post_id}')]"
                    post_link = driver.find_element(By.XPATH, post_link_xpath)
                    # The container is usually a few levels up from the link
                    post_container = post_link.find_element(By.XPATH, "./ancestor::div[@data-pagelet]")
                    if post_container:
                        print("        -> Found the specific post on the profile.")
                        break
                except NoSuchElementException:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    time.sleep(2)

            if not post_container:
                raise NoSuchElementException(f"Could not find post with ID {post_id} on the profile page.")
            
            # Scroll to the post and find its share button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_container)
            time.sleep(1)

            share_button_xpath = ".//div[@aria-label='Share']" # Look for the share button *within* the post container
            share_button = post_container.find_element(By.XPATH, share_button_xpath)

            driver.execute_script("arguments[0].click();", share_button)
            print("        -> Clicked 'Share' button.")
            time.sleep(random.uniform(2, 4))
            
            share_now_xpath = "//span[contains(text(),'Share now')]"
            share_now_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, share_now_xpath))
            )
            share_now_button.click()
            print("        -> Clicked 'Share now'.")
            logging.info(f"Successfully shared {post_url} (Attempt {i+1}/{times_to_share})")
            time.sleep(random.uniform(10, 15)) # Longer wait after a successful share

        except Exception as e:
            print(f"     -> ERROR: Could not complete share action. See logs.")
            logging.error(f"Failed to share post {post_url} on attempt {i+1}. Error: {e}")
            driver.save_screenshot(f"error_screenshot_{time.strftime('%Y%m%d-%H%M%S')}.png")
            time.sleep(5)
            continue

def main():
    total_profiles = len(FIREFOX_PROFILE_PATHS)
    for index, profile_path in enumerate(FIREFOX_PROFILE_PATHS):
        print("\n" + "="*80)
        print(f"--- Starting Bot for Profile {index + 1}/{total_profiles} ---")
        print(f"--- Profile Path: {profile_path} ---")
        
        driver = setup_persistent_firefox_driver(profile_path)
        if not driver:
            continue

        try:
            driver.get("https://www.facebook.com")
            time.sleep(4)
            
            if "login" in driver.current_url:
                print(f"ERROR: Account in profile '{os.path.basename(profile_path)}' is not logged in.")
                logging.warning(f"Session for profile {profile_path} is invalid.")
            else:
                print(f"Successfully started session for '{os.path.basename(profile_path)}'.")
                for link_to_share in LINKS_TO_SHARE:
                    share_specific_post(driver, link_to_share, 5)

        except Exception as e:
            print(f"A critical error occurred for profile {profile_path}. Check logs.")
            logging.error(f"Critical error for profile {profile_path}: {e}")
        finally:
            if driver:
                driver.quit()
            print(f"Session for '{os.path.basename(profile_path)}' finished.")
        
        if index < total_profiles - 1:
            delay = random.uniform(20, 40)
            print(f"\n--- WAITING for {delay:.0f} seconds before starting next profile... ---")
            time.sleep(delay)
    
    print("\n" + "="*80)
    print("Bot has completed its tasks for ALL profiles.")

if __name__ == "__main__":
    main()
