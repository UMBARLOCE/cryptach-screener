import itertools
from statistics import fmean
from typing import Any

from src.hammer_alert_system.checker.base import BaseChecker
from src.hammer_alert_system.structs import DOM, DOMLevelType


def rolling_window(seq: list[Any], size: int):
    if size <= 0:
        raise ValueError('Size of rolling window must be is larger than zero')
    return (seq[pos:pos + size] for pos in range(0, len(seq) - size + 1, 1))


class AggSumChecker(BaseChecker):
    threshold_quantity: float
    agg_frame: int
    bid_emoji: str
    ask_emoji: str

    def __init__(self, threshold_quantity: float, agg_frame: int, bid_emoji: str, ask_emoji: str):
        self.threshold_quantity = threshold_quantity
        self.agg_frame = agg_frame
        self.bid_emoji = bid_emoji
        self.ask_emoji = ask_emoji

    def get_big_levels(self, dom: DOM) -> list:
        """
        Проверяет большие уровни в стакане с помощью чанков - т.е.
        разбивая уровни стакана на группы и суммируя объем группы
        :param dom:
        :return:
        """
        big_levels = []
        ask_rolling_window = rolling_window(dom.asks, self.agg_frame)
        bid_rolling_window = rolling_window(dom.bids, self.agg_frame)
        for window in itertools.chain(ask_rolling_window, bid_rolling_window):
            if (quantity_sum := sum([level.quantity for level in window])) >= self.threshold_quantity:
                big_levels.append(DOM.Level(
                    price=fmean([level.price for level in window]),
                    quantity=quantity_sum,
                    level_type=window[0].level_type
                ))
        return big_levels

    def check_dom(self, dom: DOM) -> list[str]:
        """
        Возвращает список сигналов, если они имеются в стакане
        :param dom:
        :return:
        """
        levels = []
        levels += self.get_big_levels(dom)

        signals = [self.generate_signal(level, dom.symbol) for level in levels]

        return signals

    def generate_signal(self, level: DOM.Level, symbol: str) -> str:
        """
        Получить сообщение о сигнале
        :param symbol:
        :param level:
        :return:
        """
        if level.level_type == DOMLevelType.ASK:
            return f'#{symbol}\n' \
                   f'{self.ask_emoji}\n' \
                   f'Аск с объемом {level.quantity} по цене {level.price}'
        elif level.level_type == DOMLevelType.BID:
            return f'#{symbol}\n' \
                   f'{self.bid_emoji}\n' \
                   f'Бид с объемом {level.quantity} по цене {level.price}'
        else:
            raise ValueError(f'Unknown level type: {level}')
