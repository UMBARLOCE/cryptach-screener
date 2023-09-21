from dataclasses import dataclass
from datetime import datetime


@dataclass()
class SimpleSignal(object):
    symbol: str
    timeframe: str
    text: str
    posting_time: datetime = None
    message_id: int = None

