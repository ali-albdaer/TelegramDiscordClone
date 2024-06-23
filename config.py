# Telegram & Discord Configuration
telegram_user = 'user_name'  # Telegram username
telegram_phone = '+10000000'  # Telegram phone number
api_id = '9999999'  # Telegram API ID (visit my.telegram.org to get this)
api_hash = '999deadbeef9999eeeeee'  # Telegram API Hash (visit my.telegram.org to get this as well)
discord_webhook_url = 'https://discord.com/api/webhooks/...'  # Webhook URL for the backup channel
avatar_webhook_url = 'https://discord.com/api/webhooks/...'  # Webhook URL for a helper channel

# File Paths
media_folder = 'media/'  # Folder to temporarily store media files
avatar_folder = 'avatars/'  # Folder to store profile pictures

# Parameters
telegram_group_id = -40000000  # Telegram group ID (can be obtained using a bot like @userinfobot)
ignore_video_files = False  # Set to True to ignore video files
upload_messages_with_media_only = False  # Set to True to only clone messages that have media attached
include_user_data = True  # Set to True to include the sender's name and profile picture in the Discord message
