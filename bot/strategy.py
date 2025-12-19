"""Core strategy rules for Phase-2 HYPE Dip-Buying Bot."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from .alerts import send_alert
from .config import config
from .execution import Executor
from .state import BotState, Entry

logger = logging.getLogger(__name__)


@dataclass
class Indicators:
    vwap: float
    atr: float
    lower_band: float
    imbalance: float
    funding_rate: float


def level_size(level: int) -> float:
    if level <= 1:
        return config.base_size
    if 2 <= level <= 6:
        return config.normal_size
    if 7 <= level <= 10:
        return config.deep_size
    return level_size(level - 1) * config.nuclear_multiplier


def total_position(entries: list[Entry]) -> float:
    return sum(e.size for e in entries)


def average_entry(entries: list[Entry]) -> float | None:
    size = total_position(entries)
    if size == 0:
        return None
    weighted_sum = sum(e.price * e.size for e in entries)
    return weighted_sum / size


def in_blackout(utc_hour: int) -> bool:
    return config.no_trade_start <= utc_hour < config.no_trade_end


def new_lower_low(price: float, session_high: float | None) -> bool:
    if session_high is None:
        return False
    return price <= session_high * (1 - 0.0005)


class Strategy:
    def __init__(self, executor: Executor) -> None:
        self.executor = executor

    def evaluate_entry(
        self, price: float, indicators: Indicators, utc_hour: int, state: BotState
    ) -> Tuple[bool, float | None]:
        if in_blackout(utc_hour):
            return False, None
        if state.daily_pnl <= -config.max_daily_loss:
            return False, None
        if indicators.funding_rate >= config.funding_max:
            return False, None
        if price > indicators.lower_band:
            return False, None
        if indicators.imbalance < config.imbalance_min:
            return False, None
        if not new_lower_low(price, state.session_high):
            return False, None

        level = len(state.entries) + 1
        size = level_size(level)
        return True, size

    def execute_entry(self, price: float, size: float, state: BotState) -> None:
        result = self.executor.market_buy(size)
        state.entries.append(Entry(price=price, size=size))
        avg = average_entry(state.entries)
        send_alert(
            f"BUY level {len(state.entries)} size {size} at {price}; new avg {avg:.6f} ({result})"
        )

    def _apply_exit(self, state: BotState, sell_fraction: float, price: float) -> None:
        avg = average_entry(state.entries)
        if avg is None:
            return
        total = total_position(state.entries)
        sell_size = total * sell_fraction
        self.executor.reduce_only_sell(sell_size)
        realized = (price - avg) * sell_size
        state.daily_pnl += realized
        remaining = total - sell_size
        if remaining > 0:
            state.entries = [Entry(price=avg, size=remaining)]
        else:
            state.entries = []
            state.session_high = None
            state.partial_one_done = False
            state.partial_two_done = False
        send_alert(
            f"EXIT {sell_fraction*100:.0f}% at {price}; realized {realized:.2f}; remaining {remaining}"
        )

    def process_exits(self, price: float, state: BotState) -> None:
        avg = average_entry(state.entries)
        if avg is None:
            return
        total = total_position(state.entries)
        if total <= 0:
            return

        if (not state.partial_one_done) and price >= avg * config.profit_targets[0]:
            state.partial_one_done = True
            self._apply_exit(state, 0.25, price)

        if (not state.partial_two_done) and price >= avg * config.profit_targets[1]:
            state.partial_two_done = True
            self._apply_exit(state, 0.25, price)

        # Final exit at 50% (or whatever remains)
        if price >= avg * config.final_target and state.entries:
            self._apply_exit(state, 1.0, price)

    def daily_reset_if_needed(self, state: BotState) -> bool:
        today = datetime.now(timezone.utc).date().isoformat()
        if state.last_reset_date != today:
            state.daily_pnl = 0.0
            state.last_reset_date = today
            send_alert("Daily reset: counters cleared")
            return True
        return False

    def update_session_high(self, price: float, state: BotState) -> None:
        if state.session_high is None:
            state.session_high = price
        else:
            state.session_high = max(state.session_high, price)
