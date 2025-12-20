# Packages and libraries
import random
from newAgent.src.robot.flatlay import traceback_email_flatlay
from copy import deepcopy
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import time
import logging
from random import randint as rnd
from datetime import datetime
import requests
import re
import time


# From my-files
from newAgent.src.robot.scraper import Bot
from newAgent.src.services.config_helper import ConfigHelper
from newAgent.src.services.schemas import LINKEDIN_LOGIN_SCHEMA, LINKEDIN_PROFILE_INFO_SCHEMA
from newAgent.src.robot.flatlay import traceback_email_flatlay
from newAgent.src.services.action_executor import ActionExecutor
from newAgent.src.data.attributes import Attrs


# Decorators
def retry(func):
    def wrapper(*args, **kwargs):
        i = 0
        retries = 3
        while i < retries:
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as e:
                if args and hasattr(args[0], 'logger'):
                    args[0].logger.error(f'You have and Exception at requesting to {func} {e}')
                else:
                    logging.getLogger(__name__).error(f'You have and Exception at requesting to {func} {e}')
                # traceback_email_flatlay()
                i += 1
                sleep(Attrs.sleep_config['retry_wait'])
        return False

    return wrapper



# Dictionaries
# Legacy XPaths removed


class Linkedin(Bot):
    _success_element_xpath = None
    
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
            executor = ActionExecutor(self, action, saved_item, campaign, api_client)
            result = executor.execute()
            return result
        except Exception as e:
            self.logger.error(f"Error executing action: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    name = 'linkedin'
    full_name: str = 'Unknown fullname'
    company_name: str = 'Unknown company name'
    profile_pic: bytes = b''
    session_id = 'li_at'
    keywords: list = []
    row: int = 0

    def _has_challenge(self):
        sleep(random.uniform(Attrs.sleep_config['page_load'], Attrs.sleep_config['page_load'] + Attrs.sleep_config['action_min']))
        if 'linkedin.com/feed/' not in self.driver.current_url and 'linkedin.com/in/' not in self.driver.current_url:
            return True
        return False

    @retry
    def get_image_blob(self, url):
        """get image binary from url"""
        res = requests.get(url=url, timeout=10)
        return res.content

    def login(self, username, password):
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                # Fetch Config
                config = self.config_manager.get_config(
                    social='linkedin',
                    action='login',
                    html_content=self.driver.page_source,
                    purpose="Login to LinkedIn",
                    schema=LINKEDIN_LOGIN_SCHEMA
                )

                username_xpath = ConfigHelper.get_xpath(config, 'username_input')
                password_xpath = ConfigHelper.get_xpath(config, 'password_input')
                login_btn_xpath = ConfigHelper.get_xpath(config, 'login_btn')

                # Validation and Type Conversion (ensure list for find_element)
                if username_xpath:
                    username_xpath = [username_xpath]
                
                if password_xpath:
                    password_xpath = [password_xpath]
                
                if login_btn_xpath:
                    login_btn_xpath = [login_btn_xpath]

                if not (username_xpath and password_xpath and login_btn_xpath):
                     self.logger += "Missing XPath configuration for login. Aborting.\n"
                     return False

                # Interaction
                self.logger += 'Entering username...\n'
                user_input = self.find_element(username_xpath, 10)
                user_input.clear()
                self.write_like_human(user_input, username)
                
                self.logger += 'Entering password...\n'
                pass_input = self.find_element(password_xpath, 10)
                pass_input.clear()
                self.write_like_human(pass_input, password)
                
                self.logger += 'Clicking login button...\n'
                btn = self.find_element(login_btn_xpath, 10)
                btn.click()
                
                sleep(random.uniform(Attrs.sleep_config['action_max'], Attrs.sleep_config['action_max'] + Attrs.sleep_config['action_min']))
                
                # Check success
                if not self._has_challenge():
                    self.isLoggedIn = True
                    self.logger += 'Login successful!\n'
                    return True
                else:
                    self.logger += 'Login failed or challenge required.\n'
                    # Don't return False yet, let retry handle if exception occurred, but here no exception.
                    # If challenge, maybe we should stop?
                    # For now, we consider it a failure of automation if we are stuck.
                    # But _has_challenge checks URL.
                    pass
                
                # If we are here, maybe we failed.
                if attempt == max_retries:
                    return False

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed at login: {e}")
                if attempt < max_retries - 1:
                    sleep(Attrs.sleep_config['action_min'] * 2)
                    continue
                elif attempt == max_retries - 1:
                    self.logger.error("Failed 3 times. Invalidating config.")
                    self.config_manager.invalidate_config('linkedin', 'login')
                    continue
                else:
                     self.logger += f"Login failed: {e}\n"
                     return False


    # Legacy profile_info removed

    # Legacy sending_message removed

    # Legacy search_keyword removed
    
    # Legacy profile_search removed
    
    # Legacy scroll_to_top removed

    # Legacy process_direct_message removed
    
    # Legacy comment_on_posts removed
    
    # Legacy connect_with_user removed

    # Legacy like_posts removed
    
    # Legacy like_posts_by_keyword removed


if __name__ == "__main__":
    linkedin = Linkedin('https://www.linkedin.com/login')
    linkedin.web_driver()
