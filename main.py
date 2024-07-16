import os
import re
import shutil
import asyncio
import json
import logging
import requests
from telethon import TelegramClient, types, errors
from discord import SyncWebhook, File
from config import *


logging.basicConfig(level=logging.INFO)  # Change to logging.WARNING for less detailed logs.


os.makedirs('temp', exist_ok=True)
os.makedirs(avatar_folder, exist_ok=True)


class TelegramDiscordBot:
    def __init__(self):
        self.telegram_client = TelegramClient(f'{telegram_user}.session', api_id, api_hash)
        self.discord_webhook = SyncWebhook.from_url(discord_webhook_url)
        self.downloaded_profile_pics, self.last_processed_message_id = self.load_last_processed_data()
        self.rate_limit_count = 0

    # Calculates how many seconds to sleep based on how many times the bot has been rate limited. (linearly increases.)
    async def sleep(self, base_sleep_time):
        self.rate_limit_count += 1
        sleep_time = max(self.rate_limit_count * LINEAR_SLEEP_FACTOR, base_sleep_time)
        logging.warning(f'Sleeping for {sleep_time} seconds due to rate limit...')
        await asyncio.sleep(sleep_time)

        if sleep_time == MAX_SLEEP_TIME:
            self.rate_limit_count = 0

    # Ensures that the last processed message ID is saved in case of a program crash / halt.
    def save_last_processed_data(self, message_id):
        data = {
            'last_processed_message_id': message_id,
            'downloaded_profile_pics': {str(k): v for k, v in self.downloaded_profile_pics.items()}
        }
        with open(temporary_data_file, 'w') as file:
            json.dump(data, file)

    # Loads the last processed message ID and downloaded profile pictures from the temporary data file.
    def load_last_processed_data(self):
        if os.path.exists(temporary_data_file):
            try:
                with open(temporary_data_file, 'r') as file:
                    data = json.load(file)
                    return {int(k): v for k, v in data.get('downloaded_profile_pics', {}).items()}, data.get('last_processed_message_id', 0)
            except json.JSONDecodeError as e:
                logging.error(f'[load_last_processed_data] JSON decode error: {e}')
                return {}, 0
        return {}, 0

    # Fetches the sender's profile picture and name from the Telegram message.
    async def fetch_sender_details(self, message):
        try:
            sender = await message.get_sender()
            if not sender:
                return None, 'Deleted User'
            
            sender_id = sender.id
            username = (
                sender.first_name + (' ' + sender.last_name if sender.last_name else '') if sender.first_name else 
                sender.username if sender.username else 
                'Unknown User'
            )

            if sender_id not in self.downloaded_profile_pics:
                if sender.photo and (photos := await self.telegram_client.get_profile_photos(sender)):
                    photo = photos[0]
                    photo_file_name = f'{sender_id}.jpg'
                    photo_path = os.path.join(avatar_folder, photo_file_name)
                    if not os.path.exists(photo_path):
                        await self.telegram_client.download_media(photo, file=photo_path)
                    message = self.discord_webhook.send(file=File(photo_path), username=f"{username}'s Profile Picture", wait=True)
                    self.downloaded_profile_pics[sender_id] = message.attachments[0].url
                    
                else:
                    fallback_avatar_url = f'https://dummyimage.com/640x640/{sender_id}/000000.png&text={username[0]}'
                    response = requests.get(fallback_avatar_url)

                    if response.status_code == 200:
                        self.downloaded_profile_pics[sender_id] = fallback_avatar_url

                    else:
                        self.downloaded_profile_pics[sender_id] = default_avatar_url

                    self.discord_webhook.send(fallback_avatar_url, username=f"{username} Has No Profile Picture.")

                await asyncio.sleep(1.01)

            return self.downloaded_profile_pics[sender_id], username
        
        except Exception as e:
            logging.error(f'[fetch_sender_details] {e}')
            return None, None

    # Downloads the media file from the Telegram message.
    async def download_media_message(self, message):
        try:
            if IGNORE_VIDEO_FILES and message.media and isinstance(message.media, types.MessageMediaDocument):
                logging.warning(f'Skipping video file: {message.id}')
                return

            file_path = await message.download_media(file=temp_folder)
            return file_path
        
        except Exception as e:
            logging.error(f'[download_media_message] {e}')
            return

    # Uploads the message content and media file to Discord.
    async def upload_to_discord(self, file_path=None, content=None, sender_profile_pic_url=None, sender_name=None):
        try:
            payload = {
                'content': content,
                'username': sender_name,
                'avatar_url': sender_profile_pic_url
            }

            while True:
                if file_path is not None:
                    with open(file_path, 'rb') as file:
                        files = {'file': file}
                        response = requests.post(discord_webhook_url, files=files, data=payload)
                else:
                    response = requests.post(discord_webhook_url, data=payload)

                if response.status_code == 429:
                    retry_after = response.json().get('retry_after', 1)  # Default to 1 seconds if not provided
                    await self.sleep(retry_after)

                elif response.status_code in {400, 403}:
                    logging.warning(f'[Ignoring message with no content or attachments] Status code: {response.status_code}, Response: {response.text}')
                    break

                elif response.status_code not in {200, 204}:
                    logging.error(f'Failed to upload file to Discord. Status code: {response.status_code}, Response: {response.text}')
                    break

                else:
                    break

            if file_path is not None and os.path.exists(file_path) and not KEEP_MEDIA_FILES:
                os.remove(file_path)

        except Exception as e:
            logging.error(f'[upload_to_discord] {e}')

    # Processes the Telegram message and uploads it to Discord.
    async def process_message(self, message):
        if isinstance(message, types.MessageService) and not IGNORE_SYSTEM_MESSAGES:
            content = self.handle_service_message(message)

        else:
            content = message.text.encode('utf-8').decode('utf-8') if message.text else None
        
        if CLONE_MEDIA_ONLY and not message.media:
            return
        
        if content:
            # Pattern for matching mentions, [name](tg://user?id=id) -> **name**
            pattern = r'\[(.*?)\]\(tg://user\?id=(\d+)\)'
            match = re.search(pattern, content)

            if match:
                name = match.group(1)
                content = re.sub(pattern, f"**{name}**", content)

        elif not message.media:
            return

        file_path = await self.download_media_message(message) if message.media else None
        sender_profile_pic_url, sender_name = await self.fetch_sender_details(message) if SHOW_USER_INFO else (None, None)

        await self.upload_to_discord(file_path, content, sender_profile_pic_url, sender_name)
        await asyncio.sleep(1.20)
        self.save_last_processed_data(message.id)

    # Handles service messages (e.g. user joined, user left, etc.)
    def handle_service_message(self, message):
        if message.action:
            if isinstance(message.action, types.MessageActionChatAddUser):
                users = ', '.join([str(user_id) for user_id in message.action.users])
                return f"`<<< SYSTEM >>>: {users} joined the chat.`"
            
            elif isinstance(message.action, types.MessageActionChatCreate):
                return f"`<<< SYSTEM >>>: Chat created with title: {message.action.title}`"
            
            
            elif isinstance(message.action, types.MessageActionChatJoinedByLink):
                return f"`<<< SYSTEM >>>: User joined the chat via invite link.`"
            
            
            elif isinstance(message.action, types.MessageActionChatDeleteUser):
                return f"`<<< SYSTEM >>>: User was removed from the chat.`"

    # Connects to Telegram, downloads messages, and uploads them to Discord.
    async def run(self):
        logging.info('Connecting to Telegram...')
        await self.telegram_client.connect()

        try:
            if not await self.telegram_client.is_user_authorized():
                await self.telegram_client.send_code_request(telegram_phone)
                await self.telegram_client.sign_in(telegram_phone, input('Enter the code you received on Telegram: '))
            else:
                logging.info('Telegram client is already authorized.')

            group_entity = await self.telegram_client.get_entity(telegram_group_id)
            logging.info('Group entity fetched.')

            if SHOW_PROGRESS_BAR:
                latest_message = await self.telegram_client.get_messages(group_entity, limit=1)
                first_message = await self.telegram_client.get_messages(group_entity, limit=1, reverse=True)

                latest_message_id = latest_message[0].id if latest_message else 0
                first_message_id = first_message[0].id if first_message else 0
                processed_messages = 0

            batch_size = 100
            min_id = self.last_processed_message_id

            while True:
                messages = await self.telegram_client.get_messages(group_entity, min_id=min_id, limit=batch_size, reverse=True)
                if not messages:
                    break

                for message in messages:
                    await self.process_message(message)
                    processed_messages += 1

                    if SHOW_PROGRESS_BAR:
                        if latest_message_id and first_message_id:  # Avoid division by zero for the first message.
                            percentage = round(((message.id - first_message_id) / (latest_message_id - first_message_id)) * 100, 2)
                            print(f'\rProcessed Messages: [{message.id - first_message_id} / {latest_message_id - first_message_id}] [{percentage}%]', end='')

                    min_id = message.id

                await asyncio.sleep(1.01)

            if SHOW_PROGRESS_BAR:
                print()

        except errors.FloodWaitError as e:
            await self.sleep(e.seconds)

        except Exception as e:
            logging.error(f'[run] {e}')

        finally:
            logging.info('Disconnecting from Telegram...')
            await self.telegram_client.disconnect()


if __name__ == '__main__':
    bot = TelegramDiscordBot()

    try:
        asyncio.run(bot.run())

    except KeyboardInterrupt:
        logging.info('Exiting... [Keyboard Interrupt]')

    except Exception as e:
        logging.error(f'Exiting... [Fatal Error]: {e}')
        
    else:
        logging.info('Exisitng... [Program Finished.]')
        
        if CLEAR_TEMP_FOLDER:
            shutil.rmtree('temp', ignore_errors=True)
