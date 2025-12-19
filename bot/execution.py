"""Order execution helpers."""
from __future__ import annotations

import logging
from typing import Any, Dict

from .config import config
from .data import ExchangeClient

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, client: ExchangeClient) -> None:
        self.client = client

    def market_buy(self, size: float) -> Dict[str, Any]:
        if config.dry_run:
            logger.info("DRY_RUN: would buy %s", size)
            return {"status": "dry_run", "side": "buy", "size": size}
        logger.info("Placing market buy for %s", size)
        return self.client.exchange.create_order(
            config.symbol, "market", "buy", size, params={"reduceOnly": False}
        )

    def reduce_only_sell(self, size: float) -> Dict[str, Any]:
        if config.dry_run:
            logger.info("DRY_RUN: would reduce %s", size)
            return {"status": "dry_run", "side": "sell", "size": size}
        logger.info("Placing reduce-only market sell for %s", size)
        return self.client.exchange.create_order(
            config.symbol, "market", "sell", size, params={"reduceOnly": True}
        )
