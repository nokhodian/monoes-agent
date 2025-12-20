from __future__ import annotations
from newAgent.src.exceptions.errors import ParsingError
from newAgent.src.data.attributes import GUI_Attrs
import traceback
from datetime import datetime, timezone, timedelta
import calendar
from PyQt5.QtGui import QPixmap
from typing import List, Literal
import re


def convert_iso_to_current_timezone(iso_datetime: str):
    """
    Converting the ISO 8601 UTC to current user TimeZone
    example ->
        iso_datetime = 2025-01-05T12:00:00.000Z
        return: datetime.datetime(2025, 1, 5, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(seconds=12600), 'Iran Standard Time'))
    """
    try:
        if not iso_datetime:
            # Return None explicitly when the input string is empty or None
            return None
        dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).astimezone()
        return dt
    except ValueError:
        # This mean the iso_datetime format is incorrect!
        pass
    except Exception as err:
        print("Exception at convert_iso_to_current_timezone", err)


def next_period(start: datetime, end: datetime, pollInterval: int):
    """
    Generate Next Period depends on startDate, endDate, pollInterval

    Args:
        start: datetime: StartDate value
        end: datetime: EndDate value
        pollInterval: int: unit by minute

    Returns:
        datetime The datetime of the nextInterval
        None If the currentTime is out of range
    """
    start = datetime.strptime(start.strftime("%B %d, %Y, %H:%M"), "%B %d, %Y, %H:%M")
    end = datetime.strptime(end.strftime("%B %d, %Y, %H:%M"), "%B %d, %Y, %H:%M")
    current = datetime.now().replace(microsecond=0)

    if current < start:
        return start

    if current > end:
        return None

    minutes_since_start = int((current - start).total_seconds() / 60)
    nextInterval = ((minutes_since_start // pollInterval) + 1) * pollInterval
    next_time = start + timedelta(minutes=nextInterval)

    if next_time > end:
        return None

    return next_time


class Campaigns:
    """{'title': 'Name of the campaign',
        'status': 'Should be one of these[active, draft, ended]',
        'campaignID': 1923189}"""
    title: str
    status: str
    campaignID: str
    brief_description: str
    _campaign: dict = {}

    def __init__(self, campaign):
        self.campaign = campaign

    @property
    def campaign(self):
        return self._campaign

    @campaign.setter
    def campaign(self, value: dict):
        self._campaign.clear()
        self.title = value.get('title')
        self.status = value.get('status')
        self.campaignID = value.get('campaignID')
        self.brief_description = value.get('briefdescription')

        self._campaign['title'] = self.title
        self._campaign['status'] = self.status
        self._campaign['campaignID'] = self.campaignID
        self._campaign['briefdescription'] = self.brief_description


class Quotas:
    """
    Parsing MerchantsQuotas RestAPI JSON
    """
    usedQuota: int = 0
    remainingQuota: int = 0
    maxQuota: int = 0
    _quotaType: str = ''  # For Example LINKEDIN_KEYWORD_SEARCH | INSTAGRAM_MESSAGING
    _quota: dict = {}

    def __init__(self, quota: dict, quotaType: str):
        self._quotaType = quotaType
        self.quota = quota

    @property
    def quota(self):
        return self._quota

    @quota.setter
    def quota(self, value: dict):
        socialQuota: dict = value.get(self._quotaType, {}) or {}
        if not socialQuota:
            raise ParsingError(f"Couldn't parse Quotas -> QuotaType: {self._quotaType} & Value: {value}")
        self.usedQuota = socialQuota.get('usedQuota', 0) or 0
        self.remainingQuota = socialQuota.get('remainingQuota', 0) or 0
        self.maxQuota = socialQuota.get('maxQuota', 0) or 0

        self._quota['usedQuota'] = self.usedQuota
        self._quota['remainingQuota'] = self.remainingQuota
        self._quota['maxQuota'] = self.maxQuota


class NextJob:
    page: int
    status: str
    updated_at: int
    retry: bool
    _next_job: dict = {}

    def __init__(self, next_job):
        self.next_job = next_job

    @property
    def next_job(self):
        return self._next_job

    @next_job.setter
    def next_job(self, value: dict):
        if value is None:
            value = {}
        self.page = value.get('page')
        self.status = value.get('status')
        self.updated_at = value.get('updatedAt')
        self.retry = value.get('retry')

        self._next_job['page'] = self.page
        self._next_job['status'] = self.status
        self._next_job['updatedAt'] = self.updated_at
        self._next_job['retry'] = self.retry


class Media:
    """
    The properties of each content on media field on PUBLISH_CONTENT Actions.
    This class only used for easy parsing.
    """
    type: str = ""  # ["IMAGE", "VIDEO"]
    url: str = ""  # The Image or Video URL
    effect: str = "normal"  # optional
    customRatio: str = ""  # optional ["1:1", "16:9", "4:5"]
    _media: dict = {}

    def __init__(self, media):
        self.media = media

    @property
    def media(self):
        return self._media

    @media.setter
    def media(self, value: dict):
        self.type = value.get("type")
        self.url = value.get("url") or ""
        self.effect = value.get("effect")
        self.customRatio = value.get("customRatio") or ""

        self._media["type"] = self.type
        self._media["url"] = self.url
        self._media["effect"] = self.effect
        self._media["customRatio"] = self.customRatio


class Actions:
    source: str
    failedInvites: list
    inviteesCount: int = None
    sourceType: str
    reachedIndex: int
    createdAt: int
    listId: str
    listName: str = ''
    selectedListItems: list = []
    saved_list: list = []
    emails: list = []
    messageText: str
    messageSubject: str = ""
    messageTemplateId: int
    campaignId: str
    campaignName: str = ''
    state: str
    title: str
    type: str
    typeName: str = ""
    keywrd: str
    maxResultsCount: int
    resultsCount: int
    failedProfileSearches: list = []
    profilesCount: int
    failedMessages: list = []
    recipientsCount: int
    createdBy: str
    failedItems: list = []
    itemsCount: int
    requiredQuotas: int = 0
    scheduledDate: str = ""  # ISO 8601 format
    scheduledDateCurrentZone = None
    scheduledLaunchDiff = None
    currentStage: str = ""  # [POLLING, REPLYING]
    startDate: str = ""  # ISO 8601 format
    startDateCurrentZone = None
    endDate: str = ""  # ISO 8601 format
    endDateCurrentZone = None
    pollInterval: int  # 30 >=
    nextPeriod = None
    media: List[Media] = []
    text: str = ""
    locationTag: str = ""
    maxContentCount: int = 0
    commentText: str = ""
    searches: list = []
    interactionKeyword: list = []
    reachedSubIndex: int = -1
    target: str = ""  # ["POST"]

    jobs: list = []
    isRunning: bool = False
    
    # Additional metadata properties from new API
    position: int = 0
    noMorePages: bool = True
    updatedAt: str = ""
    deletedAt: str = ""
    aiUsed: bool = False
    disabled: bool = False
    ownerId: str = ""
    lastExecutedAt: str = ""
    completedAt: str = ""
    actionId: str = ""

    def __init__(self, action):
        self._action = {}
        self.action = action

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value: dict):
        self._action.clear()
        
        # Handle both old format (with execProps/props) and new format (flat structure)
        if 'execProps' in value or 'props' in value:
            # Legacy format - use existing logic
            exec_props: dict = value.get('execProps', {})
            props: dict = value.get('props', {})
        else:
            # New flat format - extract relevant properties
            # Try to find source in 'source', 'target', or 'platform'
            raw_source = value.get('source') or value.get('target') or value.get('platform')
            exec_props: dict = {
                'source': raw_source,
                'sourceType': value.get('sourceType', ''),
                'jobs': value.get('jobs', []),
                'resultsCount': value.get('resultsCount'),
                'maxResultsCount': value.get('maxResultsCount'),
                'reachedIndex': value.get('reachedIndex'),
                'failedInvites': value.get('failedInvites'),
                'failedMessages': value.get('failedMessages'),
                'inviteesCount': value.get('inviteesCount'),
                'recipientsCount': value.get('recipientsCount'),
                'profilesCount': value.get('profilesCount'),
                'failedProfileSearches': value.get('failedProfileSearches'),
                'requiredQuotas': value.get('requiredQuotas'),
                'currentStage': value.get('currentStage'),
                'failedItems': value.get('failedItems'),
                'itemsCount': value.get('itemsCount'),
                'reachedSubIndex': value.get('reachedSubIndex')
            }
            props: dict = {
                'listId': value.get('listId'),
                'keyword': value.get('keywords') or value.get('keyword'),  # Support both keys
                'maxResultsCount': value.get('maxResultsCount'),
                'selectedListItems': value.get('selectedListItems'),
                'emails': value.get('emails'),
                'campaignId': value.get('campaignId'),
                'messageText': value.get('content'),  # 'content' in new API maps to messageText
                'messageSubject': value.get('messageSubject'),
                'messageTemplateId': value.get('messageTemplateId'),
                'scheduledDate': value.get('scheduledDate'),
                'media': value.get('media'),
                'text': value.get('content'),  # Also use content for text
                'locationTag': value.get('locationTag'),
                'target': value.get('target'),
                'startDate': value.get('startDate'),
                'endDate': value.get('endDate'),
                'pollInterval': value.get('pollInterval'),
                'maxContentCount': value.get('maxContentCount'),
                'commentText': value.get('commentText'),
                'searches': value.get('searches')
            }
        
        # Handle createdAt - could be timestamp (old) or ISO string (new)
        created_at_value = value.get('createdAt', 0)
        if isinstance(created_at_value, str):
            # New format - ISO string, convert to timestamp
            try:
                from dateutil import parser
                dt = parser.parse(created_at_value)
                self.createdAt = int(dt.timestamp() * 1000)
            except:
                self.createdAt = 0
        else:
            # Old format - already timestamp
            self.createdAt = created_at_value
            
        timestamp = datetime.fromtimestamp(self.createdAt / 1000)
        cal_time = f"{calendar.month_name[timestamp.month]} " \
                   f"{timestamp.day},{timestamp.year}  {timestamp.hour}:{timestamp.minute}"
        
        self.type = value.get('type')
        state_raw = value.get('state') or value.get('status')
        if state_raw and isinstance(state_raw, str):
            state_raw = state_raw.upper()
            if state_raw == 'IN_PROGRESS' or state_raw == 'IN PROGRESS':
                self.state = 'INPROGRESS'
            else:
                self.state = state_raw
        else:
            self.state = state_raw
        self.title = value.get('title', cal_time)
        if not self.title:
            self.title = cal_time
        source_raw = exec_props.get('source') or ''
        src_norm = source_raw.upper()
        self.source = 'FLATLAY' if src_norm == 'EMAIL' else src_norm
        source_type_raw = exec_props.get('sourceType') or ''
        self.sourceType = source_type_raw.upper()
        self.listId = props.get('listId')
        
        # Handle createdBy - could be string (old) or object (new)
        created_by_value = value.get('createdBy', '')
        if isinstance(created_by_value, dict):
            # New format - extract name from object
            self.createdBy = created_by_value.get('name', '')
        else:
            # Old format - already string
            self.createdBy = created_by_value or ''
            
        self.jobs = exec_props.get('jobs', []) or []

        self.scheduledDate = props.get('scheduledDate')
        self.scheduledDateCurrentZone = convert_iso_to_current_timezone(self.scheduledDate)
        if self.scheduledDateCurrentZone:
            self.scheduledLaunchDiff = self.scheduledDateCurrentZone.timestamp() - \
                                       (datetime.now().replace(microsecond=0).replace(second=0) +
                                        timedelta(days=GUI_Attrs.socials_scheduled.get(self.source.lower(),
                                                                                       0) or 0)).timestamp()

        self._action['execProps'] = exec_props
        self._action['props'] = props
        # Capture Monoes action UUID if present and mirror to `id`
        try:
            self.actionId = value.get('id') or self._action.get('id') or ''
        except Exception:
            self.actionId = ''
        # For compatibility, also expose `id` like new API
        try:
            self.id = self.actionId
        except Exception:
            pass
        self._action['createdAt'] = self.createdAt
        self._action['type'] = self.type
        self._action['state'] = self.state
        self._action['title'] = self.title
        self._action['source'] = self.source
        self._action['sourceType'] = self.sourceType
        self._action['listId'] = self.listId
        self._action['id'] = self.actionId
        self._action['createdBy'] = self.createdBy
        self._action['scheduledDate'] = self.scheduledDate
        self._action['scheduledDateCurrentZone'] = self.scheduledDateCurrentZone
        self._action['scheduledLaunchDiff'] = self.scheduledLaunchDiff

        self._action['jobs'] = self.jobs
        self._action['id'] = self.actionId
        
        # Handle additional metadata properties
        self.position = value.get('position', 0)
        self.noMorePages = value.get('noMorePages', True)
        self.updatedAt = value.get('updatedAt', '')
        self.deletedAt = value.get('deletedAt', '')
        self.aiUsed = value.get('aiUsed', False)
        self.disabled = value.get('disabled', False)
        self.ownerId = value.get('ownerId', '')
        self.lastExecutedAt = value.get('lastExecutedAt', '')
        self.completedAt = value.get('completedAt', '')
        
        # Add metadata to action dict
        self._action['position'] = self.position
        self._action['noMorePages'] = self.noMorePages
        self._action['updatedAt'] = self.updatedAt
        self._action['deletedAt'] = self.deletedAt
        self._action['aiUsed'] = self.aiUsed
        self._action['disabled'] = self.disabled
        self._action['ownerId'] = self.ownerId
        self._action['lastExecutedAt'] = self.lastExecutedAt
        self._action['completedAt'] = self.completedAt

        if self.type == 'KEYWORD_SEARCH':
            self.typeName = "Discover More"
            self.keywrd = props.get('keyword')
            self.maxResultsCount = props.get('maxResultsCount')
            self.resultsCount = exec_props.get('resultsCount')

            self._action['keyword'] = self.keywrd
            self._action['maxResultsCount'] = self.maxResultsCount
            self._action['resultsCount'] = self.resultsCount

        elif self.type == 'PROFILE_SEARCH':
            if self.sourceType == "PROFILE_SEARCH":
                self.typeName = "Update Social Info"
            elif self.sourceType == "FOLLOW_PROFILE":
                self.typeName = "Follow Profile"
            self.selectedListItems = props.get('selectedListItems', []) or []
            self.failedProfileSearches = exec_props.get('failedProfileSearches')
            self.profilesCount = exec_props.get('profilesCount')
            self.reachedIndex = exec_props.get('reachedIndex')
            self.target = props.get('target') or exec_props.get('source') or ''

            self._action['selectedListItems'] = self.selectedListItems
            self._action['failedProfileSearches'] = self.failedProfileSearches or []
            self._action['profilesCount'] = self.profilesCount
            self._action['reachedIndex'] = self.reachedIndex
            self._action['target'] = self.target

        elif self.type == 'BULK_MESSAGING':
            self.typeName = "Direct Message"
            self.selectedListItems = props.get('selectedListItems', []) or []
            self.emails = props.get('emails', [])
            self.campaignId = props.get('campaignId')
            self.messageText = props.get('messageText') or ""
            self.messageSubject = props.get('messageSubject') or ""
            self.messageTemplateId = props.get('messageTemplateId')
            self.failedMessages = exec_props.get('failedInvites') or exec_props.get('failedMessages') or []
            self.recipientsCount = exec_props.get('inviteesCount') or exec_props.get('recipientsCount')
            self.reachedIndex = exec_props.get('reachedIndex')
            self.target = props.get('target') or exec_props.get('source') or ''

            self._action['selectedListItems'] = self.selectedListItems
            self._action['emails'] = self.emails
            self._action['campaignId'] = self.campaignId
            self._action['messageText'] = self.messageText
            self._action['messageSubject'] = self.messageSubject
            self._action['messageTemplateId'] = self.messageTemplateId
            self._action['failedMessages'] = self.failedMessages
            self._action['recipientsCount'] = self.recipientsCount
            self._action['reachedIndex'] = self.reachedIndex
            self._action['target'] = self.target
        elif self.type == 'PROFILE_FETCH':
            if self.sourceType == "GROUPS_FETCH":
                self.typeName = "Import Groups"
            elif self.sourceType == "FOLLOWERS_FETCH":
                if self.source == "TELEGRAM":
                    self.typeName = "Import Contacts"
                else:
                    self.typeName = "Pull Followers"
            elif self.sourceType == "FOLLOWINGS_FETCH":
                self.typeName = "Pull Followings"

            self.maxResultsCount = exec_props.get('maxResultsCount')
            self.resultsCount = exec_props.get('resultsCount')

            self._action['maxResultsCount'] = self.maxResultsCount
            self._action['resultsCount'] = self.resultsCount
        elif self.type == 'PUBLISH_CONTENT':
            self.typeName = "Publish Content"
            self.requiredQuotas = exec_props.get("requiredQuotas") or 0
            self.selectedListItems = props.get('selectedListItems', []) or []
            media = props.get('media') or []
            self.media = []
            for content in media:
                self.media.append(Media(content))
            self.text = props.get('text') or ""
            self.locationTag = props.get("locationTag") or ""
            self.target = props.get('target')

            self._action['media'] = self.media
            self._action['text'] = self.text
            self._action['locationTag'] = self.locationTag
            self._action['target'] = self.target
            self._action['selectedListItems'] = self.selectedListItems

        elif self.type == 'BULK_REPLYING':
            self.typeName = "Reply Messages"
            self.selectedListItems = props.get("selectedListItems") or []
            self.startDate = props.get("startDate")
            self.startDateCurrentZone = convert_iso_to_current_timezone(self.startDate)
            self.endDate = props.get("endDate")
            self.endDateCurrentZone = convert_iso_to_current_timezone(self.endDate)
            self.pollInterval = props.get("pollInterval")
            self.nextPeriod = next_period(start=self.startDateCurrentZone,
                                          end=self.endDateCurrentZone,
                                          pollInterval=self.pollInterval)
            if self.nextPeriod:
                self.scheduledLaunchDiff = self.nextPeriod.timestamp() - \
                                           datetime.now().replace(microsecond=0).replace(second=0).timestamp()
            self.currentStage = exec_props.get("currentStage") or ""
            self.failedItems = exec_props.get("failedItems") or []
            self.reachedIndex = exec_props.get("reachedIndex")
            self.itemsCount = exec_props.get("itemsCount")

            self._action["selectedListItems"] = self.selectedListItems
            self._action["startDate"] = self.startDate
            self._action["startDateCurrentZone"] = self.startDateCurrentZone
            self._action["endDate"] = self.endDate
            self._action["endDateCurrentZone"] = self.endDateCurrentZone
            self._action["pollInterval"] = self.pollInterval
            self._action["nextPeriod"] = self.nextPeriod
            self._action["scheduledLaunchDiff"] = self.scheduledLaunchDiff
            self._action["currentStage"] = self.currentStage
            self._action["failedItems"] = self.failedItems
            self._action["reachedIndex"] = self.reachedIndex
            self._action["itemsCount"] = self.itemsCount

        elif self.type == "PROFILE_INTERACTION":
            if self.sourceType == "LIKE_CONTENT":
                self.typeName = "Like Content"
            elif self.sourceType == "COMMENT_CONTENT":
                self.typeName = "Comment"
            self.maxContentCount = props.get("maxContentCount") or 0
            self.commentText = props.get("commentText") or ""
            self.searches = props.get("searches", []) or []
            if self.searches and len(self.searches) > 0:
                self.interactionKeyword = self.searches[0].get('keyword', '')
            self.reachedIndex = exec_props.get("reachedIndex")
            self.reachedSubIndex = exec_props.get("reachedSubIndex")
            self.failedItems = exec_props.get("failedItems") or []
            self.itemsCount = exec_props.get("itemsCount")

            self._action["maxContentCount"] = self.maxContentCount
            self._action["commentText"] = self.commentText
            self._action["searches"] = self.searches
            self._action["interactionKeyword"] = self.interactionKeyword
            self._action["reachedIndex"] = self.reachedIndex
            self._action["reachedSubIndex"] = self.reachedSubIndex
            self._action["failedItems"] = self.failedItems
            self._action["itemsCount"] = self.itemsCount

        self._action["typeName"] = self.typeName

    def __lt__(self, other):
        return self.scheduledLaunchDiff < other.scheduledLaunchDiff

    def __le__(self, other):
        return self.scheduledLaunchDiff <= other.scheduledLaunchDiff

    def __gt__(self, other):
        return self.scheduledLaunchDiff > other.scheduledLaunchDiff

    def __ge__(self, other):
        return self.scheduledLaunchDiff >= other.scheduledLaunchDiff

    def __repr__(self):
        return self.title


class Saved:
    listType: str
    name: str
    id: str
    itemCount: int
    email: str
    _saved: dict = {}

    def __init__(self, saved):
        self.saved = saved

    @property
    def saved(self):
        return self._saved

    @saved.setter
    def saved(self, value: dict):
        self._saved.clear()

        self.listType = value.get('listType')
        self.name = value.get('name')
        self.id = value.get('id')
        self.itemCount = value.get('itemCount')
        self.email = value.get('email')

        self._saved['listType'] = self.listType
        self._saved['name'] = self.name
        self._saved['id'] = self.id
        self._saved['itemCount'] = self.itemCount
        self._saved['email'] = self.email


class SavedItem:
    id: str
    follower_count: int
    platform: str
    platform_username: str
    updated_at: str
    category: str
    content_count: int
    external_id: str
    following_count: int
    full_name: str = ' '
    first_name: str = ' '
    last_name: str = ' '
    image_url: str
    is_business: bool
    is_verified: bool
    platform_account_type: str = '-'
    url: str
    contact_details: list = []
    creator_location: dict = {}
    connections: str = ''
    introduction: str = '-'
    website: str = '-'
    customSettings: dict
    customAttributes: dict
    variables: dict = {}
    _saved_item: dict = {}
    image_pixmap: QPixmap

    def __init__(self, saved_item):
        self.saved_item = saved_item

    @staticmethod
    def extract_username(email):
        pattern = r"([^@]+)@(.+)"
        try:
            match = re.match(pattern, email)
            if match:
                return match.group(1)
            return email
        except Exception as ex:
            print('Something went wrong on extract_username', ex)
            return email

    def _get_variables(self, static_attributes: dict, custom_attributes: dict):
        try:
            self.variables = {k: v for k, v in static_attributes.items()}
            for key, value in custom_attributes.items():
                self.variables[key] = value
        except Exception as ex:
            traceback.print_exc()
            print('Exception on class SavedItems _get_variables: ', ex)

    @property
    def saved_item(self):
        return self._saved_item

    @saved_item.setter
    def saved_item(self, value: dict):
        self._saved_item.clear()
        self.id = value.get('id')
        self.follower_count = value.get('follower_count')
        self.platform = value.get('platform')
        self.platform_username = value.get('platform_username')
        self.updated_at = value.get('updated_at')
        self.content_count = value.get('content_count')
        self.external_id = value.get('external_id')
        self.following_count = value.get('following_count')
        self.image_url = value.get('image_url')
        self.introduction = value.get('introduction', '-')
        self.is_business = value.get('is_business')
        self.is_verified = value.get('is_verified')
        self.platform_account_type = value.get('platform_account_type', '-')
        self.url = value.get('url')
        self.website = value.get('website', '-')
        self.contact_details = value.get('contact_details') or []
        self.category = value.get('category')
        self.first_name = value.get('first_name', ' ')
        self.last_name = value.get('last_name', ' ')
        self.full_name = value.get('full_name', ' ')
        self.creator_location = value.get('creator_location', {})
        self.connections = value.get('connections')
        self.customSettings = value.get('customSettings', {}) or {}
        self.customAttributes = self.customSettings.get('customAttributes', {}) or {}
        self._get_variables(static_attributes={'platform_username': self.extract_username(self.platform_username),
                                               'full_name': self.extract_username(self.full_name),
                                               'first_name': self.extract_username(self.first_name),
                                               'last_name': self.extract_username(self.last_name)},
                            custom_attributes=self.customAttributes)

        self._saved_item['id'] = self.id
        self._saved_item['follower_count'] = self.follower_count
        self._saved_item['platform'] = self.platform
        self._saved_item['platform_username'] = self.platform_username
        self._saved_item['updated_at'] = self.updated_at
        self._saved_item['content_count'] = self.content_count
        self._saved_item['external_id'] = self.external_id
        self._saved_item['following_count'] = self.following_count
        self._saved_item['image_url'] = self.image_url
        self._saved_item['introduction'] = self.introduction
        self._saved_item['is_business'] = self.is_business
        self._saved_item['is_verified'] = self.is_verified
        self._saved_item['platform_account_type'] = self.platform_account_type
        self._saved_item['url'] = self.url
        self._saved_item['website'] = self.website
        self._saved_item['contact_details'] = self.contact_details
        self._saved_item['category'] = self.category
        self._saved_item['first_name'] = self.first_name
        self._saved_item['last_name'] = self.last_name
        self._saved_item['full_name'] = self.full_name
        self._saved_item['creator_location'] = self.creator_location
        self._saved_item['connections'] = self.connections
        self._saved_item['customSettings'] = self.customSettings


class ThreadMessage:
    type: str  # [OUTBOUND, INBOUND] OUTBOUND means I sent INBOUND is response of client.
    body: str = ""  # The message responses
    sentAt: int  # Timestamp

    def __init__(self, message: dict):
        self.type = message.get("type") or ""
        self.body = message.get("body") or ""
        self.sentAt = message.get("sentAt")


class MetaData:
    key: str = ""

    def __init__(self, metadata: dict):
        self.key = metadata.get("key") or ""


class Threads:
    userId: str
    id: str = ""
    socialUserId: str = ""
    threadType: str  # [DIRECT_MESSAGE]
    messages: List[ThreadMessage] = []
    metadata: MetaData
    suggestedReplies: list = []
    confirmedReply: str = ""
    engagementStatus: str  # [INTERESTED, NOT_INTERESTED]
    isConfirmed: bool
    updatedAt: int

    _threads: dict = {}

    def __init__(self, threads: dict):
        self.threads = threads

    @property
    def threads(self):
        return self._threads

    @threads.setter
    def threads(self, value: dict):
        self.userId = value.get("userId")
        self.id = value.get("id") or ""
        self.socialUserId = value.get("socialUserId") or ""
        self.threadType = value.get("threadType")
        messages = value.get("messages") or []
        for message in messages:
            self.messages.append((ThreadMessage(message or {})))
        self.metadata = MetaData(value.get("metadata") or {})
        self.suggestedReplies = value.get("suggestedReplies") or []
        self.confirmedReply = value.get("confirmedReply") or ""
        self.engagementStatus = value.get("engagementStatus")
        self.isConfirmed = value.get("isConfirmed")
        self.updatedAt = value.get("updatedAt")

        self._threads["userId"] = self.userId
        self._threads["id"] = self.id
        self._threads["socialUserId"] = self.socialUserId
        self._threads["threadType"] = self.threadType
        self._threads["messages"] = self.messages
        self._threads["metadata"] = self.metadata
        self._threads["suggestedReplies"] = self.suggestedReplies
        self._threads["confirmedReply"] = self.confirmedReply
        self._threads["engagementStatus"] = self.engagementStatus
        self._threads["isConfirmed"] = self.isConfirmed
        self._threads["updatedAt"] = self.updatedAt

    @staticmethod
    def prepare_send(id: str = None,
                     socialUserId: str = None,
                     messages: list = None,
                     metadata: dict = None) -> dict:
        """
        Description: Prepare sending data for sending via WebSocket

        Args:
            socialUserId (str): Required
            messages (list): sample: [{"type": "OUTBOUND", "body": "hi", "sentAt": 17622138761}, {"type": "INBOUND", "body": "hi how are you"}] Required
            metadata (dict): Optional
        Returns:
            dict Converted values to JSON
        Raises:
            ParsingError: if each of Args isn't correct Type
        """
        if metadata is None:
            metadata = dict(key="any type")
        resolved_id = id or socialUserId
        if messages is None:
            messages = []
        if not isinstance(messages, list):
            raise ParsingError("Invalid messages type on prepare_send function!", 1)
        if resolved_id is None or not isinstance(resolved_id, str):
            raise ParsingError("Invalid id/socialUserId on prepare_send function!", 1)
        if not isinstance(metadata, dict):
            raise ParsingError("Invalid metadata type on prepare_send function!", 1)
        ret: dict = {
            "id": resolved_id,
            "socialUserId": socialUserId or resolved_id,
            "metadata": metadata,
            "messages": messages
        }

        return ret


class Event:
    """
    Parser of WebSocket-Req/Response.
    """
    eventType: str = ""  # request: [REPORT_JOB], response: [REPORT_JOB_ACK, REPLIES_CONFIRMED, REPLIES_CANCELED, ERROR]
    message: str = ""  # Only on the error moments
    job: dict = {}
    state: str = ""  # [EXECUTING, WAITING, STOPPED, COMPLETED]
    actionId: int
    actionJob: dict = {}  # NextJob.next_job

    _event: dict = {}

    # Easy attributes (shortcut)
    REPORT_JOB: str = "REPORT_JOB"
    REPORT_JOB_ACK: str = "REPORT_JOB_ACK"
    REPLIES_CONFIRMED: str = "REPLIES_CONFIRMED"
    REPLIES_CANCELED: str = "REPLIES_CANCELED"
    ERROR: str = "ERROR"

    def __init__(self, event: dict):
        self.event = event

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value: dict):
        self.eventType = value.get("eventType")
        self.message = value.get("message") or ""
        self.job = value.get("job") or {}
        self.state = self.job.get("state") or ""
        self.actionId = self.job.get("actionId")
        self.actionJob = self.job.get("actionJob") or {}

        self._event["eventType"] = self.eventType
        self._event["message"] = self.message
        self._event["job"] = self.job
        self._event["job"]["state"] = self.state
        self._event["job"]["actionId"] = self.actionId
        self._event["job"]["actionJob"] = self.actionJob

    @staticmethod
    def prepare_send(eventType: str,
                     state: Literal['EXECUTING', 'WAITING', 'STOPPED', 'COMPLETED'],
                     actionId: int,
                     actionJob: dict = None) -> dict:
        """
        Description: Prepare sending data for sending via WebSocket

        Args:
            eventType (str): Must be one of the following values:
                - 'REPORT_JOB'

            state (str): Must be one of the following values:
                - 'EXECUTING'
                - 'WAITING'
                - 'STOPPED'
                - 'COMPLETED'

            actionId (int): Must be The action.createdAt value
            actionJob (dict): Must be the NextJob to JSON
        Returns:
            dict Converted values to JSON
        Raises:
            ParsingError: if each of Args isn't correct Type
        """
        if not all((isinstance(eventType, str),
                    isinstance(state, str),
                    isinstance(actionId, int),
                    isinstance(actionJob, dict) or actionJob is None)):
            raise ParsingError("Invalid arguments type on prepare_send function!", 1)
        if state not in ["EXECUTING", "WAITING", "STOPPED", "COMPLETED"]:
            raise ParsingError(f"Invalid state value on prepare_send function\nstate: {state}", 2)
        if eventType not in ["REPORT_JOB"]:
            raise ParsingError(f"Invalid eventType value on prepare_send function\neventType: {eventType}", 3)

        if state == "EXECUTING":
            if actionJob:
                ret = {"eventType": eventType,
                       "job": {
                           "state": state,
                           "actionId": actionId,
                           "actionJob": actionJob
                       }}
            else:
                ret = {"eventType": eventType,
                       "job": {
                           "state": state,
                           "actionId": actionId
                       }}

        elif state == "WAITING":
            ret = {"eventType": eventType,
                   "job": {
                       "state": state,
                       "actionId": actionId
                   }}
        elif state == "STOPPED":
            ret = {"eventType": eventType,
                   "job": {
                       "state": state,
                       "actionId": actionId
                   }}
        elif state == "COMPLETED":
            ret = {"eventType": eventType,
                   "job": {
                       "state": state,
                       "actionId": actionId
                   }}
        else:
            raise ParsingError("Something went wrong at data_parser", 4)
        return ret

    # @staticmethod
    # def parse_recieve(data: dict):
    #     """
    #     Description: Parsing response data from WebSocket.
    #
    #     Args:
    #         data (dict): Must contains the following key/values:
    #             - eventType (str): Must contains in ["REPLIES_CONFIRMED"]
    #             - job (dict): Must contains the following key/values:
    #                 - actionId (int): the action.createdAt timestamp
    #
    #     """
    #     REPLIES_CONFIRMED = "REPLIES_CONFIRMED"
    #     REPLIES_IGNORED = "REPLIES_IGNORED"
    #
    #     def is_replies_confirmed() -> Tuple[int, bool]:
    #         """
    #         Returns:
    #             Tuple actionId as int & is_confirmed as bool
    #         """
    #         parsed_data = Event(data)
    #         is_confirmed = False
    #         if parsed_data.eventType == REPLIES_CONFIRMED:
    #             is_confirmed = True
    #
    #         return parsed_data.actionId, is_confirmed
    #
    #     methods: dict = {REPLIES_CONFIRMED: is_replies_confirmed}
    #     method = methods.get(data["eventType"])
    #

    def __repr__(self):
        return f"{self.event}"


if __name__ == '__main__':
    pass
