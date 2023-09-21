import os

from dotenv import load_dotenv

from src.cryptach_screener.config.config import Config


def load_config():
    load_dotenv()
    config = Config(
        token=os.getenv('BOT_TOKEN'),
        admins=[int(admin) for admin in os.getenv('ADMINS').split(', ')],
        rate_limit=os.getenv('RATE_LIMIT'),
        channel_id=os.getenv('CHANNEL_ID')
    )
    return config

