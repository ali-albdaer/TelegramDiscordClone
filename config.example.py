
development = False  # Set to True to enable development mode. This will use the development Discord webhook and Telegram group ID.
default_avatar_url = 'https://http.cat/404'  # Default avatar URL for users without a profile picture.


### CREDENTIALS ###

# Only configure these if you are not using environment variables. Everything outside of this block is still required.
# Check `.env.example` for more information.

telegram_user = 'example_user'
telegram_phone = '+1234567890'

api_id = '12345678'  # Telegram API ID (visit my.telegram.org to get this)
api_hash = 'abcdef1234567890'  # Telegram API Hash (visit my.telegram.org to get this as well)

if development:
    telegram_group_id = -1234567890  # Telegram group ID (can be obtained using a bot like @userinfobot)
    discord_webhook_url = 'https://discord.com/api/webhooks/your-development-webhook-url'  # Webhook URL for the backup channel.

else:
    telegram_group_id = -1234567891
    discord_webhook_url = 'https://discord.com/api/webhooks/your-main-webhook-url'

### END OF CREDENTIALS ###


# Flags
IGNORE_VIDEO_FILES = False
CLONE_MEDIA_ONLY = False  # Only clone messages that have media attached.
KEEP_MEDIA_FILES = False  # Keep media files downloaded on the machine. Set to False to immidiately delete them after sending to Discord.
KEEP_USER_PFP = True  # Keep user profile pictures downloaded on the machine. Set to False to immidiately delete them after sending to Discord.
SHOW_USER_INFO = True  # Include the sender's name and profile picture in the Discord message.
SHOW_PROGRESS_BAR = True  # Show an `estimate` progress bar in the console.
IGNORE_SYSTEM_MESSAGES = True  # (e.g. user joined, user left, etc.)
CLEAR_TEMP_FOLDER = False  # Set to True to clear temporary files after processing. It is recommended to keep this disabled, since it enables the script to resume, even when new messages are sent.


# Rate Limits
LINEAR_SLEEP_FACTOR = 2  # Increase the sleep time after each rate limit by this factor. Hihger value is recommended for larger groups.
MAX_SLEEP_TIME = 60  # Maximum sleep time after rate limit (in seconds).


# File Paths
temp_folder = 'temp_dev/' if development else 'temp'  # Folder to temporarily store temporary files
avatar_folder = temp_folder + 'avatars'  # Folder to store profile pictures
temporary_data_file = temp_folder + 'temp.json'  # File to store the last processed message ID
