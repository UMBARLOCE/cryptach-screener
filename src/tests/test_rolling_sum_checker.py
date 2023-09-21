import copy
from unittest import TestCase

from src.hammer_alert_system.checker.rolling_sum import rolling_window, AggSumChecker
from src.hammer_alert_system.structs import DOM, DOMLevelType

dom_without_big_levels = DOM(
    symbol='SHIBUSDT',
    asks=[
        DOM.Level(100, 0, DOMLevelType.ASK),
        DOM.Level(101, 0, DOMLevelType.ASK),
        DOM.Level(102, 0, DOMLevelType.ASK),
        DOM.Level(103, 0, DOMLevelType.ASK),
        DOM.Level(104, 0, DOMLevelType.ASK),
    ],
    bids=[
        DOM.Level(99, 0, DOMLevelType.BID),
        DOM.Level(98, 0, DOMLevelType.BID),
        DOM.Level(97, 0, DOMLevelType.BID),
        DOM.Level(96, 0, DOMLevelType.BID),
        DOM.Level(95, 0, DOMLevelType.BID),
    ]
)

dom_big_level_100_in_asks = copy.deepcopy(dom_without_big_levels)
dom_big_level_100_in_asks.asks[2].quantity = 100

dom_big_level_100_in_bids = copy.deepcopy(dom_without_big_levels)
dom_big_level_100_in_bids.bids[2].quantity = 100

dom_big_level_100_in_bids_and_asks = copy.deepcopy(dom_without_big_levels)
dom_big_level_100_in_bids_and_asks.bids[2].quantity = 100
dom_big_level_100_in_bids_and_asks.asks[2].quantity = 100

dom_with_agg_50_level_in_bids = copy.deepcopy(dom_without_big_levels)
dom_with_agg_50_level_in_bids.bids[1].quantity = 10
dom_with_agg_50_level_in_bids.bids[2].quantity = 35
dom_with_agg_50_level_in_bids.bids[3].quantity = 10

dom_with_agg_50_level_in_asks = copy.deepcopy(dom_without_big_levels)
dom_with_agg_50_level_in_asks.bids[0].quantity = 10
dom_with_agg_50_level_in_asks.bids[1].quantity = 35
dom_with_agg_50_level_in_asks.bids[2].quantity = 10


class TestAggSumChecker(TestCase):

    def setUp(self) -> None:
        self.checker = AggSumChecker(
            threshold_quantity=50,
            agg_frame=3,
            bid_emoji='',
            ask_emoji=''
        )

    def test_checker_without_big_levels(self):
        levels = self.checker.get_big_levels(dom_without_big_levels)
        self.assertListEqual(levels, [])

    def test_checker_with_big_bid(self):
        levels = self.checker.get_big_levels(dom_big_level_100_in_bids)
        self.assertListEqual(levels, [DOM.Level(97, 50, DOMLevelType.BID)])

    def test_checker_with_big_ask(self):
        levels = self.checker.get_big_levels(dom_big_level_100_in_bids)
        self.assertListEqual(levels, [DOM.Level(102, 50, DOMLevelType.ASK)])

    def test_checker_with_big_ask_and_bid(self):
        levels = self.checker.get_big_levels(dom_big_level_100_in_bids)
        self.assertListEqual(levels, [DOM.Level(97, 50, DOMLevelType.BID), DOM.Level(102, 50, DOMLevelType.ASK)])


    def test_check_dom(self):
        self.fail()

    def test_generate_signal(self):
        self.fail()


class TestRollingWindow(TestCase):
    def test_simple_list_with_window_4(self):
        lst = [1, 4, 5, 2, 3, 5, 6]
        windows = [i for i in rolling_window(lst, 4)]
        self.assertListEqual(windows, [[1, 4, 5, 2], [4, 5, 2, 3], [5, 2, 3, 5], [2, 3, 5, 6]])

    def test_simple_list_with_window_2(self):
        lst = [1, 4, 5, 2, 3, 5, 6]
        windows = [i for i in rolling_window(lst, 2)]
        self.assertListEqual(windows, [[1, 4], [4, 5], [5, 2], [2, 3], [3, 5], [5, 6]])

    def test_small_list_big_window(self):
        lst = [1, 4]
        windows = [i for i in rolling_window(lst, 3)]
        self.assertListEqual(windows, [])

    def test_simple_list_with_window_1(self):
        lst = [1, 4, 5, 2, 3, 5, 6]
        windows = [i for i in rolling_window(lst, 1)]
        self.assertListEqual(windows, [[1], [4], [5], [2], [3], [5], [6]])

    def test_empty_list(self):
        lst = []
        windows = [i for i in rolling_window(lst, 3)]
        self.assertListEqual(windows, [])

    def test_zero_window_raises_exception(self):
        lst = [1, 2, 3, 4, 5]
        self.assertRaises(ValueError, rolling_window, lst, 0)
