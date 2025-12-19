"""Main loop for the Phase-2 HYPE Dip-Buying Bot."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from .alerts import send_alert
from .config import config
from .data import ExchangeClient, compute_lower_band, compute_orderbook_imbalance, compute_vwap_and_atr
from .execution import Executor
from .state import state_manager
from .strategy import Indicators, Strategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    send_alert(f"Bot starting (dry_run={config.dry_run}, testnet={config.testnet})")
    client = ExchangeClient()
    executor = Executor(client)
    strategy = Strategy(executor)
    state = state_manager.load()

    while True:
        try:
            strategy.daily_reset_if_needed(state)
            price = client.fetch_ticker_price()
            strategy.update_session_high(price, state)

            candles = client.fetch_candles()
            vwap, atr = compute_vwap_and_atr(candles)
            lower_band = compute_lower_band(vwap, atr)

            order_book = client.fetch_order_book()
            imbalance = compute_orderbook_imbalance(order_book)

            funding_rate = client.fetch_funding_rate()

            now = datetime.now(timezone.utc)
            indicators = Indicators(
                vwap=vwap,
                atr=atr,
                lower_band=lower_band,
                imbalance=imbalance,
                funding_rate=funding_rate,
            )

            allowed, size = strategy.evaluate_entry(price, indicators, now.hour, state)
            if allowed and size:
                strategy.execute_entry(price, size, state)

            strategy.process_exits(price, state)

            state_manager.save(state)
            time.sleep(2)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("Error in main loop: %s", exc)
            send_alert(f"Error: {exc}")
            time.sleep(10)


if __name__ == "__main__":
    run()
