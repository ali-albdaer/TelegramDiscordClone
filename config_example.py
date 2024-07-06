# Telegram & Discord Configuration
telegram_user = 'example_user'  # Telegram username
telegram_phone = '+1234567890'  # Telegram phone number
telegram_group_id = -1234567890  # Telegram group ID (can be obtained using a bot like @userinfobot)
api_id = '12345678'  # Telegram API ID (visit my.telegram.org to get this)
api_hash = 'abcdef1234567890'  # Telegram API Hash (visit my.telegram.org to get this as well)
discord_webhook_url = 'https://discord.com/api/webhooks/your-webhook-url'  # Webhook URL for the backup channel
default_avatar_url = 'https://http.cat/404'  # Default avatar URL for users without a profile picture


# Parameters
IGNORE_VIDEO_FILES = False
UPLOAD_MESSAGES_WITH_MEDIA_ONLY = False  # Set to True to only clone messages that have media attached
INCLUDE_USER_DATA = True  # Set to True to include the sender's name and profile picture in the Discord message
SHOW_PROGRESS_BAR = True  # Set to True to show an `estimate` progress bar.
IGNORE_SYSTEM_MESSAGES = True  # Set to True to ignore system messages (e.g. user joined, user left, etc.)
SLEEP_OFFSET = 10.0  # Time in seconds to wait after being rate limited by the APIs. Higher value is recommended for larger groups.

# File Paths
temp_folder = 'temp/'  # Folder to temporarily store temporary files
avatar_folder = 'temp/avatars'  # Folder to store profile pictures
temporary_data_file = 'temp/temp.json'  # File to store the last processed message ID
