from dataclasses import dataclass


@dataclass
class Config(object):
    token: str
    admins: list[int]
    channel_id: str
    rate_limit: str
