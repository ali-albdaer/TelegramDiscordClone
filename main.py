import os
import asyncio
import json
import logging
import requests
from telethon import TelegramClient, types
from discord import SyncWebhook, File

from config import *


logging.basicConfig(level=logging.WARNING)


LAST_PROCESSED_FILE = 'last_processed_message.json'
telegram_client = TelegramClient(telegram_user, api_id, api_hash)
discord_webhook = SyncWebhook.from_url(discord_webhook_url)
avatar_webhook = SyncWebhook.from_url(avatar_webhook_url)
downloaded_profile_pics = {}


def save_last_processed_message_id(message_id):
    with open(LAST_PROCESSED_FILE, 'w') as file:
        json.dump({'last_processed_message_id': message_id}, file)


def load_last_processed_message_id():
    if os.path.exists(LAST_PROCESSED_FILE):
        with open(LAST_PROCESSED_FILE, 'r') as file:
            data = json.load(file)
            return data.get('last_processed_message_id', 0)
    return 0


async def fetch_sender_details(message):
    try:
        sender = await message.get_sender()
        sender_id = sender.id

        if sender_id not in downloaded_profile_pics:
            if sender.photo:
                photo = await telegram_client.get_profile_photos(sender)
                photo = photo[-1]
                photo_file_name = f'{sender_id}.jpg'
                photo_path = os.path.join(avatar_folder, photo_file_name)
                
                if not os.path.exists(photo_path):
                    await telegram_client.download_media(photo, file=photo_path)

                message = avatar_webhook.send(file=File(photo_path), username=sender.first_name or sender.username or "Unknown", wait=True)
                downloaded_profile_pics[sender_id] = message.attachments[0].url

            else:
                downloaded_profile_pics[sender_id] = None
        
        return downloaded_profile_pics[sender_id], sender.first_name or sender.username or "Unknown"
    
    except Exception as e:
        logging.error(f'[in fetch_sender_details]: {e}')
        return None, None


async def download_media_message(message):
    try:
        if ignore_video_files and message.media and isinstance(message.media, types.MessageMediaDocument):
            logging.warning(f'Skipping video file: {message.id}')
            return None
    
        file_path = await message.download_media(file=media_folder)
        return file_path
    
    except Exception as e:
        logging.error(f'[in download_media_message]: {e}')
        return None
    

async def upload_to_discord(file_path=None, content=None, sender_profile_pic_url=None, sender_name=None):
    try:
        payload = {}

        if content:
            payload['content'] = content

        if sender_profile_pic_url and sender_name:
            payload['username'] = sender_name
            payload['avatar_url'] = sender_profile_pic_url

        if file_path is not None:
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(discord_webhook_url, files=files, data=payload)

        else:
            response = requests.post(discord_webhook_url, data=payload)

        if response.status_code not in (200, 204):
            logging.error(f'Failed to upload file to Discord. Status code: {response.status_code}, Response: {response.text}')

        if file_path is not None:
            os.remove(file_path)
            
    except Exception as e:
        logging.error(f'[in upload_to_discord]: {e}')


async def download_and_upload_media():
    logging.info('Connecting to Telegram...')
    await telegram_client.connect()

    if not await telegram_client.is_user_authorized():
        await telegram_client.send_code_request(telegram_phone)
        await telegram_client.sign_in(telegram_phone, input('Enter the code you received on Telegram: '))

    else:
        logging.info('Telegram client is already authorized. Skipping authentication.')

    logging.info('Fetching group entity...')
    try:
        group_entity = await telegram_client.get_entity(telegram_group_id)
        logging.info(f'Group entity fetched.')
    except Exception as e:
        logging.error(f'[in download_and_upload_media]: [fetching group entity]: {e}')
        await telegram_client.disconnect()
        return

    last_processed_message_id = load_last_processed_message_id()
    total_messages = (await telegram_client.get_messages(group_entity, limit=0)).total
    processed_messages = 0

    try:
        async for message in telegram_client.iter_messages(group_entity, min_id=last_processed_message_id, reverse=True):
            if upload_messages_with_media_only and not message.media:
                continue

            if message.media:
                file_path = await download_media_message(message)

            else:
                file_path = None

            if include_user_data:
                sender_profile_pic_url, sender_name = await fetch_sender_details(message)

            else:
                sender_profile_pic_url, sender_name = None, None
                
            await upload_to_discord(file_path, message.text, sender_profile_pic_url, sender_name)
            await asyncio.sleep(1)

            save_last_processed_message_id(message.id)
            processed_messages += 1
            print(f'Processed: [{processed_messages} / {total_messages}]', end='\r')

    except Exception as e:
        logging.error(f'[in download_and_upload_media]: [message iteration]: {e}')

    if os.path.exists(LAST_PROCESSED_FILE):
        logging.info('Removing last_processed_file...')
        os.remove(LAST_PROCESSED_FILE)

    print('[Program Finished. Disconnecting from Telegram]')
    await telegram_client.disconnect()


if __name__ == '__main__':
    asyncio.run(download_and_upload_media())
