#!/usr/bin/env python3
"""
Manual Dropbox Login Helper

This script opens a regular Chrome browser (not automated) for you to log into Dropbox manually.
This avoids the anti-automation detection that causes CAPTCHA issues.

After logging in with this script, the main automation will be able to use your session.
"""

import os
import subprocess
import sys
import time

def open_manual_login_browser():
    """Open a regular Chrome browser for manual login"""
    print("=== Manual Dropbox Login Helper ===")
    print()
    print("This will open a regular Chrome browser (not automated) for you to log into Dropbox.")
    print("This avoids the anti-automation detection that causes CAPTCHA failures.")
    print()
    
    # Use the same profile directory as the automation
    user_data_dir = os.path.expanduser("~/selenium_chrome_profile")
    
    # Ensure the profile directory exists
    os.makedirs(user_data_dir, exist_ok=True)
    
    print(f"Using Chrome profile: {user_data_dir}")
    print()
    
    # Chrome command to open with the same profile
    chrome_commands = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Linux alternative
        "chrome",  # Windows/PATH
        "google-chrome"  # Generic
    ]
    
    chrome_path = None
    for cmd in chrome_commands:
        try:
            if os.path.exists(cmd):
                chrome_path = cmd
                break
            else:
                # Try to find it in PATH
                result = subprocess.run(["which", cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    chrome_path = cmd.strip()
                    break
        except:
            continue
    
    if not chrome_path:
        print("❌ Could not find Chrome browser. Please install Google Chrome.")
        print("   You can also manually open Chrome with this profile:")
        print(f"   --user-data-dir={user_data_dir}")
        return False
    
    print(f"Found Chrome at: {chrome_path}")
    
    # Open Chrome with the profile and navigate to Dropbox
    dropbox_url = "https://www.dropbox.com/login"
    
    try:
        print(f"Opening Chrome with Dropbox login page...")
        subprocess.Popen([
            chrome_path,
            f"--user-data-dir={user_data_dir}",
            "--new-window",
            dropbox_url
        ])
        
        print("✅ Chrome browser opened!")
        print()
        print("📋 INSTRUCTIONS:")
        print("1. Complete the login process in the browser that just opened")
        print("2. Solve any CAPTCHA if prompted (should work normally now)")
        print("3. Make sure you can access dropbox.com/requests")
        print("4. Keep the browser open")
        print("5. Run your automation script - it will use this login session")
        print()
        print("💡 TIP: The automation uses the same Chrome profile, so your login")
        print("   session will be shared between this browser and the automation.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error opening Chrome: {e}")
        print()
        print("🔧 MANUAL ALTERNATIVE:")
        print("1. Open Google Chrome manually")
        print("2. Go to Chrome Settings > Advanced > System")
        print("3. Add this flag to Chrome shortcut or command line:")
        print(f"   --user-data-dir={user_data_dir}")
        print("4. Navigate to https://www.dropbox.com/login")
        print("5. Complete the login process")
        
        return False

def main():
    print("Starting manual Dropbox login helper...")
    
    if open_manual_login_browser():
        print("\n🎉 Browser opened successfully!")
        print("Complete your login, then run the main automation script.")
        print("The automation will use your existing login session.")
    else:
        print("\n❌ Failed to open browser automatically.")
        print("Please follow the manual instructions above.")
    
    print("\nPress ENTER to exit...")
    input()

if __name__ == "__main__":
    main() 