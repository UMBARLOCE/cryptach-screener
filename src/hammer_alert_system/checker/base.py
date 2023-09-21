from abc import ABC, abstractmethod

from src.hammer_alert_system.structs import DOM


class BaseChecker(ABC):
    threshold_quantity: float

    def __init__(self, threshold_quantity: float):
        self.threshold_quantity = threshold_quantity


    @abstractmethod
    def check_dom(self, dom: DOM) -> list[str]:
        """
        Возвращает список сигналов, если они имеются в стакане
        :param dom:
        :return:
        """
        ...

    @abstractmethod
    def generate_signal(self, level: DOM.Level, symbol: str):
        """
        Получить сообщение о сигнале
        :param level:
        :param symbol:
        :return:
        """
        ...
