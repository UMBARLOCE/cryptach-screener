import logging
import os
from datetime import datetime

from aiogram import Bot, types
from aiogram.types import InputFile

from src.cryptach_screener.config.config import Config
from src.cryptach_screener.signal.simple import SimpleSignal

logger = logging.getLogger(__name__)


class TelegramPoster(object):
    def __init__(self, config: Config):
        self.config = config

        self.bot = Bot(token=config.token, parse_mode=types.ParseMode.HTML)

    async def post_signal(self, channel_id: str, direction: str, symbol: str, timeframe: str, image_path: str = None):
        text = f'{symbol}\n' \
               f'{direction}\n' \
               f'{timeframe} '
        logger.info(f'posting message:\n{text}')
        if image_path is not None and os.path.isfile(image_path):
            image = InputFile(image_path)
            result = await self.bot.send_photo(chat_id=channel_id, photo=image, caption=text)
            os.remove(image_path)
        else:
            result = await self.bot.send_message(channel_id, text)
        signal = SimpleSignal(
            timeframe=timeframe,
            text=text,
            posting_time=datetime.now(),
            message_id=result.message_id,
            symbol=symbol
        )
        return signal

    async def send_message(self, channel_id: int, text: str):
        await self.bot.send_message(channel_id, text)