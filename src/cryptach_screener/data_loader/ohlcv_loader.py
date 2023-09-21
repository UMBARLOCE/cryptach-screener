import asyncio
import logging

import aiohttp
import ccxt.async_support as ccxt
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class OHLCVLoader(object):
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.exchange = ccxt.binanceusdm()

    def start_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session is not None:
            await self.session.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
        await self.exchange.close()

    async def make_request_ohlcv(self, symbol: str, timeframe: str, limit: int):
        url = f'https://fapi.binance.com/fapi/v1/klines' \
              f'?symbol={symbol}&interval={timeframe}&limit={limit}'
        if self.session is None:
            self.start_session()
        async with self.session.get(url) as resp:
            if resp.status == 200:
                raw_ohclv = await resp.json()
                sliced_ohlcv = [row[:6] for row in raw_ohclv]
                converted_ohlcv = [[float(item) for item in row] for row in sliced_ohlcv]
                return converted_ohlcv
            else:
                logger.error(f"Error while fetching data {symbol} {timeframe}: {await resp.text()}")
        return None


    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame | None:
        ohlcv = await self.make_request_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

        # convert it into Pandas DataFrame
        if ohlcv is None:
            return None

        df = pd.DataFrame(ohlcv, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Time'] = [datetime.fromtimestamp(float(time) / 1000) for time in df['Time']]
        df.set_index('Time', inplace=True)

        return df

    async def fetch_futures_usdt_symbols(self) -> list[str]:
        markets = await self.exchange.fetch_markets()
        symbols: list[str] = [market['info']['symbol'] for market in markets]
        symbols = [symbol for symbol in symbols if symbol[-4:] == 'USDT']
        return symbols


if __name__ == '__main__':
    _loader = OHLCVLoader()
    data = asyncio.run(_loader.make_request_ohlcv('BTCUSDT', '1h', 100))
    print(data)
