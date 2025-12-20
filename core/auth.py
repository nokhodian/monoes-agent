import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
from newAgent.src.database.database import DataBase as SessionStore

class AuthManager:
    def __init__(self, platform):
        self.platform = platform.upper()
        self.session_store = SessionStore('MAC') # Defaulting to MAC for now

    def load_cookies(self, bot):
        """Load cookies from database into the bot."""
        print("  Loading cookies from database...")
        cookie_result = self.session_store.latest_cookies(self.platform)
        
        if cookie_result:
            bot.cookies = cookie_result[0]
            # Set other attributes if available
            if len(cookie_result) > 1 and cookie_result[1]:
                bot.username = cookie_result[1]
            if len(cookie_result) > 2 and cookie_result[2]:
                bot.profile_pic = cookie_result[2]
            print(f"  ✓ Cookies loaded (username: {bot.username or 'N/A'})")
            return True
        else:
            print(f"  ⚠ No cookies found for {self.platform}. You may need to log in manually.")
            # Set empty list to avoid "Cookie format is incorrect" error in scraper.py
            bot.cookies = []
            return False

    def check_and_save_login(self, bot, max_wait=120):
        """Check for manual login and save cookies if successful."""
        print("\n" + "=" * 60)
        print("MANUAL LOGIN CHECK")
        print("=" * 60)
        print("If you are not logged in, please log in now in the browser window.")
        print("Waiting for login (checking URL)...")
        
        start_time = time.time()
        
        while True:
            try:
                current_url = bot.driver.current_url
                # Simple check: if we are not on the login page anymore
                is_logged_in = False
                
                if self.platform == 'LINKEDIN':
                    if "login" not in current_url and "linkedin.com" in current_url:
                        is_logged_in = True
                elif self.platform == 'INSTAGRAM':
                    if "accounts/login" not in current_url and "instagram.com" in current_url:
                        is_logged_in = True
                # Add other platforms as needed
                else:
                    # Generic fallback: if url doesn't contain login
                    if "login" not in current_url:
                         is_logged_in = True

                if is_logged_in:
                    print(f"  ✓ Detected successful login! (URL: {current_url[:50]}...)")
                    bot.isLoggedIn = True
                    
                    # Save cookies
                    self.save_cookies(bot)
                    break
                
                if time.time() - start_time > max_wait:
                    print("  ⚠ Timeout waiting for login. Attempting to proceed anyway...")
                    break
                    
                time.sleep(2)
                if int(time.time() - start_time) % 10 == 0:
                     print(f"  Waiting... ({int(max_wait - (time.time() - start_time))}s remaining)")
            except Exception as e:
                print(f"  ⚠ Error checking URL: {e}")
                break

    def save_cookies(self, bot):
        """Save current cookies to database."""
        try:
            print("  Saving cookies for future runs...")
            cookies = bot.driver.get_cookies()
            expiry = datetime.now() + timedelta(days=365)
            # Use a generic username or try to extract from cookies if possible
            username = bot.username or "manual_test_user"
            
            self.session_store.insert_into_crawler_session(
                username=username,
                social=self.platform,
                cookies=cookies,
                expiry=expiry
            )
            print("  ✓ Cookies saved to database.")
        except Exception as e:
            print(f"  ⚠ Failed to save cookies: {e}")
