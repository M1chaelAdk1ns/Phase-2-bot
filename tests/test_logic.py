import pandas as pd

from bot.config import config
from bot.data import compute_orderbook_imbalance, compute_vwap_and_atr, compute_lower_band
from bot.state import BotState, Entry
from bot.strategy import Indicators, Strategy, average_entry, in_blackout, level_size


class DummyExecutor:
    def __init__(self):
        self.orders = []

    def reduce_only_sell(self, size: float):
        self.orders.append(("sell", size))

    def market_buy(self, size: float):
        self.orders.append(("buy", size))
        return {"status": "ok"}


def test_vwap_and_atr():
    data = []
    price = 100
    for i in range(config.vwap_window):
        price += 0.1
        data.append([i, price, price + 1, price - 1, price, 10])
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    vwap, atr = compute_vwap_and_atr(df)
    assert vwap > 0
    assert atr > 0
    lower_band = compute_lower_band(vwap, atr)
    assert lower_band < vwap


def test_orderbook_imbalance():
    ob = {
        "bids": [[1, 10]] * 20,
        "asks": [[1.1, 5]] * 20,
    }
    imbalance = compute_orderbook_imbalance(ob)
    assert imbalance == (10 * 20) / (5 * 20)


def test_level_sizing_progression():
    assert level_size(1) == config.base_size
    assert level_size(2) == config.normal_size
    assert level_size(6) == config.normal_size
    assert level_size(7) == config.deep_size
    assert level_size(10) == config.deep_size
    assert level_size(11) == config.deep_size * config.nuclear_multiplier
    assert level_size(12) == level_size(11) * config.nuclear_multiplier


def test_partial_exit_sequence():
    executor = DummyExecutor()
    strat = Strategy(executor)
    state = BotState(entries=[Entry(price=100, size=10)])
    avg = average_entry(state.entries)
    indicators = Indicators(
        vwap=0,
        atr=0,
        lower_band=0,
        imbalance=10,
        funding_rate=0,
    )

    # First target hit
    strat.process_exits(avg * config.profit_targets[0], state)
    assert state.partial_one_done is True
    assert len(executor.orders) == 1

    # Second target hit
    strat.process_exits(avg * config.profit_targets[1], state)
    assert state.partial_two_done is True
    assert len(executor.orders) == 2

    # Final target hit - should close remaining
    strat.process_exits(avg * config.final_target, state)
    assert len(state.entries) == 0
    assert len(executor.orders) == 3


def test_blackout_blocks_entry_but_allows_exit():
    executor = DummyExecutor()
    strat = Strategy(executor)
    state = BotState(entries=[Entry(price=100, size=10)])
    state.partial_one_done = False

    indicators = Indicators(
        vwap=0,
        atr=0,
        lower_band=1000,
        imbalance=config.imbalance_min,
        funding_rate=0,
    )

    allowed, size = strat.evaluate_entry(
        price=50, indicators=indicators, utc_hour=config.no_trade_start, state=state
    )
    assert allowed is False
    assert size is None

    # Exits still process
    avg = average_entry(state.entries)
    strat.process_exits(avg * config.final_target, state)
    assert len(executor.orders) == 1
    assert len(state.entries) == 0
