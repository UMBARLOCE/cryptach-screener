#!./venv/bin/python
import asyncio
import dataclasses
import datetime
import logging

from src.cryptach_screener.screener.screener import Screener
from src.cryptach_screener.config.loader import load_config
from src.hammer_alert_system.structs import DOM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename='screener.log',
    filemode='a',
)
logger = logging.getLogger('cryptach_screener')
logger.addHandler(logging.StreamHandler())

if __name__ == '__main__':
    logger.info("Start Cryptach Screener")
    config = load_config()
    analyzer = Screener(config)
    asyncio.run(analyzer.enter_loop())
