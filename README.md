# TD-Media-Clone

TD-Media-Clone is a Python project that utilizes discord.py and telethon libraries to clone messages, including media, from a Telegram group to a specified Discord channel. It achieves this by logging into a Telegram user account, temporarily downloading the messages in chronological order, and then sending them to Discord using webhooks.

## Installation

1. Clone the repository: `git clone https://github.com/your-username/TD-Media.git`
2. Install the required dependencies: `pip install -r requirements.txt`

## Configuration

1. Create 2 Discord channels and a webhook for each, and obtain both links.
2. Create a new Telegram app and obtain the API ID and API hash. (visit https://my.telegram.org)
3. Update the `config.py` file with the obtained credentials and adjust the other parameters.

## Usage

1. Run the `main.py` script: `python main.py`
2. The script will prompt you to log in to your Telegram account.
3. Once logged in, it will start cloning the messages from the Telegram group.
4. The cloned messages will be sent to the specified Discord channel via webhooks.

## Contributing

You are more than welcome to contribute to this project. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
