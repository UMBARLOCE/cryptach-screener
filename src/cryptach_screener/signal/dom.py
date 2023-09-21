from dataclasses import dataclass
from datetime import datetime


@dataclass()
class DomSignal(object):
    price: float
    quantity: float
    text: str
    posting_time: datetime = None
    message_id: int = None

