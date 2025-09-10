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
    filename='reply_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Predefined list of generic Thai replies
THAI_REPLIES = [
       " ប្រទេសថៃគឺជាប្រទេសដែលបានមកពីប្រទេសកម្ពុជាទាំងអស់វប្បធម៌អរិយធម៌ទឹកដីប្រាសាទភាសាសុទ្ធតែបានចេញពីខ្មែរទាំងអស់។សូម្បីតែប្រជាជនលោកនៅថៃក៏ជាប្រជាជនក៏ចេញពីប្រទេសកម្ពុជាដែរ។អញ្ចឹងពូលោកឯងគឺជាចោរCopyគេ។ประเทศไทยเป็นประเทศที่มาจากกัมพูชา วัฒนธรรม อารยธรรม ดินแดน วัดวาอาราม และภาษาต่างๆ ล้วนมาจากเขมร แม้แต่คนในประเทศไทยก็เป็นคนกัมพูชาเช่นกัน ดังนั้นคุณก็คือพวกเลียนแบบนั่นเอง"
       "ខំរៀបចំក្បួនយុទ្ធសាស្ត្រចង់បានទឹកដីកម្ពុជានៅពេលដែលរាជរដ្ឋាភិបាលកម្ពុជាព្រឹត្តិកម្មតុលាការអន្តរជាតិលែងហ៊ានធ្វើរឿងលួចទឹកដីគេទៀត។ពួកលោកឯងហ្នឹងក៏ជាចោរសម្បើមម៉្លេះ។  พยายามคิดกลยุทธ์ยึดครองดินแดนกัมพูชา แต่รัฐบาลกัมพูชาไม่กล้าขโมยดินแดนกัมพูชาต่อหน้าศาลระหว่างประเทศ พวกคุณก็เป็นโจรใหญ่เหมือนกัน"
       "បើបុព្វបុរសជាចោរអញ្ចឹងក្រុមពួកថៃលោកឯងក៏ជាចោរដែរ។អញ្ចឹងបានចេញមកសន្ដានតែមួយ។សុទ្ធតែពួកចង់បានដីអ្នកដទៃគ្មានចេះធ្វើអីដើម្បីអភិវឌ្ឍន៍ខ្លួនឯងសោះ។ ถ้าบรรพบุรุษเป็นโจร คนไทยเองก็เป็นโจรเหมือนกัน เลยออกมาแบบเดียวกัน คืออยากได้ที่ดินของคนอื่น ไม่รู้จักพัฒนาตัวเอง"
       "ប្រទេសថៃរាជរដ្ឋាភិបាលថៃរីកចម្រើនដោយសារតែលួចរបស់អ្នកដទៃនិយាយទៅតាំងប្រជាជនថៃហើយនិងរាជរដ្ឋាភិបាលថៃទៅចង់បានរបស់គេទាំងអស់។មិនថាប្រទេសជិតខាងទេ។គឺថៃលួចទាំងអស់ដូច្នេះប្រទេសថៃគឺជាចោរ ประชาชนชาวไทยกล่าวว่าประเทศไทยเจริญรุ่งเรืองเพราะขโมยของจากผู้อื่น และรัฐบาลไทยต้องการทุกอย่างเพื่อตัวเอง ไม่ว่าประเทศเพื่อนบ้านจะเป็นอย่างไรก็ตาม ประเทศไทยขโมยทุกอย่าง ดังนั้นประเทศไทยจึงเป็นหัวขโมย"
       "ប្រទេសថៃគ្មានអ្វីជារបស់ខ្លួនឯងទេ។បានតែលួចរបស់អ្នកដទៃជាពិសេសទឹកដី។ដែលលួចពីប្រទេសកម្ពុជា។ ประเทศไทยไม่มีอะไรเป็นของตัวเอง มีแต่ขโมยของคนอื่น โดยเฉพาะที่ดินที่ขโมยมาจากกัมพูชา"
       "ប្រទេសថៃគ្មានអ្វីជារបស់ខ្លួនឯងទេ។បានតែលួចរបស់អ្នកដទៃជាពិសេសទឹកដី។ដែលលួចពីប្រទេសកម្ពុជា។ ประเทศไทยไม่มีอะไรเป็นของตัวเอง มีแต่ขโมยของคนอื่น โดยเฉพาะที่ดินที่ขโมยมาจากกัมพูชา"
       "ពួកអាសៀមពួកចង្រៃលួចតែទឹកដីខ្មែរ พวกเอเชียไอ้สารเลวพวกนี้ขโมยแต่ดินแดนของกัมพูชาเท่านั้น"
       "កម្ពុជា​សព្វ​ថ្ងៃ​ចង់​បាន​តែ​សន្តិភាព និង​សុភមង្គល។ យើង​មិន​ដែល​ចង់​បំពាន​នរណា​ម្នាក់​ឡើយ។ បើ​គេ​បំពាន​យើង​មុន យើង​ត្រូវ​ការពារ​គេ។ กัมพูชาในปัจจุบันต้องการเพียงสันติภาพและความสุข เราไม่เคยต้องการละเมิดใคร หากพวกเขาละเมิดเราก่อน เราก็ต้องปกป้องพวกเขา"
       "បើ​ថៃ​មាន​ទំនុក​ចិត្ត​ថា​ខ្លួន​ឯង​ធ្វើ​ត្រឹម​ត្រូវ កុំ​ខ្លាច​កម្ពុជា​យក​បញ្ហា​ព្រំដែន​ទៅ​តុលាការ​យុត្តិធម៌​អន្តរជាតិ។ หากประเทศไทยมั่นใจว่าคุณกำลังทำสิ่งที่ถูกต้อง ไม่ต้องกลัวว่ากัมพูชาจะนำเรื่องชายแดนไปขึ้นศาลยุติธรรมระหว่างประเทศ"
       "មានថៃវាចង្រៃ 7 សន្ដានឃើញរបស់គេមិនបានចង់លួចឡើងញ័រខ្លួនតែកាត់តែតាត់ម៉េចរបស់គេហ្នឹងក៏មានតម្លៃដែរកុំចង់លុយរបស់គេពេកវារកអ្វីជាខ្លួនឯងផង។កុំបានឃើញរបស់គេល្អមិនបានអីញ័រខ្លួនចង់បានណាស់ มีคนไทย 7 คน ขี้งกมาก เห็นแล้วไม่อยากขโมย แค่ส่ายหัว ตัดทิ้ง ก็มีคุณค่า ไม่ต้องการเงินของตัวเองมาก หาอะไรให้ตัวเอง ไม่เห็นของดี ส่ายหัว อยากได้จริงๆ"
       "កម្ពុជា​នៅ​តែ​ប្រកាន់​ជំហរ​រឹងប៉ឹង​ក្នុង​ការ​យក​បញ្ហា​ព្រំដែន​ទៅ​តុលាការ​យុត្តិធម៌​អន្តរជាតិ បើ​ទោះ​ជា​ថៃ​បដិសេធ​ក៏​ដោយ។ กัมพูชายังคงยืนหยัดจุดยืนในการนำเรื่องพรมแดนเข้าสู่ศาลยุติธรรมระหว่างประเทศ แม้ว่าไทยจะปฏิเสธก็ตาม"
]

# Step 5.1: Load encryption key
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

# Step 5.2: Load and decrypt credentials
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

# Step 5.3: Setup Chrome driver
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

# Step 5.4: Login to Facebook
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
        time.sleep(1 + (account_index % 3))
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

# Step 5.5: Post reply to a comment
def post_reply(driver, comment_id, reply_text):
    try:
        # Find the comment reply box
        reply_box_selector = f"div[data-testid='{comment_id}'] + div [aria-label='Write a reply...']"
        reply_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, reply_box_selector))
        )
        reply_box.click()
        time.sleep(1)
        
        # Type the reply
        reply_box.send_keys(reply_text)
        time.sleep(1 + random.uniform(0.5, 1.5))  # Random delay
        
        # Submit the reply
        reply_box.send_keys(Keys.ENTER)
        time.sleep(2)
        
        logging.info(f"Successfully posted reply to comment {comment_id}: {reply_text}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to post reply to comment {comment_id}: {e}")
        return False

# Step 5.6: Automate replies to Thai comments
def automate_replies(driver, post_url, comments, account_email):
    replied_comments = []
    
    try:
        logging.info(f"Navigating to post: {post_url}")
        driver.get(post_url)
        time.sleep(5)
        
        # Check if page loaded successfully
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']"))
            )
        except:
            logging.error(f"Failed to load post page: {post_url}")
            print(f"Error: Could not load post page ({post_url}).")
            return []
        
        for comment in comments:
            if not comment.get("is_thai"):
                logging.info(f"Skipping non-Thai comment {comment['comment_id']}")
                continue
            
            reply_text = random.choice(THAI_REPLIES)
            if post_reply(driver, comment["comment_id"], reply_text):
                replied_comments.append({
                    "comment_id": comment["comment_id"],
                    "username": comment["username"],
                    "profile_name": comment["profile_name"],
                    "reply_text": reply_text
                })
                print(f"Account {account_email}: Replied to comment {comment['comment_id']} by {comment['profile_name']}: {reply_text}")
            else:
                print(f"Account {account_email}: Failed to reply to comment {comment['comment_id']} by {comment['profile_name']}")
            
            time.sleep(random.uniform(2, 5))  # Random delay between replies
        
        return replied_comments
    
    except Exception as e:
        logging.error(f"Error automating replies: {e}")
        return []

# Main reply automation function
def automate_replies_for_accounts(post_url, comments_data):
    print("Starting reply automation...")
    credentials = load_credentials()
    if not credentials:
        logging.error("No credentials available.")
        sys.exit(1)
    
    driver = setup_chrome_driver(headless=False)  # Non-headless for debugging
    all_replies = []
    
    try:
        for index, cred in enumerate(credentials, 1):
            email = cred.get("email")
            password = cred.get("password")
            
            if login_to_facebook(driver, email, password, index):
                print(f"Account {index} ({email}): Logged in successfully.")
                # Find comments associated with this account or use all comments
                account_comments = next((acc["comments"] for acc in comments_data if acc["account"] == email), [])
                if not account_comments:
                    logging.warning(f"No comments found for account {email}. Skipping.")
                    print(f"Account {index} ({email}): No Thai comments to reply to.")
                    continue
                
                replies = automate_replies(driver, post_url, account_comments, email)
                all_replies.append({
                    "account": email,
                    "replies": replies
                })
                print(f"Account {index} ({email}): Posted {len(replies)} replies.")
            else:
                print(f"Account {index} ({email}): Login failed. Check reply_logs.txt.")
            
            driver.delete_all_cookies()
            time.sleep(1)
        
        # Summarize results
        print(f"\nReply Automation Summary:")
        total_replies = sum(len(acc["replies"]) for acc in all_replies)
        print(f"Total accounts processed: {len(credentials)}")
        print(f"Total replies posted: {total_replies}")
        for acc in all_replies:
            print(f"Account {acc['account']}: {len(acc['replies'])} replies")
            for reply in acc["replies"]:
                print(f"  Replied to {reply['profile_name']} ({reply['comment_id']}): {reply['reply_text']}")
        
        return all_replies
    
    finally:
        driver.quit()
        print("Browser closed.")

# Test reply automation
if __name__ == "__main__":
    try:
        # Input and validate Facebook post URL
        post_url = input("Enter the Facebook page post URL to scan: ").strip()
        if not (post_url.startswith("https://www.facebook.com") or post_url.startswith("https://facebook.com")):
            print("Error: Invalid Facebook post URL. It must start with https://www.facebook.com or https://facebook.com")
            logging.error(f"Invalid URL entered: {post_url}")
            sys.exit(1)
        
        # Validate URL for page posts (including story.php format)
        url_pattern = re.compile(r'https?://(www\.)?facebook\.com/(story\.php\?story_fbid=\d+&id=\d+|.+/posts/.+)')
        if not url_pattern.match(post_url):
            print("Error: URL does not match expected page post format (e.g., https://www.facebook.com/[page]/posts/[post_id] or https://facebook.com/story.php?story_fbid=[id]&id=[page_id])")
            logging.error(f"URL format invalid: {post_url}")
            sys.exit(1)
        
        # Load comments data (for simplicity, re-run comment scanning or load from previous run)
        from comment_scanning import scan_comments_for_accounts
        comments_data = scan_comments_for_accounts(post_url)
        
        if not comments_data:
            print("Error: No Thai comments found to reply to.")
            sys.exit(1)
        
        replies_data = automate_replies_for_accounts(post_url, comments_data)
        print("Reply automation complete. Automation process finished.")
    except Exception as e:
        logging.error(f"Reply automation failed: {e}")
        print(f"Error: Reply automation failed. Check reply_logs.txt for details.")
        sys.exit(1)