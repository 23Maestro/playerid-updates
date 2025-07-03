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

# --- Configuration & Selectors ---
BASE_URL = "https://dashboard.nationalpid.com/videoteammsg/videomailprogress"

# Common Selectors
SEARCH_FIELD_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div:nth-child(1) > div.col-md-11.col-sm-9 > div > div.col-md-3.col-sm-5.col-xs-12.form-group.search_form > div > input"
PERSON_ICON_SELECTOR = "#progresstab > div:nth-child(2) > div > div.content > div.col-md-12.box.box-info.tbl-box > div.table-responsive > table > tbody > tr:nth-child(1) > td:nth-child(1) > a:nth-child(2) > i"
VIDEO_TAB_SELECTOR_CSS = "#profile_main_section > div > div:nth-child(1) > div > div:nth-child(3) > div.panel.panel-primary.profile_table.main_video_box > div > a"
VIDEO_TAB_FALLBACK_SELECTORS = [
    {"by": By.XPATH, "value": "//*[@id='profile_main_section']/div/div[1]/div/div[2]/div[1]/div/a"},
    {"by": By.XPATH, "value": "//a[contains(., 'Videos') or contains(., 'Video')]"},
    {"by": By.XPATH, "value": "//a[contains(@href, 'video')]"},
    {"by": By.XPATH, "value": "//div[contains(@class, 'video') or contains(@class, 'profile_table')]//a"}
]
EDIT_BUTTON_SELECTOR = "#btn_edit" # First edit button

# Selectors for revisions flow
SECOND_EDIT_BUTTON_SELECTOR = 'a[data-target="#videos_modal"][onclick*="OpenEventDlg"]'
REVISED_VIDEO_URL_INPUT_SELECTOR = "#updatevideos > div.modal-body > div:nth-child(2) > div:nth-child(2) > input"
REVISIONS_SAVE_BUTTON_SELECTOR = "#btn_update_profile"

DEFAULT_WAIT_TIMEOUT = 30
SHORT_WAIT_TIMEOUT = 10
VERY_SHORT_WAIT_TIMEOUT = 5

def process_video_revisions(driver, athlete_name, revised_youtube_link):
    print("--- Starting Video Revisions (Python Selenium) ---")
    print(f"Athlete: {athlete_name}, Revised Link: {revised_youtube_link}")
    wait = WebDriverWait(driver, DEFAULT_WAIT_TIMEOUT)
    short_wait = WebDriverWait(driver, SHORT_WAIT_TIMEOUT) # Not used yet, but good to have

    try:
        # Common steps: Navigate to site, search athlete, go to profile, click video tab, click first edit button
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
        search_field.send_keys(athlete_name)
        print(f"Typed '{athlete_name}' into search field.")
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
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, VIDEO_TAB_SELECTOR_CSS)))
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

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, EDIT_BUTTON_SELECTOR)))
        print("Video tab content (first edit button) seems to have loaded.")

        print("Attempting to click the FIRST 'Edit' button...")
        edit_button_one = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, EDIT_BUTTON_SELECTOR)))
        edit_button_one.click()
        print("FIRST 'Edit' button clicked.")

        # --- Revisions-specific steps ---
        print("--- Revisions Mode Steps Initiated ---")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SECOND_EDIT_BUTTON_SELECTOR)))
        print("Second edit button for revisions seems to have loaded.")
        
        print(f"Attempting to click the SECOND 'Edit' button: {SECOND_EDIT_BUTTON_SELECTOR}")
        second_edit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SECOND_EDIT_BUTTON_SELECTOR)))
        # Consider adding a small delay or scroll into view if needed before click
        # driver.execute_script("arguments[0].scrollIntoView(true);", second_edit_button)
        # time.sleep(0.5)
        second_edit_button.click()
        print("SECOND 'Edit' button clicked.")

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, REVISED_VIDEO_URL_INPUT_SELECTOR)))
        print("Revised video URL input field modal seems to have loaded.")
        
        revised_url_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, REVISED_VIDEO_URL_INPUT_SELECTOR)))
        revised_url_input.clear()
        revised_url_input.send_keys(revised_youtube_link)
        print(f"Filled Revised Video URL: {revised_youtube_link}")
        
        print(f"Attempting to click 'Save Changes' for revisions inside the modal only: {REVISIONS_SAVE_BUTTON_SELECTOR}")
        # Find the modal container first (parent of the input field)
        modal = revised_url_input.find_element(By.XPATH, "./ancestor::div[contains(@class, 'modal-content') or contains(@class, 'modal-dialog')]")
        # Now find the Save Changes button within this modal
        revisions_save_button = modal.find_element(By.CSS_SELECTOR, REVISIONS_SAVE_BUTTON_SELECTOR)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, REVISIONS_SAVE_BUTTON_SELECTOR)))
        revisions_save_button.click()
        print("Revisions 'Save Changes' button clicked.")

        print("Pausing for a few seconds to allow dialog to appear and attempting to accept if present...")
        time.sleep(VERY_SHORT_WAIT_TIMEOUT) # VERY_SHORT_WAIT_TIMEOUT should be defined or use a literal like 5
        try:
            alert = driver.switch_to.alert
            print(f"Alert found with text: {alert.text}. Accepting it.")
            alert.accept()
            print("Alert accepted.")
        except NoAlertPresentException:
            print("No alert was present after clicking 'Save Changes' for revisions, or it was handled too quickly.")

        time.sleep(3) # Wait for save to process
        print("--- Revisions Processed Successfully ---")

    except TimeoutException as e:
        print(f"--- AUTOMATION ERROR (Revisions): A timeout occurred --- Details: {e}")
    except NoSuchElementException as e:
        print(f"--- AUTOMATION ERROR (Revisions): An element was not found --- Details: {e}")
    except Exception as e:
        print(f"--- AN UNEXPECTED AUTOMATION ERROR OCCURRED (Revisions) --- Details: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc(file=sys.stdout)
    finally:
        print("--- Revisions Script Finished (Python Selenium) ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video revisions for an athlete profile.")
    parser.add_argument('--athlete_name', required=True, help="Name of the athlete to search for")
    parser.add_argument('--revised_youtube_link', required=True, help="URL of the revised YouTube video")
    args = parser.parse_args()

    print("Setting up WebDriver with persistent Chrome profile for Revisions...")
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

        process_video_revisions(driver, args.athlete_name, args.revised_youtube_link)

    except Exception as e:
        print(f"An error occurred during WebDriver setup or script execution (Revisions): {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc(file=sys.stdout)
    finally:
        if driver:
            print("Closing the browser (Revisions script)...")
            driver.quit()