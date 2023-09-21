from dataclasses import dataclass
from enum import Enum


class DOMLevelType(Enum):
    BID = 0
    ASK = 1


@dataclass
class DOM(object):

    @dataclass
    class Level(object):
        price: float
        quantity: float
        level_type: DOMLevelType

    asks: list[Level]
    bids: list[Level]
    symbol: str


@dataclass
class OHLCV(object):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SliceOHLCV(object):
    candles: list[OHLCV]
    symbol: str
