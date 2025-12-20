# Packages and libraries...
from newAgent.src.robot.flatlay import traceback_email_flatlay
from newAgent.src.services.config_helper import ConfigHelper
from newAgent.src.services.schemas import TIKTOK_PROFILE_INFO_SCHEMA
from newAgent.src.data.attributes import Attrs
from time import sleep
from datetime import datetime
from random import randint as rnd
import random
import re
import requests
import logging
import time
from io import BytesIO
import mimetypes
from urllib.request import getproxies
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
# from bs4 import BeautifulSoup


# From my-files...
from newAgent.src.robot.scraper import Bot


# Variables

# Decorators..
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
                    args[0].logger.error(f'You have an Exception at requesting to {func} {e}')
                else:
                    logging.getLogger(__name__).error(f'You have an Exception at requesting to {func} {e}')
                # traceback_email_flatlay()
                i += 1
                sleep(Attrs.sleep_config['retry_wait'])
        return False

    return wrapper




# Dictionaries...
# Legacy XPaths removed



class Tiktok(Bot):
    # Inheritance properties...
    _success_element_xpath = None
    # This class properties...
    name = 'tiktok'
    username: str = 'Unknown username'
    full_name: str = 'Unknown name'
    followers_count: int = None
    profile_pic: bytes = b''
    logger: str = ''
    session_id = 'sessionid'
    
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
            self.logger += f"Error executing action: {e}\n"
            return {'success': False, 'error': str(e)}

# Legacy set_xpath removed


# Legacy _has_captcha removed


# Legacy profile_info removed


# Legacy sending_message removed


# Legacy extract_profile_links removed


# Legacy get_tiktok_post_urls removed


# Legacy search_keyword removed

# Legacy profile_search removed


# Legacy get_followers removed


    # Legacy fetch_media and infer_and_generate_file_name removed

    # Legacy format_and_round_time removed

    # Legacy scroll_to_bottom removed


    # Legacy scroll_to_hour, scroll_to_minute, set_time, post_media removed
    # Legacy scroll_to_minute (remainder), set_time, random_wait, post_media removed

    # Legacy methods (process_direct_message, pull_following, pull_followers, follow_user, like_posts, comment_posts, like_posts_by_keyword) removed


    def get_user_info(self):
        try:
            config = self.config_manager.get_config(
                social='tiktok',
                action='profile_info',
                html_content=self.driver.page_source,
                purpose="Extract profile info",
                schema=TIKTOK_PROFILE_INFO_SCHEMA
            )
            
            self.username = ConfigHelper.get_text(config, 'username') or self.username
            self.full_name = ConfigHelper.get_text(config, 'full_name') or self.full_name
            self.followers_count = ConfigHelper.get_text(config, 'followers_count')
            
            profile_pic_src = ConfigHelper.get_attribute(config, 'profile_pic', 'src')
            if profile_pic_src:
                # Need to implement get_image_blob or use requests
                try:
                    res = requests.get(url=profile_pic_src, timeout=10)
                    self.profile_pic = res.content
                except:
                    pass
            
            return {
                'username': self.username,
                'full_name': self.full_name,
                'followers_count': self.followers_count,
                'profile_pic': self.profile_pic
            }
        except Exception as e:
            self.logger += f"Error getting user info: {e}\n"
            return {}


if __name__ == "__main__":
    tiktok = Tiktok('http://tiktok.com/login/phone-or-email/email', 'WINDOWS')
    tiktok.browser = 'firefox'
    # tiktok.set_xpath()
    tiktok.headless = False
    login_result = tiktok.web_driver()
    # tiktok.profile_info()
    if isinstance(login_result, str):
        tiktok.logger.error(f"Error: {login_result}")
    elif isinstance(login_result, bool):
        tiktok.logger.info(f'Login Successful: {login_result}')
        sleep(3)
        tiktok.logger.info(tiktok.driver.current_url)
    else:
        tiktok.logger.error(f'Something went wrong at login into {tiktok.name}')
    # sleep(60)
    # print(tiktok.search_keyword('NFTGaming, BlockChainGames', 30, 0))
    # tiktok.logger.info(tiktok.get_followers())
    # tiktok.logger.info(tiktok.logger)
# site:tiktok.com/@ -inurl:video -inurl:photo AND ("@gmail.com" OR "@hotmail.com" OR "@yandex.ru" OR "@icloud.com" OR "@yahoo.com" ) "flat lay"
