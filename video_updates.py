#!/usr/bin/env python3
import time
import argparse
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException

# --- Configuration & Selectors (mirrored from JavaScript) ---
BASE_URL = "https://dashboard.nationalpid.com/videoteammsg/videomailprogress"

# Selectors for main update flow (adding a NEW video)
SEARCH_FIELD_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div:nth-child(1) > div.col-md-11.col-sm-9 > div > div.col-md-3.col-sm-5.col-xs-12.form-group.search_form > div > input"
PERSON_ICON_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div.col-md-12.box.box-info.tbl-box > div.table-responsive > table > tbody > tr:nth-child(1) > td:nth-child(1) > a:nth-child(2) > i"
VIDEO_TAB_SELECTOR_CSS = "#profile_main_section > div > div:nth-child(1) > div > div:nth-child(3) > div.panel.panel-primary.profile_table.main_video_box > div > a"
VIDEO_TAB_FALLBACK_SELECTORS = [
    {"by": By.XPATH, "value": "//*[@id='profile_main_section']/div/div[1]/div/div[2]/div[1]/div/a"},
    {"by": By.XPATH, "value": "//a[contains(., 'Videos') or contains(., 'Video')]"},
    {"by": By.XPATH, "value": "//a[contains(@href, 'video')]"},
    {"by": By.XPATH, "value": "//div[contains(@class, 'video') or contains(@class, 'profile_table')]//a"}
]
EDIT_BUTTON_SELECTOR = "#btn_edit" # First edit button (to open the new video form)
VIDEO_URL_INPUT_SELECTOR = "#newVideoLink"
TITLE_INPUT_SELECTOR = "#newVideoTitle"
DESCRIPTION_INPUT_SELECTOR = "#form_save_profile > div:nth-child(6) > div:nth-child(1) > div:nth-child(6) > div.col-md-6 > input"
DATE_INPUT_SELECTOR = "#newVideoDate"
APPROVED_VIDEO_CHECKBOX_SELECTOR = "#add_approve_video"
ADD_VIDEO_BUTTON_SELECTOR = "input#btn_save_profile.btn.btn-primary"
POST_ALERT_SAVE_CHANGES_BUTTON_SELECTOR = "input#btn_save_profile.btn.btn-primary.photos_videosbtn"

DEFAULT_WAIT_TIMEOUT = 30
SHORT_WAIT_TIMEOUT = 10
VERY_SHORT_WAIT_TIMEOUT = 5

def update_video_info_in_browser(driver, args):
    print("--- Starting Video Automation (Python Selenium) ---")
    wait = WebDriverWait(driver, DEFAULT_WAIT_TIMEOUT)
    short_wait = WebDriverWait(driver, SHORT_WAIT_TIMEOUT) # Define short_wait here

    print(f"Adding new video for Athlete: {args.athlete_name}, Link: {args.youtube_link}, Season: {args.season}, Type: {args.video_type}")

    try:
        print(f"Ensuring current page is: {BASE_URL}")
        if driver.current_url != BASE_URL:
            print(f"Current URL is {driver.current_url}. Navigating to {BASE_URL}...")
            driver.get(BASE_URL)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_FIELD_SELECTOR)))
            print(f"Successfully navigated to: {BASE_URL}")
        else:
            print(f"Already on the target page: {BASE_URL}")

        print(f"Attempting to find SEARCH_FIELD_SELECTOR: {SEARCH_FIELD_SELECTOR}")
        search_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, SEARCH_FIELD_SELECTOR)))
        search_field.clear()
        search_field.send_keys(args.athlete_name)
        print(f"Typed '{args.athlete_name}' into search field.")
        time.sleep(1)

        print(f"Attempting to find person icon: {PERSON_ICON_SELECTOR}")
        person_icon_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PERSON_ICON_SELECTOR)))
        person_anchor_element = person_icon_element.find_element(By.XPATH, "./ancestor::a[1]")
        if not person_anchor_element:
            raise NoSuchElementException("Could not find profile link (anchor tag) for the person icon.")
        profile_url = person_anchor_element.get_attribute("href")
        if not profile_url:
            raise ValueError("Profile link (anchor tag) for the person icon does not have an href attribute.")
        print(f"Navigating directly to profile page: {profile_url}")
        driver.get(profile_url)
        print("Waiting for profile page to load...")
        # Wait for a general profile element, then specifically for video tab
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#profile_main_section"))) 
        print("Profile page seems to have loaded.")

        print("Navigating to video tab...")
        video_tab_clicked = False
        try:
            video_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, VIDEO_TAB_SELECTOR_CSS)))
            video_tab.click()
            video_tab_clicked = True
            print("Video tab clicked using primary selector.")
        except TimeoutException as e:
            print(f"Primary video tab CSS selector failed: {e}. Trying fallbacks...")
            for i, selector_info in enumerate(VIDEO_TAB_FALLBACK_SELECTORS):
                try:
                    fallback_video_tab = WebDriverWait(driver, VERY_SHORT_WAIT_TIMEOUT).until(
                        EC.element_to_be_clickable((selector_info['by'], selector_info['value']))
                    )
                    fallback_video_tab.click()
                    video_tab_clicked = True
                    print(f"Video tab clicked using fallback selector #{i + 1}.")
                    break 
                except TimeoutException as fallback_error:
                    print(f"Fallback video tab selector #{i + 1} ('{selector_info['value']}') failed: {fallback_error.msg}")
        if not video_tab_clicked:
            raise TimeoutException("All video tab selectors (primary and fallback) failed.")

        # RE-INSTATED: Click the initial 'Edit' button to reveal the new video form
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, EDIT_BUTTON_SELECTOR)))
        print("Video tab content (initial edit button) seems to have loaded.")
        print(f"Attempting to click the initial 'Edit' button: {EDIT_BUTTON_SELECTOR}")
        edit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, EDIT_BUTTON_SELECTOR)))
        edit_button.click()
        print("Initial 'Edit' button clicked.")

        print("--- Update Mode (Adding New Video) --- ")
        # Now wait for the new video form elements to be visible
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, VIDEO_URL_INPUT_SELECTOR)))
        print("Video form (for new video) seems to have loaded.")

        print("Filling video form...")
        video_url_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, VIDEO_URL_INPUT_SELECTOR)))
        video_url_input.clear()
        video_url_input.send_keys(args.youtube_link)
        print(f"Filled Video URL: {args.youtube_link}")

        title_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, TITLE_INPUT_SELECTOR)))
        title_input.clear()
        title_input.send_keys(args.season) # Season is used as title
        print(f"Filled Title (Season): {args.season}")

        description_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, DESCRIPTION_INPUT_SELECTOR)))
        description_input.clear()
        description_input.send_keys(args.video_type) # Video Type is used as description
        print(f"Filled Description (Video Type): {args.video_type}")

        current_date_str = datetime.now().strftime("%m/%d/%Y")
        date_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, DATE_INPUT_SELECTOR)))
        driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(current_date_str)
        print(f"Filled Date: {current_date_str}")

        approved_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, APPROVED_VIDEO_CHECKBOX_SELECTOR)))
        if not approved_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", approved_checkbox)
        print("Checked 'Approved Video'.")
        time.sleep(0.5)

        print(f"Attempting to click 'Add Video' button: {ADD_VIDEO_BUTTON_SELECTOR}")
        add_video_button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ADD_VIDEO_BUTTON_SELECTOR)))
        driver.execute_script("arguments[0].click();", add_video_button_element)
        print("'Add Video' button clicked.")

        print("Pausing for a few seconds to allow dialog to appear and attempting to accept if present...")
        time.sleep(VERY_SHORT_WAIT_TIMEOUT)
        try:
            alert = driver.switch_to.alert
            print(f"Alert found with text: {alert.text}. Accepting it.")
            alert.accept()
            print("Alert accepted.")
        except NoAlertPresentException:
            print("No alert was present after clicking 'Add Video', or it was handled too quickly.")
        
        print("Pausing after alert handling before attempting post-alert save...")
        time.sleep(3) # Changed pause to 3 seconds
        
        # Logic for clicking the second "Save Changes" button, using the same selector
        print(f"Attempting to click 'Save Changes' button (post-alert): {POST_ALERT_SAVE_CHANGES_BUTTON_SELECTOR}")
        try:
            post_alert_save_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, POST_ALERT_SAVE_CHANGES_BUTTON_SELECTOR)))
            driver.execute_script("arguments[0].click();", post_alert_save_button)
            print("'Save Changes' button (post-alert) clicked.")
            time.sleep(3) # Wait for save to process
            print("--- VIDEO UPDATE PROCESS ATTEMPTED SUCCESSFULLY (Python Selenium) ---")
        except TimeoutException:
            print("Could not find or click 'Save Changes' button (post-alert) within timeout.")
            print("This might be okay if the 'Add Video' action and alert already saved everything.")
            print("--- VIDEO ADDED, POST-ALERT SAVE SKIPPED OR NOT FOUND (Python Selenium) ---")

    except TimeoutException as e:
        print(f"--- AUTOMATION ERROR: A timeout occurred --- Details: {e}")
    except NoSuchElementException as e:
        print(f"--- AUTOMATION ERROR: An element was not found --- Details: {e}")
    except Exception as e:
        print(f"--- AN UNEXPECTED AUTOMATION ERROR OCCURRED --- Details: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc(file=sys.stdout)
    finally:
        print("--- Video Update Script Finished (Python Selenium) ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update video information for an athlete profile")
    parser.add_argument('--athlete_name', required=True, help="Name of the athlete to search for")
    
    # Arguments for 'update' mode (now the only mode)
    parser.add_argument('--youtube_link', required=True, help="URL of the YouTube video")
    parser.add_argument('--season', required=True, help="Season information")
    parser.add_argument('--video_type', required=True, help="Type of video")

    args = parser.parse_args()

    print("Setting up WebDriver with persistent Chrome profile...")
    driver = None
    try:
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        user_data_dir = os.path.expanduser("~/selenium_chrome_profile")
        print(f"Using user data directory: {user_data_dir}")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        
        chromedriver_path = ChromeDriverManager().install()
        print(f"Using ChromeDriver from: {chromedriver_path}")
        service = ChromeService(executable_path=chromedriver_path)
        
        print("Creating WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        print(f"WebDriver created. Browser: {driver.capabilities.get('browserName', 'unknown')}")
        print(f"Browser version: {driver.capabilities.get('browserVersion', 'unknown')}")
        driver.implicitly_wait(5)

        update_video_info_in_browser(driver, args)

    except Exception as e:
        print(f"An error occurred during WebDriver setup or script execution: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc(file=sys.stdout)
    finally:
        if driver:
            print("Closing the browser...")
            driver.quit()


