import random
import time
import json
import traceback
from typing import Optional, Dict, Any, List
from newAgent.src.exceptions.errors import WebDriverCustomError
from newAgent.src.robot.scraper import Bot
from newAgent.src.services.config_helper import ConfigHelper
from newAgent.src.services.schemas import INSTAGRAM_PROFILE_INFO_SCHEMA
from newAgent.src.robot.flatlay import traceback_email_flatlay
from newAgent.src.data.attributes import Attrs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, NoSuchElementException, WebDriverException
)
import mimetypes
from io import BytesIO
from time import sleep
from datetime import datetime
import urllib.request as ur
import urllib.parse
import requests
import logging
import urllib
import re
from bs4 import BeautifulSoup

# Variables
proxies = {'http': ur.getproxies().get('http'),
           'https': ur.getproxies().get('http')}

# Logging setup
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger()
# Main Execution
start_time = datetime.now()
# self.logger.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")


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


# methods

@retry
def get_image_blob(url):
    """get image binary from url"""
    res = requests.get(url=url, timeout=10, proxies=proxies)
    return res.content


# Legacy xpath_dict removed
# Legacy get_exact_number_of_post_urls removed
# Legacy extract_post_caption removed
# Legacy extract_username removed
# Legacy extract_username_from_html removed
# Legacy close_any_popup removed
# Legacy wait_for_full_load removed


class Instagram(Bot):
    base_url = ''
    login_url = ''
    profile_url = 'https://i.instagram.com/api/v1/users/web_profile_info/'
    name = 'instagram'
    session_id: str = 'sessionid'
    session_id_value: str = ''
    user_id: int
    save_login_info = False
    cookies = None
    username = ''
    full_name = ''
    profile_pic: bytes = b''
    password = ''
    logger: str = ''
    isLoggedIn = False
    pause_search = False
    result = None
    collected_user_data = []
    failed_usernames: int = 0
    
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
    duplicate_count: int = 0
    row: int = 0
    temp_users_data: list = []
    maximum_results: int = 0
    # Batch and pause settings
    SHORT_PAUSE = (3, 6)
    BATCH_PAUSE = (300, 900)

    def _has_challenge(self):
        sleep(random.uniform(Attrs.sleep_config['page_load'], Attrs.sleep_config['page_load'] + 1))
        if self.driver.current_url == self._base_url:
            return True
        elif 'challenge' in self.driver.current_url:
            traceback_email_flatlay(body=f"Found challenge via Instagram Login",
                                    image_content=self.driver.get_screenshot_as_png())
            return True
        return False

    def _has_captcha(self):
        self.driver.implicitly_wait(20)
        sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        if 'instagram.com/consent' in self.driver.current_url:
            traceback_email_flatlay(
                body=f"This isn't error, only a safety to check what is this endpoint! {self.driver.current_url}",
                use_traceback=False,
                image_content=self.driver.get_screenshot_as_png())
            # Legacy Allow All Cookies click removed
        return False

    @staticmethod
    def convert_to_list(input_string):
        if not input_string:
            return []
        # Split the string by commas and strip any leading/trailing spaces
        tokens = [token.strip() for token in input_string.split(',')]
        
        # Don't replace spaces with underscores for keyword search
        # formatted_tokens = [re.sub(r'\s+', '_', token) for token in tokens]
        
        return tokens

    def random_wait(self, min_sec: float = 2, max_sec: float = 5):
        """Wait for a random amount of time between min_sec and max_sec."""
        wait_time = random.uniform(min_sec, max_sec)
        self.logger.info(f"Waiting for {wait_time:.2f} seconds.")
        time.sleep(wait_time)

    def extract_username_from_metadata(self) -> Optional[str]:
        """
        Extract username from JSON-LD or Open Graph metadata as a robust fallback.
        
        Returns:
            Profile URL or None if not found
        """
        username = None
        html_source = self.driver.page_source
        
        # 1. Try JSON-LD Metadata
        try:
            soup = BeautifulSoup(html_source, "html.parser")
            json_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    # Navigate: author -> alternateName
                    if isinstance(data, dict) and "author" in data and "alternateName" in data["author"]:
                        username = data["author"]["alternateName"].replace("@", "")
                        self.logger.info(f"✅ Metadata Extraction: Found username '{username}' in JSON-LD")
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue
        except Exception as e:
            self.logger.warning(f"Metadata Extraction Warning (JSON-LD): {e}")

        # 2. Try Open Graph Description (Fallback)
        if not username:
            try:
                # Matches: "... - @username" or "... - username"
                og_match = re.search(r'<meta property="og:description" content=".*? - @?([^ ]+)"', html_source)
                if og_match:
                    username = og_match.group(1).rstrip('"').rstrip("'")
                    self.logger.info(f"✅ Metadata Extraction: Found username '{username}' in OG tags")
            except Exception as e:
                self.logger.warning(f"Metadata Extraction Warning (OG): {e}")

        # Final Construction
        if username:
            profile_url = f"https://www.instagram.com/{username}/"
            self.logger.info(f"✅ Metadata Extraction Success: {profile_url}")
            return profile_url
        
        self.logger.warning("❌ Metadata Extraction: No username found in metadata")
        return None

    # Legacy wait_for_full_load removed

    # Legacy close_any_popup kept as helper for collect_user_data_with_retry

    # Legacy get_exact_number_of_post_urls removed

    # Legacy extract_post_caption removed


    # Legacy extract_username removed

    # Legacy extract_username_from_html removed

    # Legacy collect_user_data_with_retry removed

    # Legacy get_user_profile removed

    # Legacy find_message_button and send_direct_message removed


    # Legacy get_followers and get_followings removed

    # Legacy profile_search removed

    # Legacy fetch_media and infer_and_generate_file_name removed

    # Legacy upload_post removed


    # Legacy process_direct_message removed


    # Legacy follow_user removed

    # Legacy extract_recent_post_elements removed

    # Legacy like_post and like_posts removed


    # Legacy comment_on_post and comment_on_posts removed


    # Legacy like_recent_posts and comment_on_recent_posts removed


    def get_user_followers(self, username: str) -> list[dict]:
        per_page: int = 50
        min_delay: float = Attrs.sleep_config['scroll_min']
        max_delay: float = Attrs.sleep_config['scroll_max']
        max_page_errors: int = 5

        base_userAgent = self.driver.execute_script("return navigator.userAgent;")

        self.logger.info(f"Starting get_user_followers for '{username}'")

        try:
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": 'Instagram 155.0.0.37.107'})
            profile_api = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
            self.driver.get(profile_api)
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
            time.sleep(random.uniform(min_delay, max_delay))
        except Exception as e:
            self.logger.error(f"Error parsing profile data for {username}: {e}")
            return []

        try:
            user = data['data']['user']
        except ValueError:
            self.logger.error(f"Invalid JSON on profile:\n{data}")
            raise
        try:
            user_id = user['id']
            self.logger.info(f"Resolved user '{username}' → ID {user_id}")

            followers = []
            has_next = True
            end_cursor = None
            page = 0
            query_hash = 'c76146de99bb02f6415203be841dd25a'

            while has_next:
                page += 1
                vars_payload = {
                    'id': user_id,
                    'include_reel': True,
                    'fetch_mutual': False,
                    'first': per_page,
                }
                if end_cursor:
                    vars_payload['after'] = end_cursor

                params = {
                    'query_hash': query_hash,
                    'variables': json.dumps(vars_payload)
                }

                attempt = 0
                while True:
                    attempt += 1
                    self.logger.debug(f"Page {page} request attempt #{attempt}")
                    try:
                        self.driver.get(f'https://www.instagram.com/graphql/query/?{urllib.parse.urlencode(params)}')
                        time.sleep(random.uniform(min_delay, max_delay))

                        data = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
                        if 'data' in data and 'user' in data['data']:
                            break
                        elif 'message' in data and data['message'] == 'Rate limit exceeded':
                            backoff = min_delay * (2 ** attempt) + random.uniform(0, 1)
                            self.logger.warning(f"Rate limit hit (HTTP 429). Backing off for {backoff:.1f}s")
                            time.sleep(backoff)
                        else:
                            self.logger.error(f"Unexpected error on page {page}: {data}")
                            if attempt >= max_page_errors:
                                self.logger.error(f"Giving up on page {page} after {attempt} attempts")
                                has_next = False
                                break
                            backoff = min_delay * attempt + random.uniform(0, 1)
                            self.logger.warning(f"Retrying page {page} in {backoff:.1f}s")
                            time.sleep(backoff)
                    except Exception as e:
                        self.logger.error(f"Error on request attempt {attempt} for page {page}: {e}")
                        break

                if 'data' not in data or 'user' not in data['data']:
                    break

                data = data['data']['user']['edge_followed_by']
                edges = data.get('edges', [])
                self.logger.info(f"Page {page} → {len(edges)} followers")

                for edge in edges:
                    node = edge['node']
                    now_ms = int(datetime.utcnow().timestamp() * 1000)
                    followers.append({
                        "updated_at": now_ms,
                        "platform": "INSTAGRAM",
                        "platform_username": node['username'],
                        "image_url": node['profile_pic_url'],
                        "url": f"https://www.instagram.com/{node['username']}/",
                        "full_name": node['full_name'],
                        "is_verified": node.get('is_verified', False),
                    })

                page_info = data.get('page_info', {})
                has_next = page_info.get('has_next_page', False)
                end_cursor = page_info.get('end_cursor')
                self.logger.info(
                    f"After page {page}: total_followers={len(followers)}, "
                    f"has_next={has_next}, next_cursor={end_cursor}"
                )

                delay = random.uniform(min_delay, max_delay)
                self.logger.debug(f"Sleeping {delay:.2f}s before next page")
                time.sleep(delay)
                self.logger.info(f"Done: retrieved {len(followers)} followers in {page} pages")
                return followers
        except Exception as e:
            self.logger.error(f"Error on request attempt {attempt} for page {page}: {e}")
            traceback_email_flatlay(
                body=f'Instagram.get_user_followers error in getring user followers: {username}\n',
                image_content=self.driver.get_screenshot_as_png())

        finally:
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": base_userAgent})

    def get_user_followings(self, username: str) -> list[dict]:
        per_page: int = 50
        min_delay: float = Attrs.sleep_config['scroll_min']
        max_delay: float = Attrs.sleep_config['scroll_max']
        max_page_errors: int = 5

        base_userAgent = self.driver.execute_script("return navigator.userAgent;")

        self.logger.info(f"Starting get_user_followings for '{username}'")

        try:
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": 'Instagram 155.0.0.37.107'})
            profile_api = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
            self.driver.get(profile_api)
            time.sleep(random.uniform(min_delay, max_delay))
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
        except Exception as e:
            self.logger.error(f"Error parsing profile data for {username}: {e}")
            return []

        try:
            user = data['data']['user']
        except ValueError:
            self.logger.error(f"Invalid JSON on profile:\n{data}")
            raise

        try:
            user_id = user['id']
            self.logger.info(f"Resolved user '{username}' → ID {user_id}")

            followings = []
            has_next = True
            end_cursor = None
            page = 0
            query_hash = 'd04b0a864b4b54837c0d870b0e77e076'

            while has_next:
                page += 1
                vars_payload = {
                    'id': user_id,
                    'include_reel': True,
                    'fetch_mutual': False,
                    'first': per_page,
                }
                if end_cursor:
                    vars_payload['after'] = end_cursor

                params = {
                    'query_hash': query_hash,
                    'variables': json.dumps(vars_payload)
                }

                attempt = 0
                while attempt < max_page_errors:
                    attempt += 1
                    self.logger.debug(f"Page {page} request attempt #{attempt}")
                    try:
                        self.driver.get(f'https://www.instagram.com/graphql/query/?{urllib.parse.urlencode(params)}')
                        time.sleep(random.uniform(min_delay, max_delay))

                        data = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
                        if 'data' in data and 'user' in data['data']:
                            break
                        elif 'message' in data and data['message'] == 'Rate limit exceeded':
                            backoff = min_delay * (2 ** attempt) + random.uniform(0, 1)
                            self.logger.warning(f"Rate limit hit (HTTP 429). Backing off for {backoff:.1f}s")
                            time.sleep(backoff)
                        else:
                            self.logger.error(f"Unexpected error on page {page}: {data}")
                            backoff = min_delay * attempt + random.uniform(0, 1)
                            self.logger.warning(f"Retrying page {page} in {backoff:.1f}s")
                            time.sleep(backoff)
                    except Exception as e:
                        self.logger.error(f"Error on request attempt {attempt} for page {page}: {e}")
                        if attempt >= max_page_errors:
                            self.logger.error(f"Giving up on page {page} after {attempt} attempts")
                            has_next = False
                            break
                        continue

                if 'data' not in data or 'user' not in data['data']:
                    break

                data = data['data']['user']['edge_follow']
                edges = data.get('edges', [])
                self.logger.info(f"Page {page} → {len(edges)} followings")

                for edge in edges:
                    node = edge['node']
                    now_ms = int(datetime.utcnow().timestamp() * 1000)
                    followings.append({
                        "updated_at": now_ms,
                        "platform": "INSTAGRAM",
                        "platform_username": node['username'],
                        "image_url": node['profile_pic_url'],
                        "url": f"https://www.instagram.com/{node['username']}/",
                        "full_name": node['full_name'],
                        "is_verified": node.get('is_verified', False),
                    })

                page_info = data.get('page_info', {})
                has_next = page_info.get('has_next_page', False)
                end_cursor = page_info.get('end_cursor')
                self.logger.info(
                    f"After page {page}: total_followings={len(followings)}, "
                    f"has_next={has_next}, next_cursor={end_cursor}"
                )

                delay = random.uniform(min_delay, max_delay)
                self.logger.debug(f"Sleeping {delay:.2f}s before next page")
                time.sleep(delay)

            self.logger.info(f"Done: retrieved {len(followings)} followings in {page} pages")
            return followings
        except Exception as e:
            self.logger.error(f"Error on request attempt {attempt} for page {page}: {e}")
            traceback_email_flatlay(
                body=f'Instagram.get_user_followers error in getring user followings: {username}\n',
                image_content=self.driver.get_screenshot_as_png())

        finally:
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": base_userAgent})

    def get_user_info(self) -> dict:
        min_delay: float = Attrs.sleep_config['scroll_min']
        max_delay: float = Attrs.sleep_config['scroll_max']
        max_page_errors: int = 5

        base_userAgent = self.driver.execute_script("return navigator.userAgent;")

        if not self.username:
             # Try to get username from current URL if it looks like a profile
             curr = self.driver.current_url
             if 'instagram.com/' in curr and '/p/' not in curr:
                  parts = curr.rstrip('/').split('/')
                  possible_user = parts[-1]
                  if possible_user not in ['home', 'explore', 'reels', 'direct', 'accounts']:
                      self.username = possible_user

        self.logger.info(f"Starting get_user_info for '{self.username}'")

        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": 'Instagram 155.0.0.37.107'})

        profile_api = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={self.username}'
        self.driver.get(profile_api)
        time.sleep(random.uniform(min_delay, max_delay))

        try:
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
        except Exception as e:
            self.logger.error(f"Error parsing profile data for {self.username}: {e}")
            return {}

        try:
            user = data['data']['user']
        except ValueError:
            self.logger.error(f"Invalid JSON on profile:\n{data}")
            raise

        try:
            user_id = user['id']
            self.logger.info(f"Fetched profile for '{user['username']}' (ID: {user_id})")

            user_data = {
                'id': user.get('id'),
                'username': user.get('username'),
                'full_name': user.get('full_name'),
                'biography': user.get('biography'),
                'profile_pic_url': user.get('profile_pic_url'),
                'is_private': user.get('is_private'),
                'is_verified': user.get('is_verified'),
                'followed_by_count': user.get('edge_followed_by', {}).get('count'),
                'following_count': user.get('edge_follow', {}).get('count'),
                'external_url': user.get('external_url'),
                'highlight_reel_count': user.get('highlight_reel_count'),
                'reel_auto_archive': user.get('reel_auto_archive'),
            }

            self.username = user.get('username')
            self.full_name = user.get('full_name')
            profile_pic_src = user.get('profile_pic_url')

            if profile_pic_src:
                response = requests.get(profile_pic_src, proxies={'http': ur.getproxies().get('http'),
                                                                  'https': ur.getproxies().get('http')})
                self.profile_pic = response.content if response.status_code == 200 else b""

            delay = random.uniform(min_delay, max_delay)
            self.logger.debug(f"Sleeping {delay:.2f}s before next action")
            time.sleep(delay)

        except Exception as e:
            self.logger.error(f"Error parsing profile data for {self.username}: {e}")
            self.username = ''
            self.full_name = ''
            self.profile_pic = b''

        finally:
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": base_userAgent})

    def text_snip(s, length=200):
        return (s[:length] + '…') if len(s) > length else s

    # Legacy like_posts_by_keyword removed


if __name__ == "__main__":
    from newAgent.src.api.APIs import RestAPI
    from newAgent.src.database.database import DataBase as SessionStore
    from newAgent.src.robot.scraper import LogWrapper
    
    store = SessionStore("WINDOWS")
    api = RestAPI("")
    instagram = Instagram('https://www.instagram.com/accounts/login/', 'WINDOWS')  # Pass the LoginURL, platform
    
    # Initialize LogWrapper
    instagram.logger = LogWrapper(logging.getLogger(instagram.name))

    crawler_data = api.get_crawler_xpath()  # GET The crawler XPath & Options from server
    instagram.set_xpath(crawler_data['crawlerXpath'][f'{instagram.name}Xpath'])  # Required
    instagram.user_agent = crawler_data["User-Agent"][instagram.name]  # Optional
    instagram.headless = crawler_data["headless"]  # Optional
    instagram.session_id = 'sessionid'  # Pass the session cookie name

    # login_result = instagram.web_driver(login_required=True)  # Login method with non-headless WebDriver
    # if not isinstance(login_result, str):
    #     exit()
    instagram.cookies = store.latest_cookies(instagram.name)
    login_result = instagram.web_driver(login_required=False)  # Automatic Login method (Default: headless = True)
    instagram.logger.info(f'Cookies is {instagram.cookies}')
    instagram.logger.info(f"Login status: {login_result}")
    if not isinstance(login_result, bool) or (isinstance(login_result, bool) and login_result is False):
        exit()
    # instagram.logger.info(f"Return Data is: {instagram.process_direct_message('hamidrezaie0')}")

    instagram_dm = [
        {
            "type": "OUTBOUND",
            "body": "Hi Futurism team! I love your content and wanted to ask if you collaborate with tech bloggers?"
        },
        {
            "type": "INBOUND",
            "body": "Hi! Thanks for reaching out. Yes, we do collaborate with tech bloggers. Please send us your portfolio."
        },
        {
            "type": "OUTBOUND",
            "body": "Thank you! Here is my portfolio: https://myblog.com/portfolio"
        },
        {
            "type": "INBOUND",
            "body": "Received, thank you. Our team will review and get back to you soon."
        }
    ]
 