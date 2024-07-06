import os
import shutil
import asyncio
import json
import logging
import requests
from telethon import TelegramClient, types
from discord import SyncWebhook, File
from config import *


logging.basicConfig(level=logging.WARNING)  # Change to logging.INFO if you like chaos.


if not os.path.exists('temp'):
    os.makedirs('temp')


if not os.path.exists(avatar_folder):
    os.makedirs(avatar_folder)


class TelegramDiscordBot:
    def __init__(self):
        self.telegram_client = TelegramClient(f'{telegram_user}.session', api_id, api_hash)
        self.discord_webhook = SyncWebhook.from_url(discord_webhook_url)
        self.downloaded_profile_pics, self.last_processed_message_id = self.load_last_processed_data()

    def save_last_processed_data(self, message_id):
        data = {
            'last_processed_message_id': message_id,
            'downloaded_profile_pics': {str(k): v for k, v in self.downloaded_profile_pics.items()}
        }
        with open(temporary_data_file, 'w') as file:
            json.dump(data, file)


    def load_last_processed_data(self):
        if os.path.exists(temporary_data_file):
            try:
                with open(temporary_data_file, 'r') as file:
                    data = json.load(file)
                    return {int(k): v for k, v in data.get('downloaded_profile_pics', {}).items()}, data.get('last_processed_message_id', 0)
            
            except json.JSONDecodeError as e:
                logging.error(f'[in load_last_processed_data]: JSON decode error: {e}')
                return {}, 0
        return {}, 0


    async def fetch_sender_details(self, message):
        try:
            sender = await message.get_sender()
            sender_id = sender.id
            
            if message.sender:
                if message.sender.first_name:
                    username = message.sender.first_name + (' ' + message.sender.last_name if message.sender.last_name else '')

                elif message.sender.username:
                    username = message.sender.username

                else:  # Could be unnecessary but just in case.
                    username = 'Unknown User'

            else:
                username = 'Unknown User'

            if sender_id not in self.downloaded_profile_pics:
                if sender.photo:
                    photos = await self.telegram_client.get_profile_photos(sender)
                    photo = photos[0]

                    photo_file_name = f'{sender_id}.jpg'
                    photo_path = os.path.join(avatar_folder, photo_file_name)
                    
                    if not os.path.exists(photo_path):
                        await self.telegram_client.download_media(photo, file=photo_path)

                    message = self.discord_webhook.send(file=File(photo_path), username=f"{username} joined the group.", wait=True)
                    self.downloaded_profile_pics[sender_id] = message.attachments[0].url

                else: # Get the default profile pic instead
                    self.discord_webhook.send(default_avatar_url, username=f"{username} joined the group.")
                    self.downloaded_profile_pics[sender_id] = default_avatar_url

                await asyncio.sleep(1)

            return self.downloaded_profile_pics[sender_id], username
        
        except Exception as e:
            logging.error(f'[in fetch_sender_details]: {e}')
            return None, None

    async def download_media_message(self, message):
        try:
            if IGNORE_VIDEO_FILES and message.media and isinstance(message.media, types.MessageMediaDocument):
                logging.warning(f'Skipping video file: {message.id}')
                return None
        
            file_path = await message.download_media(file=temp_folder)
            return file_path
        
        except Exception as e:
            logging.error(f'[in download_media_message]: {e}')
            return None

    async def upload_to_discord(self, file_path=None, content=None, sender_profile_pic_url=None, sender_name=None):
        try:
            payload = {}

            if content:
                payload['content'] = content

            if sender_name:
                payload['username'] = sender_name

            if sender_profile_pic_url:
                payload['avatar_url'] = sender_profile_pic_url
            
            if file_path is not None:
                with open(file_path, 'rb') as file:
                    files = {'file': file}
                    response = requests.post(discord_webhook_url, files=files, data=payload)
            else:
                response = requests.post(discord_webhook_url, data=payload)

            if response.status_code == 400:
                logging.warning('[Ignoring message with no content or attachments]')

            elif response.status_code not in (200, 204):
                logging.error(f'Failed to upload file to Discord. Status code: {response.status_code}, Response: {response.text}')

            if file_path is not None:
                os.remove(file_path)
                
        except Exception as e:
            logging.error(f'[in upload_to_discord]: {e}')

    async def download_and_upload_media(self):
        logging.info('Connecting to Telegram...')
        await self.telegram_client.connect()

        if not await self.telegram_client.is_user_authorized():
            await self.telegram_client.send_code_request(telegram_phone)
            await self.telegram_client.sign_in(telegram_phone, input('Enter the code you received on Telegram: '))
        else:
            logging.info('Telegram client is already authorized. Skipping authentication.')

        logging.info('Fetching group entity...')

        try:
            group_entity = await self.telegram_client.get_entity(telegram_group_id)
            logging.info(f'Group entity fetched.')

        except Exception as e:
            logging.error(f'[in download_and_upload_media]: [fetching group entity]: {e}')
            await self.telegram_client.disconnect()
            return

        if SHOW_PROGRESS_BAR:  # Maybe this is too much for a progress bar. 
            latest_message = await self.telegram_client.get_messages(group_entity, limit=1)
            first_message = await self.telegram_client.get_messages(group_entity, limit=1, reverse=True)

            latest_message_id = latest_message[0].id if latest_message else 0
            first_message_id = first_message[0].id if first_message else 0
            
            total_messages = latest_message_id - (self.last_processed_message_id or first_message_id)
            processed_messages = 0

        try:
            async for message in self.telegram_client.iter_messages(group_entity, min_id=self.last_processed_message_id, reverse=True):
                if UPLOAD_MESSAGES_WITH_MEDIA_ONLY and not message.media:
                    continue

                if message.media:
                    file_path = await self.download_media_message(message)
                else:
                    file_path = None

                if INCLUDE_USER_DATA:
                    sender_profile_pic_url, sender_name = await self.fetch_sender_details(message)
                else:
                    sender_profile_pic_url, sender_name = None, None

                await self.upload_to_discord(file_path, message.text, sender_profile_pic_url, sender_name)
                await asyncio.sleep(1)

                self.save_last_processed_data(message.id)
                processed_messages += 1

                if SHOW_PROGRESS_BAR:
                    print(f'\rProcessed Messages: [{processed_messages} / {total_messages}]', end='')

            if SHOW_PROGRESS_BAR:
                print()

        except Exception as e:
            logging.error(f'[in download_and_upload_media]: [message iteration]: {e}')

        else:
            if os.path.exists(temp_folder):
                logging.info('Removing temp data...')
                shutil.rmtree(temp_folder)

            logging.info('[Program Finished. Disconnecting from Telegram]')
            await self.telegram_client.disconnect()

    async def run(self):
        await self.download_and_upload_media()


if __name__ == '__main__':
    bot = TelegramDiscordBot()
    asyncio.run(bot.run())
