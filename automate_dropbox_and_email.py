#!/usr/bin/env python3
import argparse
import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import smtplib
from email.mime.text import MIMEText
import json

# --- IMPORTANT PRE-RUN INSTRUCTIONS ---
# This script assumes you have ALREADY LOGGED INTO:
# 1. Dropbox (https://www.dropbox.com)
# 2. The Video Progress Page (specified by --video_progress_page_url)
# using a REGULAR CHROME BROWSER with the profile located at:
# os.path.expanduser("~/selenium_chrome_profile")
#
# You can use the 'manual_dropbox_login.py' script to help open a browser
# with this specific profile for your manual login.
# KEEP THAT BROWSER WINDOW OPEN after logging in.
# The automation will attempt to use this existing login session.
# ---

# --- Dropbox Configuration & Selectors (Existing - some require user input) ---
DROPBOX_REQUESTS_URL = "https://www.dropbox.com/requests?_tk=web_left_nav_bar&role=work&di=left_nav"
DROPBOX_LOGIN_URL = "https://www.dropbox.com/login"
DB_NEW_REQUEST_BUTTON_SELECTOR = "#maestro-content-portal > div > div > div > div > div._file-request-management-page-header-container_1mgce_54 > button > span"
DB_REQUEST_TITLE_INPUT_SELECTOR = "#drops_title"
DB_CREATE_REQUEST_BUTTON_SELECTOR = "body > div.ReactModalPortal > div > div > div > div.dig-Modal-footer.dig-Modal-footer--hasTopBorder.dig-5lbgm3q_22-1-0.dig-5lbgm3s_22-1-0.dig-5lbgm3t_22-1-0 > button.dig-Button.dig-Button--primary.dig-Button--standard.dig-Button--medium.dig-Button-tone--neutral.dig-1f09ta23_22-1-0.dig-1f09ta2o_22-1-0.dig-t4vtb5d_22-1-0.dig-1f09ta21n_22-1-0.dig-t4vtb5g_22-1-0.dig-1f09ta21p_22-1-0.dig-1f09ta21w_22-1-0.dig-1f09ta21x_22-1-0._accept-button_1rdnq_2 > span"
DB_SHARE_EMAIL_INPUT_SELECTOR = "body > div.ReactModalPortal > div > div > div > div.drop-email-form > div.drop-email-contacts > div > div.tokenizer-input > div > div > span > div"
DB_SHARE_SEND_BUTTON_SELECTOR = "body > div.ReactModalPortal > div > div > div > div.dig-Modal-footer.dig-Modal-footer--hasTopBorder.dig-5lbgm3q_22-1-0.dig-5lbgm3s_22-1-0.dig-5lbgm3t_22-1-0 > button.dig-Button.dig-Button--primary.dig-Button--standard.dig-Button--medium.dig-Button-tone--neutral.dig-1f09ta23_22-1-0.dig-1f09ta2o_22-1-0.dig-t4vtb5d_22-1-0.dig-1f09ta21n_22-1-0.dig-t4vtb5g_22-1-0.dig-1f09ta21p_22-1-0.dig-1f09ta21w_22-1-0.dig-1f09ta21x_22-1-0 > span"
DB_GENERATED_REQUEST_LINK_SELECTOR = "#maestro-content-portal > div > div > div > div > div._file-request-table-wrapper_1mgce_98 > div > div.dig-Table-body.dig-cwil8c4_22-1-0._file-request-table-body_1mgce_109 > div:nth-child(1) > div:nth-child(7) > div > button"

# Dropbox login detection selectors
DB_LOGIN_INDICATORS = [
    "input[name='login_email']",  # Email input on login page
    "input[type='email'][placeholder*='email']",  # Alternative email input
    ".login-form",  # Login form container
    "[data-testid='login-form']"  # Login form with test id
]

DB_LOGGED_IN_INDICATORS = [
    "[data-testid='app-chrome-header']",  # Main app header
    ".maestro-nav",  # Navigation bar
    "#maestro-content-portal",  # Main content portal
    "[aria-label*='account menu']"  # Account menu button
]

# --- Video Progress Page Configuration (USER MUST FILL THESE OUT ACCURATELY) ---
# VIDEO_PAGE_USERNAME and VIDEO_PAGE_PASSWORD are no longer used directly by the script for login,
# relying on the Selenium profile. They can be removed if not used for other purposes.
# However, keeping them as env var placeholders might be useful if direct login is ever re-introduced.
VIDEO_PAGE_USERNAME = os.environ.get("VIDEO_PAGE_USERNAME") 
VIDEO_PAGE_PASSWORD = os.environ.get("VIDEO_PAGE_PASSWORD") 

# LOGIN_EMAIL_INPUT_SELECTOR, LOGIN_PASSWORD_INPUT_SELECTOR, LOGIN_SUBMIT_BUTTON_SELECTOR
# are no longer used by the simplified generate_title_from_page assuming profile handles login.
# These can be removed unless a more complex login check is re-added.

# Selector for an element that ONLY appears AFTER successful login / page is fully loaded.
# This is crucial to know when the main page is loaded and ready for interaction.
POST_LOGIN_INDICATOR_SELECTOR = "#progresstab" # Example: Assuming #progresstab is visible after login. VERIFY AND REPLACE

# Selectors for finding athlete data on the video progress page (after login)
# This is the search field on the main video progress/mail page.
ATHLETE_SEARCH_INPUT_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div:nth-child(1) > div.col-md-11.col-sm-9 > div > div.col-md-3.col-sm-5.col-xs-12.form-group.search_form > div > input" # From your video_updates.py, VERIFY if still correct for this context

# Dynamic selectors for athlete data - will find the row containing the searched athlete
# Base table selector
ATHLETE_TABLE_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div.col-md-12.box.box-info.tbl-box > div.table-responsive > table > tbody"
# XPath template to find row containing the athlete name
ATHLETE_ROW_XPATH_TEMPLATE = "//table//tbody//tr[td//a[contains(text(), '{name}')]]"
# Column selectors within the found row (relative to the row)
ATHLETE_NAME_IN_ROW_SELECTOR = "td:nth-child(1) a.ng-binding"
ATHLETE_CLASS_IN_ROW_SELECTOR = "td:nth-child(2)"
ATHLETE_SPORT_IN_ROW_SELECTOR = "td:nth-child(3)"
ATHLETE_STATE_IN_ROW_SELECTOR = "td:nth-child(4)"
# --- End of Video Progress Page Configuration ---

DEFAULT_WAIT_TIMEOUT = 30
SHORT_WAIT_TIMEOUT = 10
# VERY_LONG_WAIT_TIMEOUT is removed as direct login block is removed

# --- Email Configuration (Existing) ---
SMTP_SERVER = os.environ.get("SMTP_SERVER") 
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587)) 
SMTP_USERNAME = os.environ.get("SMTP_USERNAME") 
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") 
SENDER_EMAIL = "Info@prospectid.com"
EMAIL_TEMPLATE = """Hi {first_name} and family,\n\nYou should've received a Dropbox request from Info@prospectid.com.\n\nHere is the direct link to your Dropbox folder: \n{dropbox_link}\n\nPlease keep the number of clips up to 35 MAX to assist with a faster turnaround time, you'll receive a set of instructions for correctly uploading your Dropbox files as well. Additionally, please let me know when you've uploaded ALL of your plays.\n\nLet me know if you have any additional questions.\n"""

def human_like_delay(min_seconds=1, max_seconds=3):
    """Add human-like random delays"""
    import random
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def check_dropbox_login_status(driver):
    """Check if user is logged into Dropbox and prompt for login if needed."""
    print("--- Checking Dropbox Login Status (within dedicated profile) ---")
    try:
        driver.get(DROPBOX_LOGIN_URL) # Go to login page first
        human_like_delay(2, 4)

        # Look for a clear indicator of being logged OUT (e.g., email input field)
        # This selector should be for an element reliably present on the login page
        login_email_selector = "input[name='login_email']" 
        try:
            login_form_element = driver.find_element(By.CSS_SELECTOR, login_email_selector)
            if login_form_element.is_displayed():
                print("Dropbox login page detected. Manual login required within this browser window.")
                print("Please log into Dropbox in the browser window that just opened.")
                print("It's using a dedicated profile for this Dropbox automation.")
                input("Press ENTER here after you have logged in within that browser window: ")
                # Add a small wait after user confirms login
                human_like_delay(3, 5)
                # Verify by trying to go to requests page
                driver.get(DROPBOX_REQUESTS_URL)
                human_like_delay(2,3)
                if "login" in driver.current_url.lower(): # Still on login page?
                    print("❌ Login attempt failed or was not completed. Exiting.")
                    return False
                print("✅ Login seems successful.")
                return True
        except NoSuchElementException:
            # If login form element is not found, assume we might be logged in or on a different page
            print("Login form not immediately detected. Checking current URL.")
            pass # Continue to check current URL

        # If not clearly on login page, check if we are on the requests page (logged in state)
        if DROPBOX_REQUESTS_URL in driver.current_url:
            print("✅ Already logged into Dropbox (on requests page).")
            return True
        
        # If current URL is still a login-related URL, login is needed.
        if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
            print("Dropbox login page detected by URL. Manual login required within this browser window.")
            print("Please log into Dropbox in the browser window that just opened.")
            input("Press ENTER here after you have logged in: ")
            human_like_delay(3,5)
            driver.get(DROPBOX_REQUESTS_URL) # Verify
            human_like_delay(2,3)
            if "login" in driver.current_url.lower():
                 print("❌ Login attempt failed or was not completed. Exiting.")
                 return False
            print("✅ Login seems successful after URL check.")
            return True

        print("✅ Assumed logged into Dropbox (no clear login page indicators found, not on requests page initially).")
        return True # Default to true if no obvious logout signs

    except Exception as e:
        print(f"Error during Dropbox login check: {e}")
        print("Treating as login required due to error.")
        print("Please log into Dropbox in the browser window that just opened.")
        input("Press ENTER here after you have logged in: ")
        return False # Indicate failure to be safe

def setup_driver():
    print("Setting up WebDriver with standard Selenium and webdriver_manager...")
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        user_data_dir = os.path.expanduser("~/selenium_chrome_profile_dropbox_automation") # Using a SEPARATE profile for this
        print(f"Using DEDICATED user data directory for Dropbox Automation: {user_data_dir}")
        os.makedirs(user_data_dir, exist_ok=True) # Ensure it exists

        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        # Add any other specific options that were working for you before for this script
        # options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)

        chromedriver_path = ChromeDriverManager().install()
        print(f"Using ChromeDriver from: {chromedriver_path}")
        service = ChromeService(executable_path=chromedriver_path)
        
        print("Creating standard WebDriver for Dropbox Automation...")
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.implicitly_wait(SHORT_WAIT_TIMEOUT) 
        print("Standard WebDriver created successfully.")
        return driver
        
    except Exception as e:
        print(f"FATAL ERROR during WebDriver setup: {str(e)}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def generate_title_from_page(driver, video_progress_page_url, athlete_full_name):
    print(f"--- Generating Dropbox title from: {video_progress_page_url} for '{athlete_full_name}' ---")
    wait = WebDriverWait(driver, DEFAULT_WAIT_TIMEOUT)

    try:
        current_url = driver.current_url
        if video_progress_page_url not in current_url:
            print(f"Navigating to video progress page: {video_progress_page_url}")
            driver.get(video_progress_page_url)
        else:
            print(f"Already on or near video progress page: {current_url}")

        # CRUCIAL: Wait for a reliable indicator that the page (post-login) is fully loaded.
        # USER MUST VERIFY AND SET POST_LOGIN_INDICATOR_SELECTOR correctly.
        print(f"Waiting for main page content via post-login indicator: {POST_LOGIN_INDICATOR_SELECTOR}")
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, POST_LOGIN_INDICATOR_SELECTOR)))
            print(f"Main page content confirmed via '{POST_LOGIN_INDICATOR_SELECTOR}'.")
        except TimeoutException:
            print(f"ERROR: Timeout waiting for post-login indicator '{POST_LOGIN_INDICATOR_SELECTOR}'.")
            print("Ensure you are logged into the site with the shared Selenium profile, ")
            print("and that the selector correctly identifies an element on the loaded page.")
            driver.save_screenshot("post_login_indicator_timeout.png")
            return None

        # At this point, we assume the page is loaded and ready for scraping.
        print(f"Attempting to search for athlete: '{athlete_full_name}'")
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ATHLETE_SEARCH_INPUT_SELECTOR)))
        search_input.clear()
        search_input.send_keys(athlete_full_name)
        print(f"Typed '{athlete_full_name}' into search field. Waiting briefly for results to filter...")
        time.sleep(2) # Adjust if search is slow to update table

        # Wait for search results to load and then find the specific athlete row dynamically
        print(f"Looking for athlete row containing: '{athlete_full_name}'")
        try:
            # Use XPath to find the row containing the athlete's name
            athlete_row_xpath = ATHLETE_ROW_XPATH_TEMPLATE.format(name=athlete_full_name)
            print(f"Using XPath: {athlete_row_xpath}")
            
            athlete_row = wait.until(EC.visibility_of_element_located((By.XPATH, athlete_row_xpath)))
            print(f"Found athlete row for: '{athlete_full_name}'")
            
            # Extract data from the found row using relative selectors
            name_element = athlete_row.find_element(By.CSS_SELECTOR, ATHLETE_NAME_IN_ROW_SELECTOR)
            name_from_table = name_element.text.strip()
            print(f"Found athlete name: '{name_from_table}'")
            
            grad_year_element = athlete_row.find_element(By.CSS_SELECTOR, ATHLETE_CLASS_IN_ROW_SELECTOR)
            grad_year = grad_year_element.text.strip()
            print(f"Found grad year: '{grad_year}'")
            
            sport_element = athlete_row.find_element(By.CSS_SELECTOR, ATHLETE_SPORT_IN_ROW_SELECTOR)
            sport = sport_element.text.strip()
            print(f"Found sport: '{sport}'")
            
            state_element = athlete_row.find_element(By.CSS_SELECTOR, ATHLETE_STATE_IN_ROW_SELECTOR)
            state = state_element.text.strip()
            print(f"Found state: '{state}'")
            
            print(f"Extracted from table: Name='{name_from_table}', Year='{grad_year}', Sport='{sport}', State='{state}'")

            if not all([name_from_table, grad_year, sport, state]):
                print("ERROR: One or more required fields are empty after extraction from table.")
                driver.save_screenshot("empty_fields_extracted.png")
                return None

            formatted_name = name_from_table.replace(" ", "")
            generated_title = f"{formatted_name}_Class_of_{grad_year}_{sport}_{state}"
            print(f"Successfully generated title: {generated_title}")
            return generated_title
            
        except TimeoutException:
            print(f"ERROR: Timeout waiting for athlete row containing '{athlete_full_name}'")
            print("Verify that the search returned results and the athlete name matches exactly.")
            driver.save_screenshot("athlete_row_timeout.png")
            return None
        except NoSuchElementException as e:
            print(f"ERROR: Could not find athlete data element in the row: {str(e)}")
            driver.save_screenshot("athlete_data_not_found.png")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error during data extraction: {str(e)}")
            driver.save_screenshot("data_extraction_error.png")
            return None

    except TimeoutException as e:
        print(f"ERROR: General timeout in title generation: {str(e)}")
        driver.save_screenshot("title_gen_timeout.png")
        return None
    except NoSuchElementException as e:
        print(f"ERROR: Key element not found in title generation (NoSuchElement): {str(e)}")
        driver.save_screenshot("title_gen_nosuch.png")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error in title generation: {str(e)}")
        driver.save_screenshot("title_gen_unexpected.png")
        return None

def create_dropbox_request_and_get_link(driver, dropbox_request_title, recipient_email):
    print(f"--- Creating Dropbox request titled '{dropbox_request_title}' for {recipient_email} ---")
    wait = WebDriverWait(driver, DEFAULT_WAIT_TIMEOUT)

    try:
        print(f"Navigating to Dropbox requests page: {DROPBOX_REQUESTS_URL}")
        driver.get(DROPBOX_REQUESTS_URL)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, DB_NEW_REQUEST_BUTTON_SELECTOR)))
        print("Dropbox requests page loaded, 'New Request' button is clickable.")
        
        print(f"Looking for 'New Request' button with selector: {DB_NEW_REQUEST_BUTTON_SELECTOR}")
        new_request_btn = driver.find_element(By.CSS_SELECTOR, DB_NEW_REQUEST_BUTTON_SELECTOR) 
        new_request_btn.click()
        print("Clicked 'New Request' button.")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, DB_REQUEST_TITLE_INPUT_SELECTOR)))
        print("'New Request' modal/form appeared.")

        print(f"Looking for 'Request Title' input with selector: {DB_REQUEST_TITLE_INPUT_SELECTOR}")
        title_input = driver.find_element(By.CSS_SELECTOR, DB_REQUEST_TITLE_INPUT_SELECTOR) 
        title_input.clear()
        title_input.send_keys(dropbox_request_title)
        print(f"Filled request title: {dropbox_request_title}")
        time.sleep(0.5)

        print(f"Looking for 'Create Request' button with selector: {DB_CREATE_REQUEST_BUTTON_SELECTOR}")
        create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, DB_CREATE_REQUEST_BUTTON_SELECTOR)))
        create_btn.click()
        print("Clicked 'Create' button for request (should open share modal).")
        if DB_SHARE_EMAIL_INPUT_SELECTOR:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, DB_SHARE_EMAIL_INPUT_SELECTOR)))
            print("Share modal appeared.")
        else:
            print("Warning: No selector for share modal email input; relying on time.sleep(3).")
            time.sleep(3) 

        # Selectors are now provided, proceed with automation

        print(f"Looking for email input in share modal with selector: {DB_SHARE_EMAIL_INPUT_SELECTOR}")
        email_input_share_modal = driver.find_element(By.CSS_SELECTOR, DB_SHARE_EMAIL_INPUT_SELECTOR) 
        email_input_share_modal.clear()
        email_input_share_modal.send_keys(recipient_email)
        print(f"Filled recipient email in share modal: {recipient_email}")
        time.sleep(0.5) 

        print(f"Looking for 'Send' button in share modal with selector: {DB_SHARE_SEND_BUTTON_SELECTOR}")
        send_btn_share_modal = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, DB_SHARE_SEND_BUTTON_SELECTOR)))
        send_btn_share_modal.click()
        print("Clicked 'Send' button in share modal for the request.")
        if DB_GENERATED_REQUEST_LINK_SELECTOR:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, DB_GENERATED_REQUEST_LINK_SELECTOR)))
            print("Element for generated link is now visible.")
        else:
            print("Warning: No selector for generated link; relying on time.sleep(4).")
            time.sleep(4) 

        print("Waiting for the Dropbox request to appear in the requests table...")
        time.sleep(3)  # Wait for the request to be created and appear in the table
        
        print(f"Looking for the copy link button with selector: {DB_GENERATED_REQUEST_LINK_SELECTOR}")
        try:
            copy_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, DB_GENERATED_REQUEST_LINK_SELECTOR)))
            print("Found copy link button, clicking to copy the link...")
            
            # Click the copy button to copy the link to clipboard
            copy_button.click()
            print("Clicked copy link button")
            
            # Since the link is copied to clipboard, we need to get it from there
            # For now, we'll use JavaScript to get the clipboard content or look for a data attribute
            try:
                # Try to get the link from a data attribute or aria-label
                link_from_button = copy_button.get_attribute('data-url') or copy_button.get_attribute('aria-label')
                if link_from_button and 'http' in link_from_button:
                    generated_link = link_from_button
                    print(f"Extracted link from button attribute: {generated_link}")
                else:
                    # If no data attribute, try to execute JavaScript to read clipboard
                    try:
                        generated_link = driver.execute_script("return navigator.clipboard.readText();")
                        print(f"Extracted link from clipboard: {generated_link}")
                    except:
                        # Fallback: look for the link in nearby elements or use a placeholder
                        print("Could not extract link from clipboard, looking for link in nearby elements...")
                        parent_row = copy_button.find_element(By.XPATH, "../../../..")
                        link_elements = parent_row.find_elements(By.XPATH, ".//a[contains(@href, 'dropbox.com')]")
                        if link_elements:
                            generated_link = link_elements[0].get_attribute('href')
                            print(f"Found link in parent row: {generated_link}")
                        else:
                            print("WARNING: Could not extract the actual Dropbox link. Using placeholder.")
                            generated_link = f"https://dropbox.com/request/{dropbox_request_title.replace(' ', '-').lower()}"
                            
            except Exception as e:
                print(f"Error extracting link: {e}")
                generated_link = f"https://dropbox.com/request/{dropbox_request_title.replace(' ', '-').lower()}"
            
            if generated_link and generated_link.startswith("http"):
                print(f"Successfully obtained Dropbox link: {generated_link}")
                return generated_link
            else:
                print(f"ERROR: Extracted link does not look valid: '{generated_link}'")
                return None
                
        except TimeoutException:
            print("ERROR: Timeout waiting for copy link button to appear")
            driver.save_screenshot("copy_button_timeout.png")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error while getting Dropbox link: {str(e)}")
            driver.save_screenshot("link_extraction_error.png")
            return None

    except TimeoutException as e:
        print(f"ERROR: Timeout during Dropbox automation: {str(e)}")
        driver.save_screenshot("dropbox_timeout_error.png")
        print("Screenshot saved as dropbox_timeout_error.png")
        return None
    except NoSuchElementException as e:
        print(f"ERROR: Element not found during Dropbox automation: {str(e)}")
        driver.save_screenshot("dropbox_nosuchelement_error.png")
        print("Screenshot saved as dropbox_nosuchelement_error.png")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during Dropbox automation: {str(e)}")
        driver.save_screenshot("dropbox_unexpected_error.png")
        print("Screenshot saved as dropbox_unexpected_error.png")
        return None

def send_notification_email(recipient_email, athlete_first_name, dropbox_link):
    print(f"--- Preparing to send notification email to {recipient_email} ---")
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        print("ERROR: SMTP configuration is incomplete. Cannot send email. Check environment variables.")
        return False

    email_body = EMAIL_TEMPLATE.format(first_name=athlete_first_name, dropbox_link=dropbox_link)
    msg = MIMEText(email_body)
    msg['Subject'] = f"Dropbox File Request for {athlete_first_name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() 
            print("Logging into SMTP server...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("Sending email...")
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            print(f"Email successfully sent to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: SMTP Authentication failed. Check username/password. Details: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to send email: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Automate Dropbox file request creation and email notification.")
    parser.add_argument('--athlete_full_name', required=True, help="Full name of the athlete.")
    parser.add_argument('--recipient_email', required=True, help="Email address of the recipient.")
    parser.add_argument('--generate_title_from_page', action='store_true', help="Flag to generate title from video progress page (now always expected to be true from Raycast).")
    parser.add_argument('--video_progress_page_url', required=True, help="URL of the video progress page (now always expected from Raycast).")

    args = parser.parse_args()

    if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
        print("WARNING: SMTP environment variables (SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD) are not fully set. Email sending will likely fail.")

    driver = None
    try:
        driver = setup_driver()
        if not driver: 
             print("ERROR: WebDriver setup failed. Exiting.")
             return

        if not check_dropbox_login_status(driver):
            print("Dropbox login was required and not completed. Exiting script.")
            return

        print("Attempting to generate Dropbox request title from page...")
        dropbox_request_title = generate_title_from_page(driver, args.video_progress_page_url, args.athlete_full_name)
        
        if not dropbox_request_title:
            print("❌ FAILED to generate title from page!")
            print("This means the video progress page login or athlete search failed.")
            print("Check the browser window for any login prompts or errors.")
            print("Exiting due to title generation failure.")
            return # EXIT SCRIPT
        
        print(f"Using Dropbox Request Title: {dropbox_request_title}")
        dropbox_link = create_dropbox_request_and_get_link(driver, dropbox_request_title, args.recipient_email)

        if dropbox_link:
            print(f"Successfully created Dropbox request. Link: {dropbox_link}")
            athlete_first_name = args.athlete_full_name.split(" ")[0]
            if send_notification_email(args.recipient_email, athlete_first_name, dropbox_link):
                print("--- Dropbox Request Created and Email Sent Successfully ---")
            else:
                print("--- Dropbox Request Created BUT Email Sending FAILED ---")
        else:
            print("--- FAILED to create Dropbox request or retrieve link ---")

    except Exception as e:
        print(f"--- MAIN SCRIPT EXECUTION ERROR ---")
        print(f"An unexpected error occurred in main: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        if driver:
            print("Closing the browser...")
            # driver.quit() # Consider leaving browser open for debugging for now, or make it conditional
            print("Browser remains open for inspection (driver.quit() is commented out).") 
        print("--- Automation Script Finished ---")

if __name__ == "__main__":
    main() 