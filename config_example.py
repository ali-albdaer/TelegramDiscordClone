# Telegram & Discord Configuration
telegram_user = 'example_user'
telegram_phone = '+1234567890'
telegram_group_id = -1234567890  # Telegram group ID (can be obtained using a bot like @userinfobot)

api_id = '12345678'  # Telegram API ID (visit my.telegram.org to get this)
api_hash = 'abcdef1234567890'  # Telegram API Hash (visit my.telegram.org to get this as well)

discord_webhook_url = 'https://discord.com/api/webhooks/your-webhook-url'  # Webhook URL for the backup channel.
default_avatar_url = 'https://http.cat/404'  # Default avatar URL for users without a profile picture.


# Parameters
IGNORE_VIDEO_FILES = False
CLONE_MEDIA_ONLY = False  # Only clone messages that have media attached.
SHOW_USER_INFO = True  # Include the sender's name and profile picture in the Discord message.
SHOW_PROGRESS_BAR = True  # Show an `estimate` progress bar in the console.
IGNORE_SYSTEM_MESSAGES = True  # (e.g. user joined, user left, etc.)


# Rate Limiting
LINEAR_SLEEP_FACTOR = 2  # Increase the sleep time after each rate limit by this factor. Hihger value is recommended for larger groups.
MAX_SLEEP_TIME = 60  # Maximum sleep time after rate limit (in seconds).


# File Paths
temp_folder = 'temp/'  # Folder to temporarily store temporary files
avatar_folder = 'temp/avatars'  # Folder to store profile pictures
temporary_data_file = 'temp/temp.json'  # File to store the last processed message ID
