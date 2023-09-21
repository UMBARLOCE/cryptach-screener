import asyncio
import logging
import os
from datetime import datetime

import pandas as pd

from ccxt import RequestTimeout
from pandas_ta import supertrend
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.cryptach_screener.config.config import Config
from src.cryptach_screener.data_loader.ohlcv_loader import OHLCVLoader
from src.cryptach_screener.indicators.nadaraya_watson import nadaraya_watson_envelope
from src.cryptach_screener.signal.simple import SimpleSignal
from src.cryptach_screener.telegram.poster import TelegramPoster

pd.options.mode.chained_assignment = None

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def add_session_cols(df):
    df.loc[:, 'Hour'] = df.index.hour
    df.loc[:, 'SessionNY'] = df.apply(lambda x: 'NY' if 13 <= x.Hour < 22 else None, axis=1)
    df.loc[:, 'SessionLondon'] = df.apply(lambda x: 'London' if 7 <= x.Hour < 16 else None, axis=1)
    df.loc[:, 'SessionTokyo'] = df.apply(lambda x: 'Tokyo' if 0 <= x.Hour < 9 else None, axis=1)
    df.loc[:, 'SessionSydney'] = df.apply(lambda x: 'Sydney' if 21 <= x.Hour or x.Hour < 6 else None, axis=1)

    return df


class Screener(object):
    def __init__(self, config: Config):
        self.config = config
        self.ohlcv_loader = OHLCVLoader()
        self.telegram_poster = TelegramPoster(config)
        self.last_signals: list[SimpleSignal] = []
        self.timeframes = ['30m', '1h']
        self.ohlcv_limit = 500

    async def enter_loop(self):
        while True:
            try:
                # if datetime.now().minute == 00:
                #     await self.make_checking_iteration('30m')
                #     await self.make_checking_iteration('1h')
                #     logger.info('Checking iteration completed')
                # elif datetime.now().minute == 30:
                #     await self.make_checking_iteration('30m')
                #     logger.info('Checking iteration completed')

                # await asyncio.sleep(5)


                if datetime.now().minute in (00, 10, 20, 30, 40, 50):
                    await self.make_checking_iteration('1h')
                    logger.info('Checking iteration completed')
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(e, exc_info=True)
                for admin in self.config.admins:
                    await self.telegram_poster.send_message(admin, f'Error on analyzer: {e}')

    async def make_checking_iteration(self, timeframe: str):
        logger.info(f'New iteration on timeframe {timeframe}')

        self.ohlcv_loader.start_session()

        symbols = (await self.ohlcv_loader.fetch_futures_usdt_symbols())
        fetch_data_tasks = [self.fetch_market_data(symbol, timeframe) for symbol in symbols]
        loaded_market_data = await asyncio.gather(*fetch_data_tasks)
        logger.debug(f"Loaded market data")

        await self.ohlcv_loader.close_session()

        checked_symbol_counter = 0
        for symbol, market_data in zip(symbols, loaded_market_data):
            try:
                if market_data is None:
                    continue

                long_signal, short_signal = await self.get_signals(market_data)

                await self.handle_signals(long_signal, market_data, short_signal, symbol, timeframe)
                checked_symbol_counter += 1
            except Exception as e:
                logger.error(f'Error on handling {symbol} {timeframe}: {e}', exc_info=True)
                for admin in self.config.admins:
                    await self.telegram_poster.send_message(admin, f'Error on handling {symbol} {timeframe}: {e}')
        logger.info(f"Checked market data of {checked_symbol_counter} / {len(symbols)} symbols")

    async def fetch_market_data(self, symbol, timeframe):
        try:
            ohlcv = await self.ohlcv_loader.fetch_ohlcv(symbol, timeframe, self.ohlcv_limit)
            # анализирую данные

            if ohlcv is None:
                logger.debug(f'Ignore {symbol} {timeframe}: failed to load data')
                return None
            if len(ohlcv.index) < self.ohlcv_limit:
                logger.debug(f'Ignore {symbol} {timeframe}: too little data was received:'
                             f' {len(ohlcv.index)} < {self.ohlcv_limit}')
                return None

            supertrend_result = supertrend(high=ohlcv.High, low=ohlcv.Low, close=ohlcv.Close, length=7)
            nwe_result = nadaraya_watson_envelope(ohlcv, length=self.ohlcv_limit, h=8, mult=3)
            market_data = pd.merge(nwe_result, supertrend_result, left_index=True, right_index=True)
            market_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'NWE_upper',
                                   'NWE_lower', 's_trend', 's_direction', 's_long', 's_short']
            return market_data

        except asyncio.exceptions.TimeoutError:
            logger.debug(f"Timeout on fetching {symbol} {timeframe}")
            return None
        except TimeoutError:
            logger.debug(f"Timeout on fetching {symbol} {timeframe}")
            return None
        except RequestTimeout:
            logger.debug(f"Timeout on fetching {symbol} {timeframe}")
            return None
        except Exception as e:
            logger.error(f"Error on fetching {symbol} {timeframe}: {e}")
            return None

    async def get_signals(self, market_data):
        long_signal = self.check_to_long(market_data)
        short_signal = self.check_to_short(market_data)
        return long_signal, short_signal

    async def handle_signals(self, long_signal, market_data, short_signal, symbol, timeframe):
        # отправляю сигналы в канал телеграм
        if long_signal:
            image_path = self.save_market_data_chart(
                market_data,
                f'{symbol} {timeframe}',
                f'{symbol}_{timeframe}_{datetime.now().timestamp()}'
            )
            await self.telegram_poster.post_signal(
                channel_id=self.config.channel_id,
                direction='🟢 LONG',
                symbol=symbol,
                timeframe=timeframe,
                image_path=image_path
            )
            logger.info(f'New long signal: {symbol} {timeframe}')
        elif short_signal:
            image_path = self.save_market_data_chart(
                market_data,
                f'{symbol} {timeframe}',
                f'{symbol}_{timeframe}_{datetime.now().timestamp()}'
            )
            await self.telegram_poster.post_signal(
                channel_id=self.config.channel_id,
                direction='🔴 SHORT',
                symbol=symbol,
                timeframe=timeframe,
                image_path=image_path
            )
            logger.info(f'New short signal: {symbol} {timeframe}')

    @staticmethod
    def check_to_long(market_data: pd.DataFrame) -> bool:
        """
        Проверка рыночный данных на лонговый сигнал
        """
        last_data = market_data.iloc[-1]
        # проверка, что нужные данные есть в датафрейме
        if 's_long' in market_data.columns and 'NWE_lower' in market_data.columns \
                and last_data['s_long'] and last_data['NWE_lower']:
            # проверка, что supertrend подошел близко к NWE
            if last_data['s_long'] < last_data['NWE_lower']:
                # Вычисляю разницу между ценой закрытия и супертрендом, а также длину тела свечи
                # Первое частное должно быть меньше второго, исходя из принципа, что ещё одна такая же свеча, и
                # линия NWE будет преодолена линией цены
                indicator_difference = last_data['Close'] - last_data['NWE_lower']
                candle_length = last_data['Open'] - last_data['Close']

                # проверка, что цена подошла близко к NWE
                if 0 < indicator_difference < candle_length:
                    return True
        return False

    @staticmethod
    def check_to_short(market_data: pd.DataFrame) -> bool:
        """
        Проверка рыночных данных на шортовый сигнал
        """
        last_data = market_data.iloc[-1]
        # проверка, что нужные данные есть в датафрейме
        if 's_short' in market_data.columns and 'NWE_upper' in market_data.columns \
                and last_data['s_short'] and last_data['NWE_upper']:
            # проверка, что supertrend подошел близко к NWE
            if last_data['s_short'] > last_data['NWE_upper']:
                # Вычисляю разницу между ценой закрытия и супертрендом, а также длину тела свечи
                # Первое частное должно быть меньше второго, исходя из принципа, что ещё одна такая же свеча, и
                # линия NWE будет преодолена линией цены
                indicator_difference = last_data['NWE_upper'] - last_data['Close']
                candle_length = last_data['Close'] - last_data['Open']

                # проверка, что цена подошла близко к NWE
                if 0 < indicator_difference < candle_length:
                    return True
        return False

    def save_market_data_chart(self, market_data: pd.DataFrame, chart_title: str, file_name: str):
        df = market_data.tail(50)

        df = add_session_cols(df)

        fig = self.draw_chart(chart_title, df)

        if not os.path.exists("images"):
            os.mkdir("images")

        image_path = f"images/{file_name}.jpg"

        fig.write_image(image_path)
        return image_path

    @staticmethod
    def draw_chart(chart_title, df):
        fig = make_subplots(rows=2, cols=1,
                            row_heights=[0.15, 0.85],
                            shared_xaxes=True,
                            vertical_spacing=0.02)
        fig.add_traces(data=[
            go.Scatter(name='Sydney', x=df.index, y=df['SessionSydney'], showlegend=False, line={'width': 7}),
            go.Scatter(name='Tokyo', x=df.index, y=df['SessionTokyo'], showlegend=False, line={'width': 7}),
            go.Scatter(name='London', x=df.index, y=df['SessionLondon'], showlegend=False, line={'width': 7}),
            go.Scatter(name='NY', x=df.index, y=df['SessionNY'], showlegend=False, line={'width': 7}),
        ])
        fig.add_traces(data=[
            go.Candlestick(name=chart_title, x=df.index,
                           open=df['Open'], high=df['High'],
                           low=df['Low'], close=df['Close']),
            go.Scatter(name='NWE upper', x=df.index, y=df['NWE_upper'],
                       line=dict(color='lime', width=1, dash='dash')),
            go.Scatter(name='NWE lower', x=df.index, y=df['NWE_lower'], line=dict(color='red', width=1, dash='dash')),
            go.Scatter(name='Supertrend Long', x=df.index, y=df['s_long'], line=dict(color='lime', width=2)),
            go.Scatter(name='Supertrend Short', x=df.index, y=df['s_short'], line=dict(color='red', width=2)),
        ], rows=2, cols=1)
        for i in range(1, 3):
            fig.update_xaxes(row=i, col=1, rangeslider_visible=False)
        fig.update_layout(
            width=1280,
            height=720,
            title=chart_title,
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            margin=go.layout.Margin(
                l=50,
                r=50,
                b=30,
                t=70,
                pad=4
            ),
        )
        return fig
