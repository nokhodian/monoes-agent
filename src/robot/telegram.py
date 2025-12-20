import io
import argparse
import asyncio
import getpass
import os
import logging
import traceback
from datetime import datetime, timezone
from newAgent.src.data.attributes import Attrs
from newAgent.src.robot.flatlay import traceback_email_flatlay
from newAgent.src.robot.scraper import LogWrapper

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    UsernameNotOccupiedError,
    UsernameInvalidError
)

from telethon.tl.functions.contacts import GetContactsRequest
from telethon.errors import UserNotParticipantError, FloodWaitError, ChannelPrivateError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, Chat, Channel, Message
from telethon.tl.functions.contacts import ResolveUsernameRequest
from time import sleep
from urllib.request import getproxies
import base64
import requests
import json
from io import BytesIO
import mimetypes
import time


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
                # traceback.print_exc()
                i += 1
                sleep(Attrs.sleep_config['typing_min'])
        return False

    return wrapper


# methods


class Telegram:
    name = 'telegram'
    username = ''
    full_name = ''
    profile_pic: bytes = b''
    password = ''
    logger = None
    isLoggedIn = False
    pause_search = False
    _phone_code_hash = None
    function_result: str = ''
    result = None
    sendable_chats = []  # Store groups/channels where media can be sent

    def __init__(self, api_id, api_hash: str, session_name="telegram_session", log_callback=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self.max_attempts = 3
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.logger = LogWrapper(logging.getLogger(self.name))
        if log_callback:
            self.logger.set_callback(log_callback)

    @retry
    def upload_image(self, blob):
        """uploading those profile images that will be expire"""
        url = 'http://18.215.217.156:2021/uploadB64'
        base64_data = base64.b64encode(blob)

        # create the data URI
        data_uri = f"data:image/png;base64,{base64_data.decode('utf-8')}"
        body = {'data': data_uri}
        
        try:
            res = requests.post(url, json=body, timeout=10)
            res.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            return json.loads(res.text)
        except requests.RequestException as e:
            self.logger.error(f"Failed to upload image: {e}")
            return None

    async def _get_profile_blob(self, user):
        try:
            # Download the profile photo into a BytesIO object
            profile_photo_stream = io.BytesIO()
            await self.client.download_profile_photo(user, file=profile_photo_stream)

            profile_photo_stream.seek(0)

            # Get the image binary data
            return profile_photo_stream.read()

        except Exception as ex:
            traceback_email_flatlay(
                body=f'We have an Exception on Telegram_get_profile_blob')
            return b''

    async def handle_2fa(self, password: str) -> str:
        """Handle 2FA password input securely."""
        if not password:
            password = getpass.getpass("Please enter your 2FA password (input will be hidden): ")
        return password

    async def handle_phone_code(self, phone_number: str) -> bool:
        """Handle phone verification code input with retry logic."""
        for attempt in range(self.max_attempts):
            try:
                self._phone_code_hash = await self.client.send_code_request(phone_number)
                # if not code:
                #     code = input(f"Please enter the verification code sent to {phone_number}: ")
                return True
            except FloodWaitError as e:
                self.logger.warning(f"Too many attempts. Please wait {e.seconds} seconds before trying again.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                self.logger.error(f"Error sending code: {str(e)}")
                traceback_email_flatlay(
                    body=f'Error sending Telegram code: {e}')
                if attempt < self.max_attempts - 1:
                    self.logger.info("Retrying...")
                else:
                    self.logger.error(traceback.format_exc())
                    raise

        raise Exception("Maximum attempts reached for phone code verification")

    async def connect(self, phone_number: str, code: str = None, password: str = None):
        """Attempt to connect to Telegram with a maximum of 3 attempts."""
        for attempt in range(self.max_attempts):
            try:
                await self.client.connect()

                if not await self.client.is_user_authorized():
                    if not code:
                        if await self.handle_phone_code(phone_number):
                            # print(ret)
                            # print(self._phone_code_hash.phone_code_hash)
                            # code = input('Please insert code: ')
                            return 'code'

                    # code = await self.handle_phone_code(phone_number)

                    try:
                        await self.client.sign_in(phone=phone_number, code=code)
                    except PhoneCodeInvalidError:
                        self.logger.error("Invalid verification code. Please try again.")
                        return {'title': 'Error', 'message': 'Invalid verification code. Please try again.'}

                if await self.client.is_user_authorized():
                    self.logger.info("Successfully connected to Telegram")
                    self.isLoggedIn = True
                    return True

            except SessionPasswordNeededError:
                if not password:
                    return '2FA'
                # password = await self.handle_2fa(password)
                await self.client.sign_in(password=password)
                self.logger.info("2FA authentication successful")
                self.isLoggedIn = True
                return True
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                self.logger.error(traceback.format_exc())
                if attempt >= self.max_attempts - 1:
                    self.logger.error("Maximum connection attempts reached.")
                    return {'title': 'Error', 'message': 'Maximum connection attempts reached.'}

        return False

    async def disconnect(self):
        """Properly close the Telegram client and delete session file."""
        if self.client:
            await self.client.log_out()
            self.isLoggedIn = False
            self.logger.info("Telegram client Logged out")

    async def get_profile_info(self):
        """Get the name and profile picture of the connected account."""
        try:
            me = await self.client.get_me()

            # Get name
            self.full_name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
            sanitized_name = self.full_name.replace(" ", "_")  # Replacing spaces with underscores for filename
            self.logger.info(f"Account Name: {self.full_name}")
            self.username = me.username

            # Get profile picture
            if me.photo:
                self.profile_pic = await self._get_profile_blob(me)

                self.logger.info(f"Profile picture saved as binary for {sanitized_name}")
            else:
                self.logger.info("No profile picture found for this account.")
                self.profile_pic = b''

        except Exception as e:
            traceback_email_flatlay(
                body=f'Error fetching Telegram profile info: {str(e)}')
            self.logger.error(f"Error fetching profile info: {str(e)}")

    async def export_contacts(self) -> list:
        """Export Telegram contacts to a CSV file."""
        try:
            contacts = await self.client(GetContactsRequest(hash=0))
            contact_list = []

            for user in contacts.users:
                # Getting user profile binary photo
                blob = await self._get_profile_blob(user)
                # Uploading to aws server for showing user profile pic on front
                url = self.upload_image(blob)

                time_now = datetime.now()
                updated_at = int(datetime.timestamp(time_now) * 1000)
                contact_info = {
                    "url": f"https://telegram.me/{user.username}",
                    "updated_at": updated_at,
                    "platform": "TELEGRAM",
                    "platform_username": user.username,
                    "full_name": user.first_name + (' ' + user.last_name if user.last_name else ''),
                    "contact_details": [{"type": "phone", "value": user.phone}],
                    "external_id": user.id
                }
                # replacing to sample dict
                if url and blob:
                    try:
                        contact_info['image_url'] = url.get('standard')
                    except Exception as ex2:
                        self.logger += f'we have an exception on profile_search.assigning new url {ex2}\n'
                else:
                    self.logger += f"Couldn't get new profile image"
                contact_list.append(contact_info)
            return contact_list

        except FloodWaitError as e:
            self.logger.warning(f"Hit rate limit. Waiting for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)

        except Exception as e:
            self.logger.error(f"Error exporting contacts: {str(e)}")
            raise

    async def get_telegram_id(self, identifier: str):
        """
        Get the Telegram ID of a user, group, or channel by phone number, username, or invite link.

        Args:
            identifier (str): The phone number, username, or invite link.

        Returns:
            int: Telegram ID of the user, group, or channel, if available.
        """
        try:
            # Use Telethon's get_entity method to fetch the entity from identifier
            entity = await self.client.get_entity(identifier)

            # Return the Telegram ID
            return entity.id

        except (UsernameNotOccupiedError, UsernameInvalidError):
            self.logger.warning(f"Username, phone number, or link '{identifier}' not found or invalid.")
            return None

        except FloodWaitError as e:
            self.logger.warning(f"Hit rate limit. Waiting for {e.seconds} seconds before retrying.")
            await asyncio.sleep(e.seconds)
            return await self.get_telegram_id(identifier)  # Retry after waiting

        except Exception as e:
            self.logger.error(f"Error retrieving Telegram ID for '{identifier}': {str(e)}")
            return None

    async def send_message(self, influencer, message: str):
        """
        Send a message to a list of Telegram user IDs.

        Args:
            influencer : Telegram user IDs (as integers) and also could be username or phone number as string
            username = 'example'
            phone = '98912111111'.
            message (str): The message to send to each user.
        """
        # Send a message to the user ID
        self.function_result = ''
        try:
            if not influencer:
                self.logger.warning('telegram.send_message Influencer is None')
                self.function_result = f"Can't send message to {influencer} because his/her username | phone is None"
                return False
            await self.client.send_message(influencer, message)
            self.logger.info(f"Message sent to user ID {influencer}")
            self.function_result = f"Message has been sent to {influencer}"
            return True
        except FloodWaitError as e:
            self.logger.warning(f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            if 'reply_to_msg_id' in str(e):
                self.function_result = f"Message has been sent to {influencer}"
                return True
            self.logger.error(f"Failed to send message to {influencer}: {str(e)}")
            self.function_result = f"Can't send to {influencer} Error: {str(e)}"
        return False

    async def get_private_group_id(self, group_username):
        try:
            entity = await self.client(ResolveUsernameRequest(group_username))
            return entity.id  # ✅ Returns numeric ID
        except (UsernameNotOccupiedError, UsernameInvalidError):
            self.logger.warning(f"Username {group_username} does not exist or is invalid.")
        except Exception as e:
            self.logger.error(f"Failed to get ID for {group_username}: {e}")
        return None

    async def check_groups_permissions(self, dialogs):
        """
        Check if the user can send media in each group or channel.
        """

        for dialog in dialogs[:200]:
            entity = dialog.entity

            # Process only groups or channels
            if isinstance(entity, (Channel, Chat)):
                try:
                    entity_id = entity.id if hasattr(entity, "id") else None

                    if entity_id is None and hasattr(entity, "username") and entity.username:
                        entity_id = await self.get_private_group_id(entity.username)

                    # Skip broadcast channels where only admins can post
                    if isinstance(entity, Channel) and entity.broadcast:
                        self.logger.info(f"Skipping broadcast channel: {entity.title}")
                        continue

                    # Check if group has username...
                    group_username = str(entity_id)
                    if has_username := (hasattr(entity, "username") and entity.username):
                        group_username = entity.username
                    # Check permissions
                    time_now = datetime.now()
                    updated_at = int(datetime.timestamp(time_now) * 1000)
                    group_info = {
                        "url": f"https://t.me/{group_username}" if has_username else None,
                        "updated_at": updated_at,
                        "platform": "TELEGRAM",
                        "platform_username": group_username,
                        "full_name": entity.title,
                        "platform_account_type": "GROUP",
                        "external_id": entity_id
                    }

                    if entity.admin_rights and entity.admin_rights.post_messages:
                        # User is an admin with post message rights
                        self.sendable_chats.append(group_info)
                        self.logger.info(f"You can send media in (Admin Rights): {entity.title}")
                    elif hasattr(entity, "restriction_reason") and entity.restriction_reason:
                        # The channel/group has posting restrictions
                        self.logger.info(f"Cannot send media in (Restricted): {entity.title}")
                    else:
                        # No restrictions, assumed sendable
                        self.sendable_chats.append(group_info)
                        self.logger.info(f"You can send media in: {entity.title}")

                except Exception as e:
                    self.logger.error(f"Error while checking {entity.title}: {str(e)}")
        return self.sendable_chats

    async def check_channels_permissions(self, dialogs):
        """
        Check all channels (including broadcast) where the user can post media.
        """
        postable_channels = []  # List to store channels where posting is allowed

        for dialog in dialogs[:200]:
            entity = dialog.entity

            # Process only channels
            if isinstance(entity, Channel):
                try:

                    entity_id = entity.id if hasattr(entity, "id") else None

                    if entity_id is None and hasattr(entity, "username") and entity.username:
                        entity_id = await self.get_private_group_id(entity.username)

                    # Fetch participant details to verify permissions
                    participant = await self.client(GetParticipantRequest(entity.id, 'me'))

                    time_now = datetime.now()
                    updated_at = int(datetime.timestamp(time_now) * 1000)
                    # Prepare the channel info dictionary
                    channel_info = {
                        "url": f"https://t.me/{entity.username}",
                        "updated_at": updated_at,
                        "platform": "TELEGRAM",
                        "platform_username": entity.username or str(entity.id),
                        "full_name": entity.title,
                        "platform_account_type": "CHANNEL",
                        "external_id": entity_id
                    }

                    # Check if the user is an admin (or creator) with post permissions
                    if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                        postable_channels.append(channel_info)
                        self.logger.info(f"You can post media in (Admin Rights): {entity.title}")

                except UserNotParticipantError:
                    self.logger.warning(f"You are not a member of: {entity.title}")
                except ChannelPrivateError:
                    self.logger.warning(f"The channel {entity.title} is private.")
                except Exception as e:
                    self.logger.error(f"Error while checking channel {entity.title}: {str(e)}")

        self.sendable_chats.extend(postable_channels)
        return postable_channels

    async def export_groups(self):
        """Export Telegram groups (name, id, and link) to a CSV file, handling pagination and rate limits."""
        try:
            self.sendable_chats = []
            dialogs = await self.client.get_dialogs()
            await self.check_groups_permissions(dialogs)
            await self.check_channels_permissions(dialogs)

            return self.sendable_chats

        except Exception as e:
            self.logger.error(f"Error exporting groups and channels: {str(e)}")
            raise e

    def fetch_media(self, media_url: str):
        """Fetch media from a URL with improved filename handling."""
        self.logger.info(f"Fetching media from: {media_url}")
        response = requests.get(media_url,
                                proxies={'http': getproxies().get('http'),
                                         'https': getproxies().get('http')},
                                stream=True)
        if response.status_code != 200:
            self.logger.error(f"Failed to fetch media: {response.status_code}")
            raise ValueError("Failed to fetch media.")

        self.logger.debug("Media fetched successfully.")
        media_stream = BytesIO(response.content)

        # Handle content type
        content_type = response.headers.get('content-type')

        # Generate a default filename with proper extension
        extension = mimetypes.guess_extension(content_type) if content_type else '.jpg'
        if not extension:
            extension = '.jpg'  # Fallback extension for images

        default_filename = f"media{extension}"

        # Try to get filename from URL, fallback to default if none found
        file_name = media_url.split("/")[-1]
        if not file_name or not '.' in file_name:
            file_name = default_filename

        self.logger.debug(f"Using file name: {file_name} with content type: {content_type}")
        return media_stream, file_name, content_type

    def infer_and_generate_file_name(self, file_name: str, content_type: str = None) -> str:
        """Generate a unique file name with improved extension handling."""
        if not file_name:
            self.logger.error("File name is None or empty.")
            extension = mimetypes.guess_extension(content_type) if content_type else '.jpg'
            file_name = f"media{extension}"

        # Ensure we have an extension
        if '.' not in file_name:
            extension = mimetypes.guess_extension(content_type) if content_type else '.jpg'
            file_name = f"{file_name}{extension}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = file_name.rsplit('.', 1)
        return f"{name}_{timestamp}.{ext}"

    def parse_schedule_time(self, schedule_time: str) -> int:
        """Parse and validate the schedule time in ISO 8601 format."""
        try:
            # Using fromisoformat for ISO 8601 parsing
            dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))  # Adjust for UTC if Z is present
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)  # Set UTC if no timezone provided
            return int(dt.timestamp())
        except ValueError as e:
            logger.error(f"Invalid ISO 8601 schedule_time format: {schedule_time}")
            raise ValueError(f"Invalid schedule_time format: {e}")

    def validate_future_time(self, schedule_timestamp: int):
        """Ensure the schedule timestamp is in the future.

        Args:
            schedule_timestamp: The Unix timestamp to validate.

        Raises:
            ValueError: If the schedule time is not in the future.
        """
        current_timestamp = int(time.time())
        if schedule_timestamp <= current_timestamp:
            logger.error(f"schedule_time is not in the future: {schedule_timestamp}")
            traceback_email_flatlay(
                body=f"schedule_time is not in the future: {schedule_timestamp}")
            raise ValueError("Schedule time must be in the future.")

    async def schedule_media_message(self, chat_id, media_stream, schedule_timestamp, caption, isScheduled):
        """Send the media with scheduling.

        Args:
            client: The Telegram client instance.
            chat_id: ID of the chat where the media should be sent.
            media_stream: The media stream to send.
            schedule_timestamp: The Unix timestamp for scheduling the message.
            caption: Optional caption for the media.
        """
        logger.debug(f"Calling send_file with schedule_date: {schedule_timestamp}")
        if isScheduled:
            await self.client.send_file(
                chat_id,
                file=media_stream,
                caption=caption,
                schedule=schedule_timestamp
            )
        else:
            await self.client.send_file(
                chat_id,
                file=media_stream,
                caption=caption,
            )

    async def send_message_post(self, chat_id, schedule_time: str, isScheduled=True, caption=None):
        """Send the media with scheduling."""
        try:
            schedule_timestamp = int(datetime.fromisoformat(schedule_time.replace("Z", "+00:00")).timestamp())
            if isScheduled:
                await self.client.send_message(
                    chat_id,
                    message=caption,
                    schedule=schedule_timestamp
                )
            else:
                await self.client.send_message(
                    chat_id,
                    message=caption,
                )
        except Exception as e:
            logger.error(f"Failed to send message post: {e}")
            traceback_email_flatlay(
                body=f"Failed to send message post: {e}")

    async def send_media_post(self, chat_id, media_url, schedule_time: str, isScheduled=True, caption=None):
        """
        Main function to send a scheduled post.

        Args:
            client: The Telegram client instance.
            chat_id: ID of the chat where the media should be sent.
            media_url: URL of the media to fetch.
            schedule_time: The time to schedule the message in the format 'YYYY-MM-DD HH:MM:SS' (UTC).
            caption: Optional caption for the media.

        Raises:
            ValueError: If the schedule_time is not in the correct format or is not in the future.
        """
        try:
            logger.info("Starting scheduled media sending process.")
            logger.debug(
                f"Received parameters - chat_id: {chat_id}, media_url: {media_url}, schedule_time: {schedule_time}, caption: {caption}")

            # Validate and parse schedule time
            schedule_timestamp = int(datetime.fromisoformat(schedule_time.replace("Z", "+00:00")).timestamp())

            # Fetch media
            media_stream, file_name, content_type = self.fetch_media(media_url)
            logger.debug(f"Fetched media with file_name: {file_name} and content_type: {content_type}")

            # Generate unique file name
            unique_file_name = self.infer_and_generate_file_name(file_name, content_type)
            logger.debug(f"Generated unique file name: {unique_file_name}")
            media_stream.name = unique_file_name

            # Schedule the media
            await self.schedule_media_message(chat_id, media_stream, schedule_timestamp, caption, isScheduled)

            logger.info(f"Media scheduled successfully to chat ID {chat_id} at {schedule_time}.")
        except Exception as e:
            traceback_email_flatlay(
                body=f'Error in Telegram.send_scheduled_post: {str(e)}')
            logger.error(f"Error in send_scheduled_post: {str(e)}")

    async def send_group_media_post(self, chat_id, media_urls, schedule_time: str = None,
                                    isScheduled: bool = True, caption: str = None):
        """
        Send media files (images or videos) from URLs directly to Telegram without saving locally.

        Args:
            client: The Telethon client instance.
            chat_id: The chat ID where the media should be sent.
            media_urls: List of media URLs to send.
            caption: Optional caption for the media.
        """
        try:
            logger.info(f"Preparing to send media to chat ID {chat_id}.")
            media_files = []

            schedule_timestamp = None
            if isScheduled and schedule_time:
                try:
                    schedule_timestamp = int(datetime.fromisoformat(
                        schedule_time.replace("Z", "+00:00")).timestamp())
                except ValueError as e:
                    raise ValueError(f"Invalid schedule_time format: {e}")

            for idx, media_url in enumerate(media_urls):
                try:
                    # Fetch the media from the URL
                    logger.info(f"Fetching media from URL: {media_url}")
                    response = requests.get(media_url, stream=True)
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch media from {media_url}, status code: {response.status_code}")
                        continue

                    # Extract content type
                    content_type = response.headers.get('Content-Type')
                    logger.debug(f"Content type of media: {content_type}")

                    # Guess file extension based on content type
                    extension = mimetypes.guess_extension(content_type) or '.dat'
                    unique_id = datetime.now().strftime("%Y%m%d_%H%M%S%f")  # Unique timestamp up to microseconds
                    file_name = f"flatlay_{unique_id}{extension}"

                    # Wrap the media content in BytesIO
                    media_stream = BytesIO(response.content)
                    media_stream.name = file_name  # Required by Telethon

                    # Append to the list of media files
                    media_files.append(
                        {"file": media_stream, "caption": caption if idx == 0 else None})
                    logger.info(f"Media from {media_url} prepared successfully.")
                except Exception as e:
                    logger.error(f"Error processing URL {media_url}: {e}")

            if not media_files:
                raise ValueError("No valid media files to send.")

            # Send media group to Telegram
            logger.info(f"Sending {len(media_files)} media files to chat ID {chat_id}.")
            await self.client.send_file(
                entity=chat_id,
                file=[media["file"] for media in media_files],
                caption=[caption] if caption else None,
                schedule=schedule_timestamp if isScheduled else None
            )
            logger.info(f"Media sent successfully to chat ID {chat_id}.")
        except Exception as e:
            logger.error(f"Error in send_group_media_post: {str(e)}")
            raise

    async def process_direct_message(self, chat_id: int):
        """
        Args:
            chat_id (int): The numeric Telegram ID of the user.
        """
        try:
            messages = await self.client.get_messages(chat_id, limit=50)  # Fetch last 50 messages
            messages.reverse()

            result = []
            outbound_found = False

            for message in messages:
                if isinstance(message, Message):
                    message_data = {
                        "body": message.text or "[MEDIA]",
                        "type": "OUTBOUND" if message.out else "INBOUND",
                        "timestamp": message.date.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    if message.out:
                        result = [message_data]
                        outbound_found = True
                    elif outbound_found:
                        result.append(message_data)  

            if result and result[0]["type"] == "OUTBOUND" and len(result) == 1:
                return []

            return result

        except Exception as e:
            logger.error(f"Failed to fetch messages for user {chat_id}: {e}")
            return []


async def main():
    """ just use it just for a cli test and should delete after in production"""
    parser = argparse.ArgumentParser(description='Telegram Scraper')

    # Command-line arguments
    parser.add_argument('--api_id', required=True, help='RestAPI ID from Telegram')
    parser.add_argument('--api_hash', required=True, help='RestAPI Hash from Telegram')
    parser.add_argument('--phone', required=True, help='Phone number linked to your Telegram account')
    parser.add_argument('--code', help='Verification code sent to your phone')
    parser.add_argument('--password', help='Two-step verification password, if enabled')

    args = parser.parse_args()

    # Load RestAPI credentials
    API_ID = args.api_id
    API_HASH = args.api_hash
    PHONE = args.phone
    CODE = args.code
    PASSWORD = args.password

    exporter = Telegram(API_ID, API_HASH)

    try:
        # Connect to Telegram
        result = await exporter.connect(PHONE, CODE, PASSWORD)
        if isinstance(result, dict):
            exporter.logger.info(f"{result['title']} {result['message']}")
        elif isinstance(result, bool) and result:
            exporter.logger.info('Authentication was successful')
        elif isinstance(result, str):
            code = input(f'Please insert {result}')
            if 'code' in result:
                result = await exporter.connect(PHONE, code, PASSWORD)
            elif '2FA' in result:
                result = await exporter.connect(PHONE, password=code)
        exporter.logger.info(f'last result is {result}')
        exit()
        if not await exporter.connect(PHONE, CODE, PASSWORD):
            exporter.logger.error("Failed to connect to Telegram")
            return

        # Get profile information (name and profile picture)
        await exporter.get_profile_info()

        # Export contacts
        contacts = await exporter.export_contacts()

        # Print summary
        exporter.logger.info("\nContact Export Summary:")
        exporter.logger.info(f"Total contacts exported: {len(contacts)}")
        exporter.logger.info(f"Output file: telegram_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    except Exception as e:
        exporter.logger.error(f"An error occurred: {str(e)}")

    finally:
        await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
