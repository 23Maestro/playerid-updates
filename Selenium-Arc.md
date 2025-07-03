
AI Agent Rules for Executing the Python Selenium Video Updater Script
These rules outline the prerequisites, setup, execution steps, and data handling for an AI agent tasked with running the provided Python Selenium script for updating video information.
I. Environment & Prerequisite Setup:
 * Rule 1.1 (Python Installation): Ensure a Python interpreter (version 3.6 or newer recommended) is installed and accessible in the execution environment.
 * Rule 1.2 (Selenium Installation): Verify that the Selenium Python package is installed. If not, install it using the command: pip install selenium.
 * Rule 1.3 (WebDriverManager Installation - Recommended): For automated WebDriver management, verify the webdriver-manager package is installed. If not, install it: pip install webdriver-manager.
 * Rule 1.4 (WebDriver Availability):
   * If using webdriver-manager (as per Rule 1.3), the agent should expect the script to handle WebDriver download and setup automatically for supported browsers (e.g., Chrome).
   * If webdriver-manager is not used or fails, the agent must ensure a compatible WebDriver (e.g., chromedriver for Chrome, geckodriver for Firefox) is:
     * Present in the system's PATH, OR
     * Its executable path is correctly specified within the script (the agent might need to be configured with this path or have a mechanism to discover it).
 * Rule 1.5 (Browser Installation): Ensure a compatible web browser (e.g., Google Chrome, Mozilla Firefox) is installed on the system where the script will run. The chosen WebDriver must match the installed browser.
II. Script Acquisition and Configuration:
 * Rule 2.1 (Script Location): The AI agent must have access to the Python Selenium script file (e.g., video_updater.py). This might involve retrieving it from a specified path, a version control system, or receiving it as input.
 * Rule 2.2 (Script Integrity): Before execution, ensure the script is complete and has not been corrupted. (Optional: Implement a checksum verification if necessary).
 * Rule 2.3 (WebDriver Configuration within Script):
   * If webdriver-manager is intended, confirm the script contains the necessary import and instantiation lines (e.g., from webdriver_manager.chrome import ChromeDriverManager; driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))).
   * If a manual WebDriver path is required, the agent might need to dynamically update the script or provide the path as a configuration parameter to the script execution environment if the script is designed to accept it. The default script example shows where this path would be set (driver_path = "/path/to/your/chromedriver").
III. Input Data Management:
 * Rule 3.1 (Required Input Parameters): The agent must acquire the following four pieces of information before initiating the script:
   * athlete_name (String): The name of the athlete to search for.
   * youtube_link (String): The URL of the YouTube video.
   * season (String): The season information to be used as the video title.
   * video_type (String): The type of video, used for the description.
 * Rule 3.2 (Data Source): The agent must be configured with a method to obtain these input parameters. This could be:
   * Direct API call parameters.
   * User input via a UI.
   * Reading from a configuration file or database.
   * Arguments passed from a calling process (e.g., Raycast, as mentioned in the original context).
 * Rule 3.3 (Data Validation - Basic): Before passing data to the script, perform basic validation (e.g., ensure youtube_link is a plausible URL format, ensure no required fields are empty).
IV. Execution and Monitoring:
 * Rule 4.1 (Execution Command): Execute the script using the Python interpreter: python /path/to/video_updater.py. If the script is designed to take inputs as command-line arguments, append them appropriately. (The provided script uses internal variables for the example, but this could be modified).
 * Rule 4.2 (Output Logging): Capture and monitor the standard output (and standard error) from the script. The script is designed to print progress and error messages.
 * Rule 4.3 (Browser Interaction): Understand that the script will launch and control a web browser. Ensure the environment allows for GUI interactions if not running headless (note: the current script is not configured for headless mode by default).
 * Rule 4.4 (Termination and Cleanup):
   * The script includes a driver.quit() in a finally block (potentially commented out or behind an input() for debugging). For automated execution, ensure driver.quit() is reliably called to close the browser and terminate the WebDriver session, even if errors occur.
   * If the script hangs or an input() prompt is active (as in the example's finally block for debugging), the agent needs a timeout mechanism or a way to provide the necessary input (or ensure such prompts are removed for fully automated runs).
V. Error Handling and Reporting:
 * Rule 5.1 (Error Detection): Monitor the script's output for error messages (e.g., "AUTOMATION ERROR," "AN UNEXPECTED AUTOMATION ERROR OCCURRED").
 * Rule 5.2 (Screenshot on Error - Optional): If the script is modified to save screenshots on error (as commented out in the example), know the location where these screenshots are saved for diagnostic purposes.
 * Rule 5.3 (Reporting): Report the success or failure of the script execution, including any relevant error messages or log outputs, to the initiating user or system.
VI. Specific Behavior Notes (from original script):
 * Rule 6.1 (Search Mechanism): Be aware that the script types the athlete's name and then directly attempts to click the profile icon, bypassing an explicit search submission (Enter key/button click). This relies on the website's dynamic search-as-you-type functionality.
 * Rule 6.2 (Alert Handling): The script attempts to automatically accept JavaScript alerts that may appear after clicking the "Add Video" button. If alerts are more complex or unexpected, manual intervention might be flagged as needed by the script's output.
By following these rules, an AI agent should be able to manage and execute the Selenium script effectively.
