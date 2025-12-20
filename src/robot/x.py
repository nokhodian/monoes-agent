import logging
import time
from datetime import datetime
import random
import re
import urllib.request as ur
import requests

from newAgent.src.data.attributes import Attrs
from newAgent.src.robot.flatlay import traceback_email_flatlay
from newAgent.src.robot.scraper import Bot
from newAgent.src.services.config_helper import ConfigHelper
from newAgent.src.services.schemas import X_PROFILE_INFO_SCHEMA, X_FOLLOWERS_SCHEMA
from io import BytesIO
import mimetypes
from urllib.parse import quote_plus
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, \
    ElementClickInterceptedException


class X(Bot):
    home_url = 'https://x.com/home'
    name = 'x'
    session_id: str = 'auth_token'
    session_id_value: str = ''
    username = ''
    full_name = ''
    password = ''
    profile_pic: bytes = b''
    log_messages: str = ''
    isLoggedIn = False
    pause_search = False
    result = None
    failed_direct_message_users = []
    counter = 0
    
    def execute_action(self, action, saved_item=None, campaign=None, api_client=None):
        """
        Execute an action using JSON-based action definitions.
        
        Args:
            action: Action object
            saved_item: Optional SavedItem for iteration context
            campaign: Optional Campaign object
            api_client: Optional API client for saving data
            
        Returns:
            Execution result dictionary
        """
        try:
            from newAgent.src.services.action_executor import ActionExecutor
            executor = ActionExecutor(self, action, saved_item, campaign, api_client)
            result = executor.execute()
            return result
        except Exception as e:
            self.log_messages += f"Error executing action: {e}\n"
            return {'success': False, 'error': str(e)}

    def _has_challenge(self):
        self.random_wait(Attrs.sleep_config['typing_max'], Attrs.sleep_config['action_min'])
        self.driver.get(self.home_url)
        self.driver.implicitly_wait(20)
        self.random_wait(Attrs.sleep_config['action_max'], Attrs.sleep_config['page_load'])
        if 'x.com/home' not in self.driver.current_url:
            return True
        if not self.driver.get_cookie('d_prefs'):
            btn_accept_cookies = self.find_element(['//button[contains(*, "cookies") and contains(*, "ccept")]',
                                                    '//*[text()="Accept all cookies"]//ancestor::button',
                                                    '//*[text()="Accept all cookies"]'], 5)
            self.random_wait(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max'])
            if btn_accept_cookies:
                self.driver.execute_script('arguments[0].click();', btn_accept_cookies)
                self.logger.info("X Cookies Accepted!")
        return False

    @staticmethod
    def convert_to_list(input_string):
        # Split the string by commas and strip any leading/trailing spaces
        tokens = [token.strip() for token in input_string.split(',')]

        # Replace spaces with underscores and ensure proper formatting
        formatted_tokens = [re.sub(r'\s+', '_', token) for token in tokens]

        return formatted_tokens

    # Legacy get_user_profile removed


    # Legacy collect_tweet_data removed


    # Legacy search_keyword removed


    # Legacy check_for_retry_button removed

    # Legacy navigate_to_user_profile removed

    # Legacy click_message_button removed

    # Legacy send_message removed

    # Legacy send_direct_message removed

    # Legacy profile_search removed

    # Legacy fetch_media removed

    # Legacy infer_and_generate_file_name removed

    # Legacy post_media removed


    # Legacy process_direct_message removed


    # Legacy comment_on_posts removed


    # Legacy like_posts removed


    # Legacy pull_followers removed

    # Legacy pull_following removed


    # Legacy follow_user removed


    # Legacy like_posts_by_keyword removed



if __name__ == "__main__":
    from newAgent.src.api.APIs import RestAPI
    from newAgent.src.database.database import DataBase as SessionStore

    store = SessionStore("WINDOWS")

    api = RestAPI("")
    x: X = X('https://x.com/i/flow/login', "WINDOWS")
    # Pass the LoginURL, platform

    crawler_data = api.get_crawler_xpath()  # GET The crawler XPath & Options from server
    x.user_agent = crawler_data["User-Agent"][x.name]  # Optional
    x.headless = False
    x.session_id = 'sessionid'  # Pass the session cookie name

 
    x.cookies = store.latest_cookies(x.name)
    login_result = x.web_driver(login_required=False)  # Automatic Login method (Default: headless = True)
    try:
        cookie_container = x.cookies[0] if isinstance(x.cookies, tuple) and x.cookies else x.cookies
        cookie_count = len(cookie_container) if isinstance(cookie_container, (list, dict)) else 0
        x.logger.info(f"Cookies loaded: {cookie_count}")
    except Exception:
        x.logger.info("Cookies loaded")
    x.logger.info(f"Login status: {login_result}")
    if not isinstance(login_result, bool) or (isinstance(login_result, bool) and login_result is False):
        exit()
    x.logger.info(f"Return Data is: {x.send_direct_message('OtakuCursed2', 'Hello otaku!')}")  # This can be replaced by each method of this social media class
    time.sleep(10 ** 5)
    # print("")
