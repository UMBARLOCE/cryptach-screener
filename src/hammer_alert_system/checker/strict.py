from src.hammer_alert_system.checker.base import BaseChecker
from src.hammer_alert_system.structs import DOM, DOMLevelType


class StrictChecker(BaseChecker):
    threshold_quantity: float

    def get_big_bids(self, dom: DOM) -> list:
        big_bids = []
        for level in dom.bids:
            if level.quantity >= self.threshold_quantity:
                big_bids.append(level)
        return big_bids

    def get_big_asks(self, dom: DOM) -> list:
        big_asks = []
        for level in dom.asks:
            if level.quantity >= self.threshold_quantity:
                big_asks.append(level)
        return big_asks

    def check_dom(self, dom: DOM) -> list[DOM.Level]:
        """
        Возвращает список уровней с большими заявками, если они имеются в стакане
        :param dom:
        :return:
        """
        levels = []
        levels += self.get_big_asks(dom)
        levels += self.get_big_bids(dom)

        return levels

    def generate_signal(self, level: DOM.Level, symbol: str) -> str:
        """
        Получить сообщение о сигнале
        :param symbol:
        :param level:
        :return:
        """
        if level.level_type == DOMLevelType.ASK:
            return f'#{symbol}\n' \
                      f'🔴🔴🔴\n' \
                      f'Аск с объемом {level.quantity} по цене {level.price}'
        elif level.level_type == DOMLevelType.BID:
            return f'#{symbol}\n' \
                      f'🟢🟢🟢\n' \
                      f'Бид с объемом {level.quantity} по цене {level.price}'
        else:
            raise ValueError(f'Unknown level type: {level}')
