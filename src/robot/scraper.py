# Packages and libraries...
from newAgent.src.robot.flatlay import traceback_email_flatlay
import random
# from selenium_stealth import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
import requests
from urllib.request import getproxies
from urllib.parse import urlparse
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoSuchWindowException, \
    WebDriverException
from time import sleep
from random import randint as rnd
import traceback
import os
import shutil
import fnmatch
import logging
import tempfile
from datetime import datetime
import subprocess
from newAgent.src.services.config_manager import ConfigManager
from newAgent.src.data.attributes import Attrs
import random

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
pyLogger = logging.getLogger()
# Main Execution
start_time = datetime.now()
pyLogger.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")


class LogWrapper:
    """A wrapper class for logging.Logger that supports += operator for string concatenation"""
    
    def __init__(self, logger):
        self._logger = logger
        self._buffer = ""
        self.callback = None
    
    def set_callback(self, callback):
        self.callback = callback

    def __iadd__(self, message):
        """Support for += operator to accumulate log messages"""
        if isinstance(message, str):
            self._buffer += message
            # Log the message immediately for real-time feedback
            if message.strip():  # Only log non-empty messages
                self._logger.info(message.rstrip('\n'))
                if self.callback:
                    try:
                        self.callback(message.rstrip('\n'))
                    except Exception:
                        pass
        return self
    
    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)
        if self.callback:
            try:
                self.callback(str(msg))
            except Exception:
                pass

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)
        if self.callback:
            try:
                self.callback(str(msg), color='orange')
            except Exception:
                pass

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)
        if self.callback:
            try:
                self.callback(str(msg), color='red')
            except Exception:
                pass
    
    def __str__(self):
        """Return the accumulated buffer as string"""
        return self._buffer
    
    def clear(self):
        """Clear the accumulated buffer"""
        self._buffer = ""
    
    def get_buffer(self):
        """Get the current buffer content"""
        return self._buffer
    
    # Delegate all other logger methods to the wrapped logger
    def __getattr__(self, name):
        return getattr(self._logger, name)


# Decorators...
def again(func):
    def wrapper(*args, **kwargs):
        arguments = list(args)
        for arg in arguments[1]:
            arguments[1] = arg
            args = tuple(arguments)
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as ex:
                print('again decorator Exception', ex)
                # traceback_email_flatlay()

    return wrapper


# Functions
def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


class ValueChangedEvent:
    """Handling Monitor status of each function
        value should be type of list or dict"""

    def __init__(self):
        self._value = None
        self._handlers = set()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if new_value != self._value:
            self._value = new_value
            for handler in self._handlers:
                if isinstance(new_value, dict):
                    handler(**new_value)
                elif isinstance(new_value, list):
                    handler(*new_value)

    def connect(self, handler):
        self._handlers.add(handler)

    def disconnect(self, handler):
        self._handlers.discard(handler)


class Bot:
    """When you want to use this class for inheritance you should assign that Three parameters:
            ~~Which They are (_username_xpath, _password_xpath, _login_btn_xpath, _success_element_xpath,
             save_login_info, headless, isLoggedIn, profile_pics_loc, search_result)~~"""
    driver = None
    cookies = None
    home_url: str = None
    _base_url: str = None
    _username_xpath = None
    _password_xpath = None
    _login_btn_xpath = None
    _success_element_xpath = None
    save_login_info = False
    headless = True
    isLoggedIn = False
    profile_pics_loc = ''
    search_result = []
    name = ''
    pause_search = False
    session_id: str = ''
    session_id_value: str = ''
    session_expiry: int
    # browsers = ['firefox', 'chrome', 'microsoftEdge', 'safari']
    version_firefox: str = ''
    version_chrome: str = ''
    browser: str = 'chrome'
    user_agent: str = ''
    profile_path: str = ''
    result = None
    function_result: str = ''
    status_results = ValueChangedEvent()  # value should be dict(row: int, text: str, color: str = None | 'green' | 'red')
    messages_limit: int = 0
    row: int = 0

    def __init__(self, url, platform: str):
        self._base_url = url
        self.platform = platform
        # Wrap logger to support '+=' usage and buffer accumulation for UI/prints
        self.logger = LogWrapper(logging.getLogger(__name__))
        self.config_manager = ConfigManager(platform=platform)

    @staticmethod
    def _delete_wdm_cache():
        try:
            home_dir = os.path.expanduser("~")
            wdm_path = os.path.join(home_dir, ".wdm")
            if os.path.exists(wdm_path):
                shutil.rmtree(wdm_path)
                return True
            else:
                return False
        except Exception as ex:
            print('Exception at _delete_wdm_cache', ex)
            traceback_email_flatlay()

    def _element_not_found(self):
        """returning True if we don't found any session cookie on specify social else returning False"""
        cookies = self.driver.get_cookie(self.session_id)
        if cookies:
            self.session_expiry = cookies.get('expiry', 1)
            self.cookies = self.driver.get_cookies()
            return False
        return True

    def _has_challenge(self):
        """returning True if social has not logged in or challenge required"""
        sleep(random.uniform(Attrs.sleep_config['page_load'] - 1, Attrs.sleep_config['page_load']))
        if self.driver.current_url == self._base_url:
            return True
        return False

    def _has_captcha(self):
        """returning True if social has captcha to solve"""
        return False

    def web_driver(self, login_required: bool = True):
        try:
            if self.browser == 'chrome':
                try:
                    # Check if Chrome is installed and get version
                    pyLogger.info("Checking Chrome installation...")
                    chrome_version = None
                    try:
                        if self.platform == 'WINDOWS':
                            import winreg
                            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                            chrome_version = winreg.QueryValueEx(key, "version")[0]
                        elif self.platform == 'MAC':
                            import subprocess
                            result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], capture_output=True, text=True)
                            chrome_version = result.stdout.strip().split()[-1]
                    except Exception as chrome_err:
                        error_msg = f"Failed to detect Chrome version: {chrome_err}"
                        pyLogger.error(error_msg)
                        traceback_email_flatlay(body=f"Chrome Detection Error:\n{error_msg}\nPlease ensure Chrome is installed.")
                        return {'title': 'Error', 'message': 'Could not detect Chrome. Please ensure Chrome is installed.'}

                    # Attempt to install ChromeDriver
                    # Using Selenium Manager (native) instead of ChromeDriverManager
                    pyLogger.info(f"Using Selenium Manager to handle ChromeDriver for Chrome version {chrome_version}...")
                except Exception as e:
                    pyLogger.warning(f"Error during Chrome version check or setup: {e}")


                try:
                    # Configure Chrome options
                    options = ChromeOptions()
                    if self.user_agent:
                        options.add_argument(f'--user-agent={self.user_agent}')
                    if self.headless and not login_required:
                        options.add_argument('--headless=new')
                    
                    # Performance optimizations for both headless and non-headless modes
                    # GPU and hardware acceleration (works in both modes)
                    options.add_argument('--enable-gpu')
                    options.add_argument('--enable-accelerated-2d-canvas')
                    options.add_argument('--enable-accelerated-video-decode')
                    options.add_argument('--enable-gpu-rasterization')
                    options.add_argument('--enable-oop-rasterization')
                    
                    # Memory and performance optimizations
                    options.add_argument('--memory-pressure-off')
                    # options.add_argument('--max_old_space_size=4096')
                    options.add_argument('--aggressive-cache-discard')
                    # options.add_argument('--enable-features=VaapiVideoDecoder')
                    
                    # Rendering optimizations
                    options.add_argument('--enable-smooth-scrolling')
                    options.add_argument('--enable-fast-unload')
                    options.add_argument('--disable-background-timer-throttling')
                    options.add_argument('--disable-renderer-backgrounding')
                    options.add_argument('--disable-backgrounding-occluded-windows')
                    
                    # Process and threading optimizations
                    # options.add_argument('--enable-site-per-process')
                    # options.add_argument('--process-per-tab')
                    # options.add_argument('--enable-threaded-compositing')
                    
                    # Headless-specific optimizations
                    if self.headless and not login_required:
                        # Additional headless performance flags
                        options.add_argument('--disable-gpu-sandbox')
                        options.add_argument('--disable-software-rasterizer')
                        options.add_argument('--disable-background-networking')
                        options.add_argument('--disable-default-apps')
                        options.add_argument('--disable-extensions')
                        options.add_argument('--disable-sync')
                        options.add_argument('--disable-translate')
                        options.add_argument('--hide-scrollbars')
                        options.add_argument('--metrics-recording-only')
                        options.add_argument('--mute-audio')
                        options.add_argument('--no-first-run')
                        options.add_argument('--safebrowsing-disable-auto-update')
                        options.add_argument('--disable-ipc-flooding-protection')
                    
                    # Common options for all modes
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--allow-running-insecure-content')
                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-notifications')
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--mute-audio")
                    options.add_argument('--no-sandbox')
                    # options.add_argument("--disable-blink-features=AutomationControlled")
                    
                    # Additional performance flags for all modes
                    options.add_argument('--disable-logging')
                    options.add_argument('--disable-default-apps')
                    options.add_argument('--disable-sync')
                    options.add_argument('--disable-translate')
                    options.add_argument('--disable-plugins-discovery')
                    options.add_argument('--disable-preconnect')
                    
                    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    # options.add_experimental_option("useAutomationExtension", False)
                    
                    # Performance preferences
                    prefs = {
                        "profile.default_content_setting_values": {
                            "notifications": 2,
                            "media_stream": 2,
                        },
                        "profile.managed_default_content_settings": {
                            "images": 1
                        }
                    }
                    options.add_experimental_option("prefs", prefs)

                    # Initialize Chrome driver with retries and cleanup
                    pyLogger.info("Initializing Chrome driver...")
                    
                    # Skipping manual permission checks as we use Selenium Manager
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            pyLogger.info(f"Attempt {attempt + 1}/{max_retries} to start ChromeDriver service...")
                            
                            # Use Selenium Manager (native)
                            self.driver = webdriver.Chrome(options=options)
                            pyLogger.info("ChromeDriver initialized successfully.")
                            break
                        except WebDriverException as wd_err:
                            pyLogger.warning(f"WebDriver initialization attempt {attempt + 1} failed: {wd_err}")
                            
                            # Kill potential zombie processes
                            if self.platform == 'MAC':
                                try:
                                    subprocess.run(['pkill', 'chromedriver'], check=False)
                                    # Avoid killing Google Chrome as it might be user's browser
                                    sleep(2)
                                except Exception:
                                    pass
                            elif self.platform == 'WINDOWS':
                                try:
                                    subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], check=False)
                                    sleep(2)
                                except Exception:
                                    pass
                                    
                            if attempt == max_retries - 1:
                                pyLogger.error("All WebDriver initialization attempts failed.")
                                raise wd_err
                            sleep(2)

                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    # Handle user agent
                    if not self.user_agent:
                        cur_ua = self.driver.execute_script('return navigator.userAgent;')
                        ua = cur_ua.replace('Headless', '')
                        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {'userAgent': ua})
                        
                except WebDriverException as wd_err:
                    error_msg = f"WebDriver initialization error after {max_retries} attempts: {wd_err}"
                    pyLogger.error(error_msg)
                    traceback_email_flatlay(body=f"ChromeDriver Initialization Error:\n{error_msg}")
                    
                    # Try to clean up WebDriver Manager cache
                    if self._delete_wdm_cache():
                        return {'title': 'Warning', 'message': 'Your web driver is on old version\nplease try again to update and log in.'}
                    else:
                        return {'title': 'Error', 'message': 'ChromeDriver version.\nError: No path '}
                    
                except Exception as init_err:
                    error_msg = f"Unexpected error during Chrome initialization: {init_err}\n{traceback.format_exc()}"
                    pyLogger.error(error_msg)
                    traceback_email_flatlay(body=f"Chrome Initialization Error:\n{error_msg}")
                    return {'title': 'Error', 'message': f'Failed to initialize Chrome: {init_err}'}

            self.driver.implicitly_wait(20)
            self.driver.maximize_window()
            self.driver.implicitly_wait(4)
            self.driver.get(self._base_url)
            self.driver.implicitly_wait(15)
            if login_required:
                timeout = 300 * 1000
                while self._element_not_found():
                    timeout -= 1
                    if timeout <= 0:
                        traceback_email_flatlay(body=f"Timeout reached on {self.name} login\n",
                                                image_content=self.driver.get_screenshot_as_png())
                        self.logout()
                        return {'title': 'Error', 'message': "Timeout reached!"}
                    sleep(Attrs.sleep_config['retry_wait'])
                # self.logout()
                return 'save_user'
            self.add_cookies()
            self.driver.implicitly_wait(20)
            sleep(random.uniform(Attrs.sleep_config['action_max'], Attrs.sleep_config['page_load']))
            try:
                cur_url = self.driver.current_url
                parsed = urlparse(cur_url) if cur_url else None
                pyLogger.debug(f"Current URL host: {parsed.netloc if parsed else ''}")
            except Exception:
                pass
            if self._has_challenge():
                self.logout()
                return 'expired challenge'
            if self._has_captcha():
                self.logout()
                return 'expired captcha'
            self.isLoggedIn = True
            # Printing Current User-Agent
            try:
                ua = self.driver.execute_script("return navigator.userAgent;")
                pyLogger.debug(f"User-Agent length: {len(ua) if ua else 0}")
            except Exception as user_agent_err:
                _ = user_agent_err
            return True
        except NoSuchWindowException:
            self.logout()
            # traceback_email_flatlay()
            return {'title': 'Error', 'message': 'Browser Closed'}
        except (WebDriverException, TimeoutException) as e:
            pyLogger.error(f"WebDriver/Timeout Exception in web_driver: {e}")
            pyLogger.error(traceback.format_exc())
            self.logout()
            return {'title': 'Error', 'message': "The site can't be reached!\n"
                                                 "please check your internet speed or proxy server."}

        except Exception as ex:
            pyLogger.error(f"General Exception in web_driver: {ex}")
            pyLogger.error(traceback.format_exc())
            self.logout()
            traceback_email_flatlay()
            self.logger += f'Exception on web_driver() {ex}'
            return {'title': 'Error', 'message': f'Something went wrong.\nError: {ex}'}

    @again
    def find_element(self, element, timeout=20, rand_off=True, ret_locator=False, poll_frequency: float = 0.5):
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        ret = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency).until(
            EC.presence_of_element_located((By.XPATH, element)))
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        if ret_locator:
            return ret, element
        return ret

    @again
    def find_elements(self, element, timeout=20, rand_off=True, ret_locator=False, poll_frequency: float = 0.5):
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        ret = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency).until(
            EC.presence_of_all_elements_located((By.XPATH, element)))
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        if ret_locator:
            return ret, element
        return ret

    @again
    def find_element_clickable(self, element, timeout=20, rand_off=True, ret_locator=False,
                               poll_frequency: float = 0.5):
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        ret = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency).until(
            EC.element_to_be_clickable((By.XPATH, element))).click()
        if rand_off:
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['typing_max']))
        else:
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        if ret_locator:
            return ret, element
        return ret

    def try_xpath_single(self, xpath_list, base_xpath=None, attribute=None, timeout=5, debug_on_failure=False):
        """
        Try to find an element using a list of XPath selectors.
        Returns the text content or specified attribute of the first matching element.
        
        Args:
            xpath_list: List of XPath selectors to try
            base_xpath: Base XPath to prepend to each selector (optional)
            attribute: Attribute to extract instead of text (optional)
            timeout: Timeout for each XPath attempt
            debug_on_failure: Whether to run debug analysis if all XPaths fail
            
        Returns:
            String value of the element's text or attribute, or None if not found
        """
        if isinstance(xpath_list, str):
            xpath_list = [xpath_list]
        
        failed_xpaths = []
        
        for i, xpath in enumerate(xpath_list):
            try:
                # Combine base_xpath with current xpath if provided
                full_xpath = f"{base_xpath}{xpath}" if base_xpath else xpath
                
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, full_xpath))
                )
                
                # Log successful XPath if it wasn't the first one
                if i > 0:
                    pyLogger.info(f"✅ XPath found on attempt {i+1}/{len(xpath_list)}: {full_xpath}")
                
                if attribute:
                    result = element.get_attribute(attribute)
                    if result is None:
                        pyLogger.debug(f"📄 Extracted attribute '{attribute}': <none>")
                    elif isinstance(result, str):
                        pyLogger.debug(f"📄 Extracted attribute '{attribute}': {len(result)} chars")
                    else:
                        pyLogger.debug(f"📄 Extracted attribute '{attribute}': {type(result).__name__}")
                    return result
                else:
                    result = element.text.strip() if element.text else None
                    if result is None:
                        pyLogger.debug("📄 Extracted text: <none>")
                    else:
                        pyLogger.debug(f"📄 Extracted text: {len(result)} chars")
                    return result
                    
            except (NoSuchElementException, TimeoutException) as e:
                full_xpath = f"{base_xpath}{xpath}" if base_xpath else xpath
                failed_xpaths.append({
                    'xpath': full_xpath,
                    'error': type(e).__name__,
                    'attempt': i + 1
                })
                pyLogger.debug(f"❌ XPath attempt {i+1}/{len(xpath_list)} failed ({type(e).__name__}): {full_xpath}")
                continue
            except Exception as e:
                full_xpath = f"{base_xpath}{xpath}" if base_xpath else xpath
                failed_xpaths.append({
                    'xpath': full_xpath,
                    'error': f"{type(e).__name__}: {str(e)}",
                    'attempt': i + 1
                })
                pyLogger.warning(f"⚠️ XPath attempt {i+1}/{len(xpath_list)} failed with unexpected error: {full_xpath} - {type(e).__name__}: {str(e)}")
                continue
        
        # Log summary of all failed attempts
        if failed_xpaths:
            pyLogger.warning(f"🔍 All {len(failed_xpaths)} XPath attempts failed:")
            for failed in failed_xpaths:
                pyLogger.warning(f"   Attempt {failed['attempt']}: {failed['xpath']} ({failed['error']})")
            
            # Additional context logging
            try:
                current_url = self.driver.current_url
                page_title = self.driver.title
                parsed = urlparse(current_url) if current_url else None
                pyLogger.info(f"📍 Current page: {page_title} ({parsed.netloc if parsed else ''})")
            except Exception:
                pyLogger.debug("Could not retrieve current page information")
            
            # Run debug analysis if requested
            if debug_on_failure:
                pyLogger.info("🔧 Running detailed XPath debug analysis...")
                self.debug_xpath_elements(xpath_list, base_xpath)
        
        return None

    def debug_xpath_elements(self, xpath_list, base_xpath=None, max_elements=5):
        """
        Debug helper method to analyze what elements are available on the page
        when XPath selectors fail to find the expected elements.
        
        Args:
            xpath_list: List of XPath selectors that failed
            base_xpath: Base XPath that was used (optional)
            max_elements: Maximum number of similar elements to log
            
        Returns:
            Dictionary with debugging information
        """
        debug_info = {
            'page_url': None,
            'page_title': None,
            'similar_elements': [],
            'page_source_snippet': None
        }
        
        try:
            debug_info['page_url'] = self.driver.current_url
            debug_info['page_title'] = self.driver.title
            
            pyLogger.info(f"🔍 XPath Debug Analysis for page: {debug_info['page_title']}")
            try:
                parsed = urlparse(debug_info['page_url']) if debug_info['page_url'] else None
                pyLogger.info(f"🔗 URL host: {parsed.netloc if parsed else ''}")
            except Exception:
                pyLogger.info("🔗 URL host: ")
            
            # Try to find similar elements using broader selectors
            if isinstance(xpath_list, str):
                xpath_list = [xpath_list]
                
            for i, xpath in enumerate(xpath_list):
                full_xpath = f"{base_xpath}{xpath}" if base_xpath else xpath
                pyLogger.info(f"🔍 Analyzing failed XPath {i+1}: {full_xpath}")
                
                # Try to find elements with similar patterns
                try:
                    # Extract tag name from XPath if possible
                    if '//' in xpath and '[' in xpath:
                        tag_part = xpath.split('//')[1].split('[')[0] if '//' in xpath else xpath.split('[')[0]
                        if tag_part:
                            similar_xpath = f"//{tag_part}"
                            similar_elements = self.driver.find_elements(By.XPATH, similar_xpath)
                            
                            pyLogger.info(f"📊 Found {len(similar_elements)} similar '{tag_part}' elements on page")
                            
                            for j, elem in enumerate(similar_elements[:max_elements]):
                                try:
                                    elem_info = {
                                        'tag': elem.tag_name,
                                        'text_length': len(elem.text) if elem.text else 0,
                                        'classes': elem.get_attribute('class'),
                                        'id': elem.get_attribute('id'),
                                        'visible': elem.is_displayed()
                                    }
                                    debug_info['similar_elements'].append(elem_info)
                                    pyLogger.info(f"   Element {j+1}: {elem_info}")
                                except Exception as elem_ex:
                                    pyLogger.debug(f"   Could not analyze element {j+1}: {elem_ex}")
                                    
                except Exception as similar_ex:
                    pyLogger.debug(f"Could not find similar elements: {similar_ex}")
            
            # Get a snippet of page source for manual inspection
            try:
                page_source = self.driver.page_source
                debug_info['page_source_snippet'] = None
                pyLogger.debug(f"📄 Page source length: {len(page_source) if page_source else 0} chars")
            except Exception as source_ex:
                pyLogger.debug(f"Could not retrieve page source: {source_ex}")
                
        except Exception as debug_ex:
            pyLogger.warning(f"XPath debug analysis failed: {debug_ex}")
            
        return debug_info

    def check_google_captcha(self):
        try:
            captcha = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//form[contains (@id, "captcha")]')))
            if captcha:
                print('Captcha Element has been found')
                captcha.click()
                print('Captcha Element has been clicked')
            self.driver.implicitly_wait(4)
            sleep(random.uniform(Attrs.sleep_config['action_max'], Attrs.sleep_config['page_load']))
        except NoSuchElementException:
            pass
        sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        try:
            self.driver.switch_to.frame(self.driver.find_elements(By.TAG_NAME, "iframe")[0])
            check_box = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
            check_box.click()
            sleep(random.uniform(Attrs.sleep_config['action_min'], Attrs.sleep_config['action_max']))
        except TimeoutException:
            pass
        except Exception as ex:
            print(ex)
            traceback_email_flatlay()

    @staticmethod
    def _convert_M_K_to_num(value: str) -> int:
        try:
            value = value.replace(',', '')
            str_to_int = {'K': int(float(value[:-1]) * 1000),
                          'M': int(float(value[:-1]) * 1_000_000)}
            value = str_to_int.get(value[-1]) if str_to_int.get(
                value[-1]) is not None \
                else int(value)
        except Exception as ex:
            _ = f'Exception on _convert_M_K_to_num {ex}'
            value = int(value)
        finally:
            return value

    def driver_get(self, driver, url, adding_cookie: bool = False):
        driver.get(url)
        if adding_cookie:
            self.add_cookies()
        driver.implicitly_wait(6)
        self.check_google_captcha()

    def get_cookies(self):
        cookies = self.driver.get_cookies()
        # If You want to save cookies in file Uncomment this below...

        # pickle.dump(self.cookies, open('cookies.txt', 'wb'))
        return cookies

    def add_cookies(self):
        if isinstance(self.cookies, list):
            for cookie in self.cookies:
                self.driver.add_cookie(cookie)
                sleep(0.001)
            self.driver.refresh()
        elif isinstance(self.cookies, dict):
            self.driver.add_cookie(self.cookies)
            self.driver.refresh()
        else:
            raise Exception('Cookie format is incorrect please re login again.')

        try:
            pyLogger.debug(f"Cookies in driver: {len(self.driver.get_cookies())}")
        except Exception:
            pass

    def write_like_human(self, element, text, mistake_probability=0.05):
        try:
            for char in text:
                element.send_keys(char)
                sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['action_min']))

                # Occasionally make a mistake
                if random.random() < mistake_probability:
                    # Type a random wrong character
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    element.send_keys(wrong_char)
                    sleep(random.uniform(Attrs.sleep_config['typing_min'] / 10, Attrs.sleep_config['typing_min']))

                    # Backspace to correct it
                    backspaces = random.randint(1, 3)
                    for _ in range(backspaces):
                        element.send_keys(Keys.BACKSPACE)
                        sleep(random.uniform(Attrs.sleep_config['typing_min'] / 10, Attrs.sleep_config['typing_min']))

                    # Retype the correct character
                    element.send_keys(char)
                    sleep(random.uniform(Attrs.sleep_config['typing_min'] / 10, Attrs.sleep_config['typing_min']))

            sleep(random.uniform(Attrs.sleep_config['action_max'], Attrs.sleep_config['page_load']))
        except Exception as ex:
            pyLogger.error(f"write_like_human failed: {type(ex).__name__}")
            self.logger += f'Write like human failed {ex}'

    def non_bmp_bypass(self, input_element, text: str, remove_newlines: bool = False):
        try:
            action = ActionChains(self.driver)
            sleep(random.uniform(Attrs.sleep_config['typing_min'], Attrs.sleep_config['action_min']))
            action.click(input_element)
            if remove_newlines:
                for char in text.replace('\n', ' '):
                    action.send_keys(char)
                    sleep(random.uniform(Attrs.sleep_config['typing_min'] / 10, Attrs.sleep_config['typing_min']))
                action.perform()
            else:
                for char in text:
                    if char == '\n':
                        action.key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(
                            Keys.ENTER).key_up(Keys.SHIFT)
                    else:
                        action.send_keys(char)
                    sleep(random.uniform(Attrs.sleep_config['typing_min'] / 10, Attrs.sleep_config['typing_min']))
                action.perform()

        except Exception as ex:
            print('Exception at non_bmp_bypass', ex)
            self.logger += f'non_bmp_bypass failed {ex}\n'
            traceback_email_flatlay()

    @staticmethod
    def _remove_temp_file(temp_file_path: str):
        """This method will delete the temp_file that you created earlier"""
        pyLogger.info(f'Deleting the temp_file: {temp_file_path} ...')
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                pyLogger.info(f'{temp_file_path} has been deleted successfully')
            except OSError as os_err:
                pyLogger.error(msg := f"OSError: Unable to delete the temporary file {temp_file_path}: {os_err}")
                traceback_email_flatlay(body=f"{msg}\n")
            except Exception as err:
                pyLogger.error(msg := f"An unexpected error occurred while deleting the file: {err}")
                traceback_email_flatlay(body=f"{msg}\n")
        else:
            pyLogger.warning('No such temp_file detected!')

    def _remove_temp_files(self, temp_file_paths: list):
        """This method will delete the temp_files that you created earlier"""
        for temp_file_path in temp_file_paths:
            self._remove_temp_file(temp_file_path=temp_file_path)

    def _requests_for_media_and_create_temp(self,
                                            media_url: str
                                            # Media Url path accept image/jpeg,image/png,image/heic,image/heif,video/mp4
                                            ) -> str:
        """ ***NOTE: Before using this method make sure you used these except classes for error handling -> :
                    1-requests.exceptions.ProxyError,
                    2-requests.exceptions.ConnectionError,
                    3-requests.exceptions.SSLError,
                    4-requests.exceptions.Timeout,
                    5-requests.exceptions.RequestException,
                    6-OSError
                    Also on the end of your method make sure you'll delete the temp_file using _remove_temp_file method***"""
        media = requests.get(media_url, proxies={'http': getproxies().get('http'),
                                                 'https': getproxies().get('http')})
        media.raise_for_status()
        content_type = media.headers.get("Content-Type", "application/octet-stream")  # Fallback if None
        ext_map = {
            "video/quicktime": "mov",
            "video/mp4": "mp4",
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/heic": "heic",
            "image/heif": "heif"
        }
        suffix = f".{ext_map.get(content_type, content_type.split('/')[-1] if '/' in content_type else 'bin')}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Write the binary content to the temporary file
            temp_file.write(media.content)

            temp_file_path = temp_file.name  # Get the path of the temporary file
        # Check if temp_file_path is also empty and the media size required
        if not temp_file_path:
            raise OSError(f"Temporary file path is None. media.status_code_response={media.status_code}")
        elif os.path.getsize(temp_file_path) < 5576:
            self._remove_temp_file(temp_file_path)
            raise OSError(f"The media size is too small")
        return temp_file_path

    def logout(self):
        try:
            self.isLoggedIn = False
            self.logger = ''
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as ex:
            print('Exception at Bot.logout()', ex)
            traceback_email_flatlay()


if __name__ == '__main__':
    bot = Bot('http://tiktok.com/login/phone-or-email/email', 'WINDOWS')
    bot.browser = 'chrome'
    bot.session_id = 'sessionid'
    print(bot.profile_path)
    bot.user_agent = ''
    bot.web_driver(login_required=True)
    user_agent = bot.driver.execute_script("return navigator.userAgent;")
    print('User Agent', user_agent)
    # bot.login('asdkjasd', 'asdjhad')
    sleep(Attrs.sleep_config['long_wait'])
