# import traceback
from newAgent.src.robot.flatlay import FlatLay, traceback_email_flatlay, regenerate_token
from newAgent.src.data.attributes import Attrs
import requests
import json
from time import sleep
import urllib.request
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
# Main Execution
start_time = datetime.now()


# logger.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")


# Decorators..
def retry(func):
    def wrapper(*args, **kwargs):
        i = 0
        retries = 10
        while i < retries:
            response = None
            data_type = None
            try:
                response = func(*args, **kwargs)
                if isinstance(response, tuple):
                    response, data_type = response
                response.raise_for_status()
                if data_type and data_type == bytes:
                    ret = response.content
                else:
                    ret = json.loads(response.text)
                return ret

            except (requests.exceptions.ProxyError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.SSLError):
                logger.error('Network Failure at the requesting sleep for 12 seconds')
                sleep(Attrs.sleep_config['page_load'])
                # traceback.print_exc()
            except requests.exceptions.Timeout:
                logger.error('Timeout Exception while requesting')
                sleep(Attrs.sleep_config['retry_wait'])
            except requests.exceptions.HTTPError as h_err:
                if response.status_code == 401:
                    logger.warning('UnAuthorized Status code trying to regenerate token...')
                    id_token = regenerate_token()
                    if id_token:
                        RestAPI.set_authorization(id_token)
                    else:
                        logger.error(f'An error occurred on regenerating token {id_token}')
                else:
                    try:
                        if 'done' in json.loads(response.text).get('message').lower():
                            return json.loads(response.text)
                    except Exception as err:
                        logger.error(f"Couldn't JSON parse the response {err}")
                    response_text = getattr(response, "text", None)
                    response_len = len(response_text) if isinstance(response_text, str) else 0
                    logger.warning(
                        f'HTTP Error with status code: {response.status_code}\nResponseLength: {response_len}\nerror_message: {h_err}')
                    traceback_email_flatlay(
                        body=f'HTTP Error with status code: {response.status_code}\nResponseLength: {response_len}\nerror_message: {h_err}')
            except requests.exceptions.RequestException as r_err:
                logger.error(f'An Error occurred while request {r_err}')
                traceback_email_flatlay(body=f"An RequestException Error occurred while requesting {r_err}")
            except Exception as ex:
                logger.error(f'You have and Exception at requesting to: {ex}')
                traceback_email_flatlay(body=f"UnExpected Error occurred while requesting {ex}")
            finally:
                i += 1
                sleep(Attrs.sleep_config['retry_wait'])

    return wrapper


class RestAPI:
    timeout: int = 300
    _auth_header: dict = {"Authorization": "",
                          "Cache-Control": "no-cache"}
    _flatlay_api_url: str = 'https://api.flatlay.io/campaign'
    _flatlay_v2_api_url: str = 'https://apiv2.flatlay.io/%s'
    # _monoes_api_url: str = 'https://api.monoes.me/rest/%s'  # Deprecated. Prefer _monoes_dash_api_url.
    _monoes_dash_api_url: str = 'https://monoes.me/rest/%s'
    _session = requests.session()
    _session.trust_env = False
    id_token: str = ""

    def __init__(self, id_token):
        RestAPI.id_token = id_token
        RestAPI.set_authorization(id_token)

    @staticmethod
    def map_new_person_to_legacy(person):
        legacy = {
            "id": person.get("id"),
            "name": f"{person.get('name', {}).get('firstName', '')} {person.get('name', {}).get('lastName', '')}".strip(),
            "first_name": person.get("name", {}).get("firstName"),
            "last_name": person.get("name", {}).get("lastName"),
            "email": person.get("emails", {}).get("primaryEmail"),
            "phone": person.get("phones", {}).get("primaryPhoneNumber"),
            "city": person.get("city"),
            "avatar": person.get("avatarUrl"),
            "position": person.get("position"),
            "created_at": person.get("createdAt"),
            "updated_at": person.get("updatedAt"),
            "company_id": person.get("companyId"),
            "created_by": person.get("createdBy", {}).get("name"),
            "platforms": []
        }
        # Map social platforms
        for platform in ["insta", "tiktok", "x", "linkedin"]:
            entry = {}
            if platform == "linkedin":
                entry["platform"] = "LINKEDIN"
                entry["url"] = person.get("linkedinLink", {}).get("primaryLinkUrl")
                entry["category"] = None
                entry["introduction"] = person.get("linkedinIntro")
                entry["is_verified"] = None
                entry["follower_count"] = person.get("linkedinFollowerCount")
                entry["position"] = person.get("linkedinPosition")
            else:
                entry["platform"] = platform.upper()
                entry["url"] = person.get(f"{platform}Link")
                entry["category"] = person.get(f"{platform}Category")
                entry["introduction"] = person.get(f"{platform}Intro")
                entry["is_verified"] = person.get(f"{platform}IsVerified")
                entry["follower_count"] = person.get(f"{platform}FollowerCount")
            if any(entry.get(k) for k in ["url", "introduction", "follower_count"]):
                legacy["platforms"].append(entry)
        # Add additional emails/phones if present
        legacy["additional_emails"] = person.get("emails", {}).get("additionalEmails")
        legacy["additional_phones"] = person.get("phones", {}).get("additionalPhones")
        legacy["job_title"] = person.get("jobTitle")
        legacy["search_vector"] = person.get("searchVector")
        legacy["deleted_at"] = person.get("deletedAt")
        # Flatten company fields if present
        company = person.get("company", {})
        if company:
            legacy["company_name"] = company.get("name")
            legacy["company_domain"] = company.get("domainName", {}).get("primaryLinkUrl")
            legacy["company_employees"] = company.get("employees")
            legacy["company_linkedin"] = company.get("linkedinLink", {}).get("primaryLinkUrl")
            legacy["company_x"] = company.get("xLink", {}).get("primaryLinkUrl")
            legacy["company_annual_revenue"] = company.get("annualRecurringRevenue", {}).get("amountMicros")
            legacy["company_annual_revenue_currency"] = company.get("annualRecurringRevenue", {}).get("currencyCode")
            legacy["company_address"] = company.get("address")
            legacy["company_ideal_customer_profile"] = company.get("idealCustomerProfile")
            legacy["company_position"] = company.get("position")
            legacy["company_created_by"] = company.get("createdBy", {}).get("name")
            legacy["company_created_at"] = company.get("createdAt")
            legacy["company_updated_at"] = company.get("updatedAt")
            legacy["company_deleted_at"] = company.get("deletedAt")
            legacy["company_account_owner_id"] = company.get("accountOwnerId")
            legacy["company_id"] = company.get("id")
        # Map related lists if present
        for key in [
            "taskTargets", "noteTargets", "actionTargets", "favorites", "attachments",
            "pointOfContactForOpportunities", "messageParticipants", "calendarEventParticipants", "timelineActivities"
        ]:
            if person.get(key) is not None:
                legacy[key] = person.get(key)
        legacy["_raw"] = person
        return legacy

    @staticmethod
    def set_authorization(token: str):
        RestAPI.id_token = token
        # Check if token is Bearer token or old token format
        clean_token = token.replace('Bearer ', '') if token.startswith('Bearer ') else token
        
        if token.startswith('Bearer '):
            RestAPI._auth_header['Authorization'] = token
        else:
            RestAPI._auth_header['Authorization'] = f'Bearer {token}'
            
        # Sync with FlatLay
        try:
            FlatLay.auth(clean_token)
        except Exception as e:
            logger.error(f"Error syncing with FlatLay: {e}")

    @classmethod
    def get_campaigns(cls):
        """
        DISABLED: Returns mock data for testing actions list only
        """
        print("MOCK: get_campaigns() - returning mock response (campaign API disabled)")
        # Return the structure the rest of the code expects: a dict with a 'campaigns' list
        return {
            "campaigns": [],
            "message": "Mock response - campaigns disabled for testing"
        }

    @classmethod
    def get_merchant_quotas(cls):
        """
        DISABLED: Returns mock data for testing actions list only
        """
        print("MOCK: get_merchant_quotas() - returning mock response")
        # Create a mock response object
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"data": {"quotas": {"instagram": {"used": 0, "limit": 100}, "facebook": {"used": 0, "limit": 100}, "twitter": {"used": 0, "limit": 100}}}, "message": "Mock response - quotas disabled for testing"}'
            def json(self):
                return {
                    "data": {
                        "quotas": {
                            "instagram": {"used": 0, "limit": 100},
                            "facebook": {"used": 0, "limit": 100},
                            "twitter": {"used": 0, "limit": 100}
                        }
                    },
                    "message": "Mock response - quotas disabled for testing"
                }
        return MockResponse()

    @classmethod
    def _parse_media_from_monoes_action(cls, monoes_action):
        """Parse media from Monoes action format to legacy format"""
        media_array = []
        
        # Get media URL and content type
        media_url = monoes_action.get('mediaURL', '')
        content_type = monoes_action.get('contentType', '').lower()
        
        if media_url:
            # Determine media type based on contentType or URL extension
            if content_type in ['video', 'mp4', 'mov', 'avi'] or any(ext in media_url.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv']):
                media_type = 'VIDEO'
            else:
                media_type = 'IMAGE'  # Default to image
                
            media_array.append({
                'url': media_url,
                'type': media_type,
                'effect': 'normal',
                'customRatio': ''
            })
        
        return media_array

    @classmethod
    def _transform_monoes_action_to_legacy_format(cls, monoes_action):
        """Transform new Monoes API response format to legacy format"""
        try:
            # Convert ISO timestamp to milliseconds timestamp for legacy format
            def iso_to_milliseconds(iso_string):
                """Convert ISO timestamp string to milliseconds since epoch"""
                if not iso_string:
                    return 0
                try:
                    from datetime import datetime
                    # Parse ISO timestamp and convert to milliseconds
                    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
                    return int(dt.timestamp() * 1000)
                except:
                    return 0
            
            # Use actual createdAt timestamp instead of UUID hash
            created_at_iso = monoes_action.get('createdAt', '')
            created_at_ms = iso_to_milliseconds(created_at_iso)
            
            # Fallback to current timestamp if no createdAt
            if not created_at_ms:
                import time
                created_at_ms = int(time.time() * 1000)
            
            legacy_action = {
                'id': monoes_action.get('id', ''),  # Preserve the original Monoes action ID
                'createdAt': created_at_ms,  # Use actual timestamp instead of UUID hash
                'type': monoes_action.get('type', ''),
                # Map Monoes status to legacy state names expected by GUI
                'state': {
                    'ASSIGNED': 'PENDING',        # Newly created but not started yet
                    'IN_PROGRESS': 'INPROGRESS',  # Actively running
                    'PAUSED': 'PAUSE',            # Manually paused
                    'PENDING': 'PENDING',
                    'DONE': 'DONE'
                }.get(monoes_action.get('status', ''), monoes_action.get('status', '')),
                'title': monoes_action.get('title', ''),
                'createdBy': 'AI' if monoes_action.get('aiUsed', False) else monoes_action.get('createdBy', {}).get('name', ''),
                'execProps': {
                    'source': monoes_action.get('target', ''),  # Map target to source
                    'sourceType': monoes_action.get('contentType', ''),
                    'jobs': monoes_action.get('jobs', []),
                    'maxResultsCount': monoes_action.get('maxResultsCount', 0),
                    'resultsCount': 0,  # Default value, may need to be updated based on actual data
                    'failedInvites': [],
                    'inviteesCount': 0,
                    'reachedIndex': 0,
                    'failedProfileSearches': [],
                    'profilesCount': 0,
                    'failedMessages': [],
                    'recipientsCount': 0,
                    'failedItems': [],
                    'itemsCount': 0,
                    'requiredQuotas': 0,
                    'currentStage': '',
                    'reachedSubIndex': -1
                },
                'props': {
                    'listId': '',  # This may need to be extracted from a different field
                    'selectedListItems': [],
                    'emails': [],
                    'campaignId': '',
                    'messageText': monoes_action.get('content', ''),
                    'messageSubject': monoes_action.get('messageSubject', ''),
                    'messageTemplateId': 0,
                    'keyword': monoes_action.get('keywords', ''),
                    'maxResultsCount': monoes_action.get('maxResultsCount', 0),
                    'scheduledDate': monoes_action.get('scheduledDate', ''),
                    'media': cls._parse_media_from_monoes_action(monoes_action),
                    'text': monoes_action.get('content', ''),
                    'locationTag': monoes_action.get('locationTag', ''),
                    'target': monoes_action.get('target', ''),
                    'startDate': '',
                    'endDate': '',
                    'pollInterval': 0,
                    'maxContentCount': 0,
                    'commentText': '',
                    'searches': []
                }
            }
            
            # Add additional metadata properties
            legacy_action['lastExecutedAt'] = monoes_action.get('lastExecutedAt', '')
            legacy_action['completedAt'] = monoes_action.get('completedAt', '')
            legacy_action['disabled'] = monoes_action.get('disabled', False)
            legacy_action['ownerId'] = monoes_action.get('ownerId', '')
            legacy_action['position'] = monoes_action.get('position', 0)
            legacy_action['noMorePages'] = monoes_action.get('noMorePages', True)
            legacy_action['updatedAt'] = monoes_action.get('updatedAt', '')
            legacy_action['deletedAt'] = monoes_action.get('deletedAt', '')
            legacy_action['aiUsed'] = monoes_action.get('aiUsed', False)
            
            return legacy_action
            
        except Exception as e:
            logger.error(f"Error transforming Monoes action to legacy format: {e}")
            return None

    @classmethod
    def get_actions(cls, state=None):
        """Get actions from Monoes API and transform to legacy format"""
        url = cls._monoes_dash_api_url % 'actions'
        print(url)
        
        try:
            # Use the new API endpoint
            res = cls._session.get(url=url, headers=RestAPI._auth_header, timeout=cls.timeout)
            res.raise_for_status()  # Check for HTTP errors
            
            # Transform the response to legacy format
            monoes_response = json.loads(res.text)
            actions_data = monoes_response.get('data', {}).get('actions', [])
            
            # Filter by state if provided
            if state:
                # Map legacy state names to new API state names
                state_mapping = {
                    'PENDING': 'PENDING',
                    'INPROGRESS': 'IN_PROGRESS', 
                    'DONE': 'DONE'
                }
                mapped_state = state_mapping.get(state, state)
                actions_data = [action for action in actions_data if action.get('status') == mapped_state]
            
            # Transform each action to legacy format
            legacy_actions = []
            for action in actions_data:
                legacy_action = cls._transform_monoes_action_to_legacy_format(action)
                if legacy_action:
                    legacy_actions.append(legacy_action)
            
            # Return in legacy format
            legacy_response = {
                'actions': legacy_actions,
                'totalCount': monoes_response.get('totalCount', len(legacy_actions))
            }
            
            return legacy_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Monoes API: {e}")
            # Return mock data on error to allow UI testing
            print("WARNING: Returning mock actions due to API error")
            import time
            current_time = int(time.time() * 1000)
            mock_actions = [
                {
                    'id': 'mock-1',
                    'createdAt': current_time,
                    'type': 'INSTAGRAM_LIKE',
                    'state': 'PENDING',
                    'title': 'Mock Instagram Like',
                    'createdBy': 'AI',
                    'execProps': {
                        'source': 'https://instagram.com/test',
                        'sourceType': 'PROFILE',
                        'itemsCount': 10
                    },
                    'props': {
                        'media': [],
                        'text': 'Mock action for UI testing'
                    },
                    'aiUsed': True
                },
                {
                    'id': 'mock-2',
                    'createdAt': current_time - 10000,
                    'type': 'LINKEDIN_CONNECT',
                    'state': 'INPROGRESS',
                    'title': 'Mock LinkedIn Connect',
                    'createdBy': 'User',
                    'execProps': {
                        'source': 'https://linkedin.com/in/test',
                        'sourceType': 'SEARCH',
                        'itemsCount': 5
                    },
                    'props': {
                        'media': [],
                        'text': 'Connecting...'
                    },
                    'aiUsed': False
                }
            ]
            return {'actions': mock_actions, 'totalCount': len(mock_actions)}
        except Exception as e:
            logger.error(f"Error processing Monoes API response: {e}")
            # Return empty response on error
            return {'actions': [], 'totalCount': 0}

    @classmethod
    def get_actions_native(cls, state=None):
        """Get actions from Monoes API in native format with optional state filtering."""
        url = cls._monoes_dash_api_url % 'actions'
        try:
            res = cls._session.get(url=url, headers=RestAPI._auth_header, timeout=cls.timeout)
            res.raise_for_status()
            monoes_response = json.loads(res.text)
            actions_data = monoes_response.get('data', {}).get('actions', [])
            if state:
                state_mapping = {
                    'PENDING': 'PENDING',
                    'INPROGRESS': 'IN_PROGRESS',
                    'DONE': 'DONE'
                }
                mapped_state = state_mapping.get(state, state)
                actions_data = [action for action in actions_data if action.get('status') == mapped_state]
            return {
                'data': {
                    'actions': actions_data,
                    'totalCount': monoes_response.get('totalCount', len(actions_data))
                }
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Monoes API (native): {e}")
            return {'data': {'actions': [], 'totalCount': 0}}
        except Exception as e:
            logger.error(f"Error processing Monoes API response (native): {e}")
            return {'data': {'actions': [], 'totalCount': 0}}

    @classmethod
    def get_actions_summary_native(cls):
        try:
            data = cls.get_actions_native().get('data', {}).get('actions', [])
            counts = {'ALL': 0, 'PENDING': 0, 'IN_PROGRESS': 0, 'DONE': 0}
            for a in data:
                counts['ALL'] += 1
                s = a.get('status')
                if s == 'PENDING':
                    counts['PENDING'] += 1
                elif s == 'IN_PROGRESS':
                    counts['IN_PROGRESS'] += 1
                elif s == 'DONE':
                    counts['DONE'] += 1
            return counts
        except Exception:
            return {'ALL': 0, 'PENDING': 0, 'IN_PROGRESS': 0, 'DONE': 0}

    @classmethod
    @retry
    def get_actions_legacy(cls, state=None):
        """Original get_actions method for fallback"""
        url = cls._monoes_dash_api_url % 'actions'
        print(url)
        params = {'disabled': False}
        if state is not None:
            params['state'] = state
        params = json.dumps(params)
        res = cls._session.get(url=url, headers=RestAPI._auth_header, params=params, timeout=cls.timeout)
        return res

    @classmethod
    @retry
    def get_specify_action(cls, created_at):
        """state : ['PENDING, INPROGRESS, DONE]"""
        url = cls._monoes_dash_api_url % f'actions/{created_at}'
        print(url)
        res = cls._session.get(url=url, headers=RestAPI._auth_header, timeout=cls.timeout)
        return res

    @classmethod
    @retry
    def get_specify_template(cls, template_id: int):
        """
        Args:
            template_id: int : comes from messageTemplateId
        """
        url = cls._monoes_dash_api_url % f'templates/{template_id}'
        print(url)
        res = cls._session.get(url=url, headers=RestAPI._auth_header, timeout=cls.timeout)
        return res

    @classmethod
    @retry
    def update_action_custom(cls, action_id, body: dict):
        """updating action via custom body"""
        # for i in range(10):
        sleep(1.1)
        url = cls._monoes_dash_api_url % f'actions/{action_id}'
        print(url, body)
        res = cls._session.patch(url=url, headers=RestAPI._auth_header, json=body, timeout=cls.timeout)
        return res
    
    @classmethod
    def set_action_state(cls, action_id, state):
        """setting action state"""
        url = cls._monoes_dash_api_url % f'actions/{action_id}'
        if state == 'INPROGRESS':
            payload = {
                        "status": "ASSIGNED",
                        "state": "INPROGRESS"
                    }
        elif state == 'DONE':
            payload = {
                    "status": "DONE",
                    "state": "DONE"
                }
        res = cls._session.patch(url=url, headers=RestAPI._auth_header, json=payload, timeout=cls.timeout)
        return res

    def get_action_targets(self, action_id: str, after: str = None, limit: int = 100) -> dict:
        """
        Fetch action targets for a given action ID with pagination support.
        
        Args:
            action_id: The ID of the action to get targets for
            after: Cursor for pagination (optional)
            limit: Maximum number of targets to return (default: 100)
            
        Returns:
            Dictionary containing actionTargets data with pagination info
        """
        url = self._monoes_dash_api_url % 'actionTargets'
        
        params = {'actionId': action_id, 'first': limit}
        if after:
            params['after'] = after
            
        try:
            res = self._session.get(url=url, headers=RestAPI._auth_header, params=params, timeout=self.timeout)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Error fetching action targets: {e}")
            # Ensure callers can safely access data.actionTargets
            return {"data": {"actionTargets": []}, "pageInfo": {}}

    def get_person(self, person_id: str) -> dict:
        """
        Fetch a single person's data by ID from the Monoes API.
        
        Args:
            person_id: The ID of the person to fetch
            
        Returns:
            Dictionary containing person data
        """
        url = self._monoes_dash_api_url % f'people/{person_id}'
        
        try:
            res = self._session.get(url=url, headers=RestAPI._auth_header, timeout=self.timeout)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Error fetching person {person_id}: {e}")
            return {}

    @staticmethod
    def _extract_username_from_url(url: str) -> str:
        """
        Extract username from social media URLs.
        
        Args:
            url: Social media profile URL
            
        Returns:
            Extracted username or empty string if not found
        """
        if not url:
            return ""
        try:
            from urllib.parse import urlparse
            # Ensure scheme for consistent parsing
            test_url = url
            if not test_url.startswith('http://') and not test_url.startswith('https://'):
                test_url = f"https://{test_url}"
            parsed = urlparse(test_url)
            host = parsed.netloc.lower()
            path = parsed.path.strip('/')
            first_segment = path.split('/')[0] if path else ""

            if not first_segment:
                return ""

            if 'instagram.com' in host:
                return first_segment
            if 'twitter.com' in host or host == 'x.com' or host.endswith('.x.com'):
                return first_segment
            if 'tiktok.com' in host:
                return first_segment
            if 'linkedin.com' in host:
                # Expecting /in/<username>
                if path.startswith('in/'):
                    return path.split('/')[1] if len(path.split('/')) > 1 else ""
                return first_segment
            if host == 't.me' or host.endswith('.t.me'):
                return first_segment
        except Exception:
            pass
        return ""

    def map_action_targets_to_saved_items(self, action: 'Actions', targets: list[dict]) -> list[dict]:
        """
        Convert raw actionTargets and their hydrated person data into SavedItem-like dictionaries.
        
        Args:
            action: Actions object containing action details
            targets: List of actionTargets with nested person data
            
        Returns:
            List of dictionaries in SavedItem format
        """
        if not targets:
            return []
            
        mapped_items = []
        # Try to get target from different possible locations
        target_platform = 'INSTAGRAM'  # Default fallback
        if hasattr(action, 'target') and action.target:
            target_platform = action.target.upper()
        elif hasattr(action, 'props') and action.props and hasattr(action.props, 'target') and action.props.target:
            target_platform = action.props.target.upper()
        elif hasattr(action, 'execProps') and action.execProps and hasattr(action.execProps, 'source') and action.execProps.source:
            target_platform = action.execProps.source.upper()
        
        for target in targets:
            person_data = target.get('person', {})
            company_data = target.get('company', {})
            opportunity_data = target.get('opportunity', {})
            
            # Extract platform-specific username
            platform_username = ""
            # Define link placeholders to avoid unbound references
            insta_link = x_link = tiktok_link = linkedin_link = telegram_link = ""
            if target_platform == 'INSTAGRAM':
                insta_link = person_data.get('instaLink', '')
                if isinstance(insta_link, dict):
                    insta_link = insta_link.get('primaryLinkUrl', '')
                platform_username = self._extract_username_from_url(insta_link)
            elif target_platform == 'X':
                x_link = person_data.get('xLink', '')
                if isinstance(x_link, dict):
                    x_link = x_link.get('primaryLinkUrl', '')
                platform_username = self._extract_username_from_url(x_link)
            elif target_platform == 'TIKTOK':
                tiktok_link = person_data.get('tiktokLink', '')
                if isinstance(tiktok_link, dict):
                    tiktok_link = tiktok_link.get('primaryLinkUrl', '')
                platform_username = self._extract_username_from_url(tiktok_link)
            elif target_platform == 'LINKEDIN':
                linkedin_link = person_data.get('linkedinLink', '')
                if isinstance(linkedin_link, dict):
                    linkedin_link = linkedin_link.get('primaryLinkUrl', '')
                platform_username = self._extract_username_from_url(linkedin_link)
            elif target_platform == 'TELEGRAM':
                telegram_link = person_data.get('telegramLink', '')
                if isinstance(telegram_link, dict):
                    telegram_link = telegram_link.get('primaryLinkUrl', '')
                platform_username = self._extract_username_from_url(telegram_link)
            
            # Strict requirement: we only care about the active platform link.
            # If the link/username is missing for this platform, skip this target.
            # This ensures messaging/search actions only process valid platform users.
            # Note: url_val is set below; to keep logic clear we perform a presence check after url_val is computed.

            # Helper: normalize URL to include https scheme if missing
            def normalize_url(url: str) -> str:
                if not url:
                    return ''
                if not url.startswith('http://') and not url.startswith('https://'):
                    return f"https://{url}"
                return url

            # Choose platform-specific fields only (ignore other socials)
            follower_count = 0
            category_val = ''
            intro_val = ''
            is_verified_val = False
            url_val = ''
            if target_platform == 'INSTAGRAM':
                follower_count = person_data.get('instaFollowerCount') or 0
                category_val = person_data.get('instaCategory', '')
                intro_val = person_data.get('instaIntro', '')
                is_verified_val = person_data.get('instaIsVerified', False)
                url_val = normalize_url(insta_link)
            elif target_platform == 'X':
                follower_count = person_data.get('xFollowerCount') or 0
                category_val = person_data.get('xCategory', '')
                intro_val = person_data.get('xIntro', '')
                is_verified_val = person_data.get('xIsVerified', False)
                url_val = normalize_url(x_link)
            elif target_platform == 'TIKTOK':
                follower_count = person_data.get('tiktokFollowerCount') or 0
                category_val = person_data.get('tiktokCategory', '')
                intro_val = person_data.get('tiktokIntro', '')
                is_verified_val = person_data.get('tiktokIsVerified', False)
                url_val = normalize_url(tiktok_link)
            elif target_platform == 'LINKEDIN':
                follower_count = person_data.get('linkedinFollowerCount') or 0
                intro_val = person_data.get('linkedinIntro', '')
                url_val = normalize_url(linkedin_link)
            elif target_platform == 'TELEGRAM':
                url_val = normalize_url(telegram_link)

            # Map to SavedItem format (only if we have a valid platform URL and username)
            if not url_val or not platform_username:
                continue
            saved_item = {
                'id': target.get('personId'),  # Use personId as the ID
                'socialUserId': target.get('personId'),  # Legacy compatibility
                'platform_username': platform_username,
                'full_name': (person_data.get('name', {}).get('firstName', '') + ' ' + person_data.get('name', {}).get('lastName', '')).strip(),
                'image_url': person_data.get('avatarUrl', ''),
                'follower_count': follower_count,
                'contact_details': person_data.get('emails', {}).get('primaryEmail', ''),
                'website': '',  # Not available in current person data
                'url': url_val,
                'platform': target_platform.lower(),
                'updated_at': person_data.get('updatedAt', ''),
                'created_at': person_data.get('createdAt', ''),
                'category': category_val,
                'introduction': intro_val,
                'is_verified': is_verified_val,
                'location': person_data.get('city', ''),
                'company_name': '',  # Not available in current person data
                'job_title': person_data.get('jobTitle', ''),
                'opportunity_title': '',  # Not available in current person data
                'opportunity_value': 0  # Not available in current person data
            }
            
            # Remove None/empty values
            saved_item = {k: v for k, v in saved_item.items() if v is not None and v != ''}
            mapped_items.append(saved_item)
            
        return mapped_items

    def fetch_targets_as_saved_items(self, action: 'Actions') -> list[dict]:
        """
        Fetch all pages of actionTargets for an action, hydrate person data, and map to SavedItem format.
        
        Args:
            action: Actions object containing action details
            
        Returns:
            List of dictionaries in SavedItem format
        """
        # Resolve action identifier (support both action.actionId and action.id)
        action_id = getattr(action, 'actionId', None) or getattr(action, 'id', None) or getattr(getattr(action, '_action', {}), 'get', lambda *_: None)('id')
        if not action_id:
            print("Action has no id/actionId, cannot fetch targets")
            return []
            
        all_targets = []
        after_cursor = None
        page_count = 0
        max_pages = 10  # Safety limit to prevent infinite loops
        
        while page_count < max_pages:
            try:
                # Fetch action targets
                targets_response = self.get_action_targets(action_id, after=after_cursor, limit=100)
                targets_data = targets_response.get('data', {}).get('actionTargets', [])
                # Client-side safeguard: ensure only targets for this actionId are processed
                if targets_data:
                    targets_data = [t for t in targets_data if t.get('actionId') == action_id]
                
                if not targets_data:
                    break
                    
                # Hydrate person data for each target
                hydrated_targets = []
                for target in targets_data:
                    person_id = target.get('personId')
                    if person_id:
                        person_data = self.get_person(person_id)
                        if person_data:
                            # Merge person data into target
                            target['person'] = person_data.get('data', {}).get('person', {})
                            hydrated_targets.append(target)
                
                all_targets.extend(hydrated_targets)
                
                # Check if there are more pages (support both nested and root pageInfo)
                page_info = (targets_response.get('data', {}) or {}).get('pageInfo', {}) or targets_response.get('pageInfo', {})
                if not page_info.get('hasNextPage', False):
                    break
                    
                after_cursor = page_info.get('endCursor')
                page_count += 1
                
            except Exception as e:
                print(f"Error fetching targets page {page_count + 1}: {e}")
                break
        
        # Map to SavedItem format
        mapped_items = self.map_action_targets_to_saved_items(action, all_targets)
        
        # Remove duplicates based on personId
        seen_ids = set()
        unique_items = []
        for item in mapped_items:
            if item.get('id') not in seen_ids:
                seen_ids.add(item.get('id'))
                unique_items.append(item)
        
        print(f"Fetched {len(all_targets)} targets, mapped to {len(unique_items)} unique SavedItems")
        return unique_items

    def fetch_targets_as_saved_items_graphql(self, action: 'Actions', first: int = 100) -> list[dict]:
        """
        Fetch actionTargets with nested person data via GraphQL and map to SavedItem format.

        This avoids REST N+1 hydration by requesting person fields inline.
        Pagination is handled via pageInfo { hasNextPage, endCursor }.
        """
        # Resolve action identifier (support both action.actionId and action.id)
        action_id = getattr(action, 'actionId', None) or getattr(action, 'id', None) or getattr(getattr(action, '_action', {}), 'get', lambda *_: None)('id')
        if not action_id:
            print("Action has no id/actionId, cannot fetch targets (GraphQL)")
            return []

        # GraphQL endpoint (same host, graphql path)
        url = self._monoes_dash_api_url % 'graphql'

        # Define query asking for actionTargets and nested person fields we map
        query = (
            "query ActionTargets($actionId: String!, $first: Int!, $after: String) {\n"
            "  actionTargets(actionId: $actionId, first: $first, after: $after) {\n"
            "    nodes {\n"
            "      actionId\n"
            "      personId\n"
            "      person {\n"
            "        id\n"
            "        name { firstName lastName }\n"
            "        avatarUrl\n"
            "        instaLink { primaryLinkUrl }\n"
            "        xLink { primaryLinkUrl }\n"
            "        tiktokLink { primaryLinkUrl }\n"
            "        linkedinLink { primaryLinkUrl }\n"
            "        instaFollowerCount\n"
            "        xFollowerCount\n"
            "        tiktokFollowerCount\n"
            "        linkedinFollowerCount\n"
            "        instaIntro\n"
            "        xIntro\n"
            "        tiktokIntro\n"
            "        linkedinIntro\n"
            "        instaIsVerified\n"
            "        xIsVerified\n"
            "        tiktokIsVerified\n"
            "        city\n"
            "        jobTitle\n"
            "        createdAt\n"
            "        updatedAt\n"
            "      }\n"
            "    }\n"
            "    pageInfo { hasNextPage endCursor }\n"
            "  }\n"
            "}"
        )

        variables = {"actionId": action_id, "first": first, "after": None}

        all_nodes: list[dict] = []
        page_count = 0
        max_pages = 10
        while page_count < max_pages:
            try:
                payload = {"query": query, "variables": variables}
                res = self._session.post(url=url, headers=RestAPI._auth_header, json=payload, timeout=self.timeout)
                res.raise_for_status()
                data = res.json() or {}
                action_targets = (((data.get('data') or {}).get('actionTargets')) or {})
                nodes = action_targets.get('nodes', []) or []
                # Safeguard: filter by actionId client-side as well
                nodes = [n for n in nodes if n.get('actionId') == action_id]
                # Normalize GraphQL nodes to REST-like targets shape (person nested already)
                all_nodes.extend(nodes)

                page_info = action_targets.get('pageInfo') or {}
                if not page_info.get('hasNextPage'):
                    break
                variables['after'] = page_info.get('endCursor')
                page_count += 1
            except Exception as e:
                print(f"GraphQL error fetching targets page {page_count + 1}: {e}")
                break

        # Map to SavedItem format using existing mapper
        mapped_items = self.map_action_targets_to_saved_items(action, all_nodes)

        # Deduplicate by personId
        seen_ids = set()
        unique_items = []
        for item in mapped_items:
            if item.get('id') not in seen_ids:
                seen_ids.add(item.get('id'))
                unique_items.append(item)

        print(f"[GraphQL] Fetched {len(all_nodes)} targets, mapped to {len(unique_items)} unique SavedItems")
        return unique_items

    @classmethod
    def get_saved_list(cls):
        """
        DISABLED: Returns mock data for testing actions list only
        Original format:
        {
              "message": "Successful",
              "data": [
                {
                  "listType": "INSTAGRAM",
                  "name": "in-new-list-2",
                  "id": "6c7df1ea-98fa-4c87-9f80-4ee509f4845f",
                  "itemCount": 3,
                  "email": "nokhodian@gmail.com"
                }
            ]
        }
        """
        print("MOCK: get_saved_list() - returning mock response")
        # Create a mock response object
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"message": "Mock response - saved lists disabled for testing", "data": []}'
            def json(self):
                return {
                    "message": "Mock response - saved lists disabled for testing",
                    "data": []
                }
        return MockResponse()

    @classmethod
    def get_social_saved_item(cls, list_id):
        """
        DISABLED: Returns mock data for testing actions list only
        Original format:
        {
              "message": "Successful",
              "data": [
                        {
                          "id": "a1e3d0b8-a61f-4858-b6a5-cbce4e7cbd5a",
                          "contact_details": [
                            {
                              "type": "email",
                              "value": ""
                            }
                          ],
                          "follower_count": 1,
                          "platform": "instagram",
                          "platform_username": "malohg",
                          "updated_at": "Gholam",
                          "full_name": "GholamRest",
                          "image_url": "",
                          "url": "gholam/.com"
                        }
                      ]
            }
        """
        print(f"MOCK: get_social_saved_item({list_id}) - returning mock response")
        # Create a mock response object
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"message": "Mock response - social saved items disabled for testing", "data": []}'
            def json(self):
                return {
                    "message": "Mock response - social saved items disabled for testing",
                    "data": []
                }
        return MockResponse()

    @classmethod
    @retry
    def create_social_item(cls, list_id, body):
        """body = {"updated_at": "124490284174",
                    "platform": "TELEGRAM",
                    "platform_username": "malohg",
                    "image_url": "",
                    "url": "gholam/.com",
                    "full_name": "GholamRest",
                    "contact_details": [{"type":"email", "value": ""}],
                    "follower_count": 1}"""
        url = cls._monoes_dash_api_url % f'social-list/{list_id}/item'
        print(url)

      
        body["createdBy"] = {"name": "monoes-agent"}

        body = body
        res = cls._session.post(url=url, headers=RestAPI._auth_header | {'User-Agent': 'FlatlayBot'}, json=body,
                                timeout=cls.timeout)
        print(res)
        return res

    @classmethod
    @retry
    def create_social_items(cls, list_id, created_list: list):
        """body = 'items': [{"updated_at": "124490284174",
                    "platform": "INSTAGRAM",
                    "platform_username": "malohg",
                    "image_url": "",
                    "url": "gholam/.com",
                    "full_name": "GholamRest",
                    "contact_details": [{"type":"email", "value": ""}],
                    "follower_count": 1}]"""
        url = cls._monoes_dash_api_url % f'social-list/{list_id}/items'
        print(url)
        
        # Inject createdBy for all items
        for item in created_list:
            if "createdBy" not in item:
                item["createdBy"] = {"name": "monoes-agent"}

        # Debug: show a concise snapshot of what is being sent
        try:
            preview = []
            for item in (created_list or [])[:5]:
                preview.append({
                    "platform": item.get("platform"),
                    "url": item.get("url"),
                    "city": (item.get("creator_location") or {}).get("city") if isinstance(item.get("creator_location"), dict) else item.get("creator_location"),
                })
            print("[API] create_social_items: posting", len(created_list or []), "items; preview:", preview)
        except Exception:
            pass

        body = {"items": created_list}
        res = cls._session.post(url=url, headers=RestAPI._auth_header | {'User-Agent': 'FlatlayBot'}, json=body,
                                timeout=cls.timeout)
        print(res)
        return res

    @classmethod
    @retry
    def update_social_users(cls, updated_list: list):
        """body = 'items': [{"updated_at": "124490284174",
                    "platform": "INSTAGRAM",
                    "platform_username": "malohg",
                    "image_url": "",
                    "url": "gholam/.com",
                    "full_name": "GholamRest",
                    "contact_details": [{"type":"email", "value": ""}],
                    "follower_count": 1}]"""
        url = cls._monoes_dash_api_url % f'social-users'
        print(url)

        # Inject createdBy for all items
        for item in updated_list:
            if "createdBy" not in item:
                item["createdBy"] = {"name": "monoes-agent"}

        body = {"items": updated_list}
        res = cls._session.put(url=url, headers=RestAPI._auth_header | {'User-Agent': 'FlatlayBot'}, json=body,
                               timeout=cls.timeout)
        print(res)
        return res

    @classmethod
    def get_threads(cls, action_id: int = None, is_confirmed: bool = True, generate_replies: bool = False):
        """
        DISABLED: Returns mock data for testing actions list only
        
        Args:
            action_id: int : Action.createdAt //required when multi action is running, otherwise it can use as optional argument
            is_confirmed: bool: default is True //optional
            generate_replies: bool: If True the replies will generate //optional

        Returns:
            {"threads": []}
        """
        print(f"MOCK: get_threads({action_id}, {is_confirmed}, {generate_replies}) - returning mock response")
        # Create a mock response object
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"threads": [], "message": "Mock response - threads disabled for testing"}'
            def json(self):
                return {
                    "threads": [],
                    "message": "Mock response - threads disabled for testing"
                }
        return MockResponse()

    @classmethod
    @retry
    def upsert_threads(cls, threads_list: list):
        """
        Payload sample:
           {
            "threads": [
                {
                    "socialUserId": "C+bnsqLGODAGR+ilIhazdjL7kEe8l+VaLEJpNRYOBn0=",
                    "metadata": { // is not validated - any object
                        "key": "any type"
                    },
                    "messages": [
                        {
                            "type": "OUTBOUND", // sent
                            "body": "Yo whadup",
                            "sentAt": 1726857862000
                        },
                        {
                            "type": "INBOUND", // received
                            "body": "Plz, Leave me alone."
                        }
                    ]
                },
                {
                    "socialUserId": "G+dPoBu9wz21IbDppJH92epY7bHXR6TXD2WBbHd/9U0=",
                    "messages": [
                        {
                            "type": "OUTBOUND",
                            "body": "Hi?",
                            "sentAt": 1726857862000
                        },
                        {
                            "type": "INBOUND",
                            "body": "Hi!"
                        }
                    ]
                }
            ]
        }
        """
        url = cls._monoes_dash_api_url % f'threads'
        print(url)
        body = {"threads": threads_list}
        res = cls._session.put(url=url, headers=RestAPI._auth_header | {'User-Agent': 'FlatlayBot'}, json=body,
                               timeout=cls.timeout)
        return res

    @classmethod
    @retry
    def latest_bot_version(cls, platform: str, current_version: str):
        """ 'platform': 'WINDOWS'||'MAC',
            'Version': if lastVersion[first_digit] > currentVersion:
                        forced = True"""
        url = cls._monoes_dash_api_url % 'version/'
        print(url)
        params = json.dumps({'platform': platform,
                             'version': current_version})
        res = cls._session.get(url=url, headers=RestAPI._auth_header, params=params, timeout=cls.timeout)
        return res

    @classmethod
    @retry
    def download_images(cls, url):
        print(url)
        res = cls._session.get(url, proxies={'http': urllib.request.getproxies().get('http'),
                                             'https': urllib.request.getproxies().get('http')})
        return res, bytes

    @classmethod
    def get_profile_info(cls):
        """
        DISABLED: Returns mock data for testing actions list only
        
        getting image_url , first_name  of user
        """
        print("MOCK: get_profile_info() - returning mock response")
        # Create a mock response object
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"data": {"isMerchant": false, "email": "test@example.com", "merchantId": "", "image_url": "", "first_name": "Test User"}, "message": "Mock response - profile info disabled for testing"}'
            def json(self):
                return {
                    "data": {
                        "isMerchant": False,
                        "email": "test@example.com",
                        "merchantId": "",
                        "image_url": "",
                        "first_name": "Test User"
                    },
                    "message": "Mock response - profile info disabled for testing"
                }
        return MockResponse()

    @classmethod
    def get_crawler_xpath(cls):
        """
        Returns crawler data from a mock file for testing instead of making an API call.
        """
        import os
        import sys
        import traceback
        print("DEBUG: get_crawler_xpath called")
        mock_path = os.path.join(os.path.dirname(__file__), '../data/crawler_mock_data.json')
        print(f"DEBUG: mock_path is {mock_path}")
        try:
            print("DEBUG: Opening mock JSON file...")
            with open(mock_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("DEBUG: Loaded JSON. Keys in data:", list(data.keys()))

            class MockResponse:
                def __init__(self, data):
                    self.status_code = 200
                    self._data = data
                    self.text = json.dumps(data)
                def json(self):
                    return self._data
            return MockResponse(data)
        except Exception as e:
            print(f"MOCK: get_crawler_xpath() - failed to load mock file, using fallback. Error: {e}")
            traceback.print_exc()
            # Fallback to previous mock
            class MockResponse:
                def __init__(self):
                    self.status_code = 200
                    self.text = '{"data": {"xpath": {}, "settings": {}}, "message": "Mock response - crawler xpath disabled for testing"}'
                def json(self):
                    return {
                        "data": {
                            "xpath": {},
                            "settings": {}
                        },
                        "message": "Mock response - crawler xpath disabled for testing"
                    }
            return MockResponse()
            
    @classmethod
    @retry
    def create_people(cls, people_list: list):
        """
        Sends a batch of person objects to the new API.
        """
        # Debug: raw input preview (platform/url/location)
        try:
            raw_preview = []
            for p in (people_list or [])[:5]:
                raw_preview.append({
                    "platform": p.get("platform"),
                    "url": p.get("url"),
                    "location": p.get("creator_location") or p.get("location"),
                    "name": p.get("full_name")
                })
            print("[API] create_people: input", len(people_list or []), "profiles; preview:", raw_preview)
        except Exception:
            pass

        people_list = cls.map_social_users_to_person(people_list)

        try:
            print(f"[API] create_people: payload size: {len(people_list) if people_list else 0}")
            # Debug: Print full payload for troubleshooting 401
            import json
            logger.info(f"[DEBUG] create_people payload: {json.dumps(people_list, indent=2)}")
        except Exception as e:
            logger.error(f"[DEBUG] Error printing payload: {e}")

        url = "https://monoes.me/rest/batch/people"
        headers = RestAPI._auth_header | {
            "User-Agent": "FlatlayBot",
            "Content-Type": "application/json"
        }
        logger.info(f"[DEBUG] create_people headers: {headers}")
        res = cls._session.post(url=url, headers=headers, json=people_list, timeout=cls.timeout)
        return res
    
    @classmethod
    def _to_iso_datetime_str(cls, value: Any) -> Optional[str]:
        """Safely converts a millisecond Unix timestamp string to an ISO 8601 datetime string."""
        if not value:
            return None
        try:
            dt_object = datetime.fromtimestamp(int(value) / 1000)
            return dt_object.isoformat() + "Z"
        except (ValueError, TypeError):
            return None

    @classmethod
    def _to_bool(cls, value: Any) -> bool:
        """Safely converts a value to a boolean."""
        return str(value).lower() in ['true', '1', 'yes', 'true']

    @classmethod
    def _split_name(cls, full_name: str) -> Tuple[str, str]:
        """Splits a full name into a first and last name."""
        if not full_name or not isinstance(full_name, str):
            return "", ""
        parts = full_name.strip().split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        return first_name, last_name


    @classmethod
    def map_social_users_to_person(cls, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Maps a list of profiles from a single social media source to a list of
        standardized dictionaries.

        Args:
            profiles: A list of profile dictionaries, all from the same platform.

        Returns:
            A list of standardized dictionaries.
        """
        if not profiles:
            return []

        # Determine the platform from the first item in the list.
        # We assume all items in the list are from this same platform.
        platform = str(profiles[0].get("platform") or "").upper()
        
        mapped_list = []
        for profile in profiles:
            if not profile:
                continue
                
            # Basic structure for every person
            person_dict = {
                "name": {},
                "emails": {},
                "company": {},
            }

            # 1. Map common fields
            full_name = profile.get("full_name") or profile.get("name")
            if full_name:
                first_name, last_name = cls._split_name(full_name)
                person_dict["name"]["firstName"] = first_name
                person_dict["name"]["lastName"] = last_name
            else:
                # Fallback to username if name is missing
                username = profile.get('platform_username') or profile.get('username')
                if username:
                    person_dict["name"]["firstName"] = username
                    person_dict["name"]["lastName"] = "(Social Profile)"
                else:
                    person_dict["name"]["firstName"] = "Unknown"
                    person_dict["name"]["lastName"] = "User"

            person_dict["avatarUrl"] = profile.get("image_url") or profile.get("avatar")
            
            # Handle creator_location - can be string or object
            creator_location = profile.get("creator_location") or profile.get("location")
            if isinstance(creator_location, dict):
                # Fallback order for city: city -> state -> country
                person_dict["city"] = (
                    creator_location.get("city")
                    or creator_location.get("state")
                    or creator_location.get("country")
                )
            else:
                person_dict["city"] = creator_location
                
            person_dict["createdAt"] = cls._to_iso_datetime_str(profile.get("joined_date") or profile.get("created_at"))
            person_dict["updatedAt"] = cls._to_iso_datetime_str(profile.get("updated_at"))
            
            # Handle contact_details - can be string or list of objects
            contact = profile.get("contact_details") or profile.get("email")
            if contact:
                if isinstance(contact, list) and len(contact) > 0:
                    # Extract first email from list format: [{"type": "email", "value": "email@example.com"}]
                    for contact_item in contact:
                        if isinstance(contact_item, dict) and contact_item.get("type") == "email":
                            person_dict["emails"]["primaryEmail"] = contact_item.get("value")
                            break
                        elif isinstance(contact_item, str) and '@' in contact_item:
                             person_dict["emails"]["primaryEmail"] = contact_item
                             break
                elif isinstance(contact, str) and '@' in contact:
                    # Handle string format directly
                    person_dict["emails"]["primaryEmail"] = contact

            # 2. Map platform-specific fields (use nested link object structure)
            url_val = profile.get("url") or profile.get("profile_link")
            
            if platform == "INSTAGRAM":
                person_dict["instaLink"] = {
                    "primaryLinkLabel": "",
                    "primaryLinkUrl": url_val,
                    "additionalLinks": []
                }
                person_dict["instaCategory"] = profile.get("category")
                person_dict["instaIntro"] = profile.get("introduction") or profile.get("bio")
                person_dict["instaIsVerified"] = cls._to_bool(profile.get("is_verified") or profile.get("verified"))
                person_dict["instaFollowerCount"] = profile.get("follower_count") or profile.get("followers")
                if profile.get("website"):
                    person_dict["company"]["domainName"] = profile.get("website")

            elif platform == "X" or platform == "TWITTER":
                person_dict["xLink"] = {
                    "primaryLinkLabel": "",
                    "primaryLinkUrl": url_val,
                    "additionalLinks": []
                }
                person_dict["xCategory"] = profile.get("category")
                person_dict["xIntro"] = profile.get("introduction") or profile.get("bio")
                person_dict["xIsVerified"] = cls._to_bool(profile.get("is_verified") or profile.get("verified"))
                person_dict["xFollowerCount"] = profile.get("follower_count") or profile.get("followers")
                if profile.get("website"):
                    person_dict["company"]["domainName"] = profile.get("website")
            
            elif platform == "LINKEDIN":
                person_dict["linkedinLink"] = {
                    "primaryLinkLabel": "",
                    "primaryLinkUrl": url_val,
                    "additionalLinks": []
                }
                person_dict["linkedinIntro"] = profile.get("introduction") or profile.get("bio")
                person_dict["linkedinFollowerCount"] = profile.get("follower_count") or profile.get("followers") or profile.get("connections")
                if profile.get("website"):
                    person_dict["company"]["domainName"] = profile.get("website")
                if profile.get("company"):
                    person_dict["company"]["name"] = profile.get("company")

            elif platform == "TIKTOK":
                person_dict["tiktokLink"] = {
                    "primaryLinkLabel": "",
                    "primaryLinkUrl": url_val,
                    "additionalLinks": []
                }
                person_dict["tiktokCategory"] = profile.get("category")
                person_dict["tiktokIntro"] = profile.get("introduction") or profile.get("bio")
                person_dict["tiktokIsVerified"] = cls._to_bool(profile.get("is_verified") or profile.get("verified"))
                person_dict["tiktokFollowerCount"] = profile.get("follower_count") or profile.get("followers")
                if profile.get("website"):
                    person_dict["company"]["domainName"] = profile.get("website")

            # Inject createdBy
            person_dict["createdBy"] = {"name": "monoes-agent"}

            # Map note if present
            if profile.get("note"):
                person_dict["noteTargets"] = [{
                    "content": profile.get("note"),
                    "createdBy": {"name": "monoes-agent"}
                }]

            # Add the fully mapped dictionary to our list after removing empty keys
            # Important: Keep nested dicts if they have data
            mapped_item = {k: v for k, v in person_dict.items() if v}
            mapped_list.append(mapped_item)
            
        return mapped_list


if __name__ == "__main__":
    req = RestAPI(token)

    resp = req.create_people(person_legacy_data)
   
