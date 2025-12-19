"""Data retrieval and indicator calculations."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import ccxt  # type: ignore
import numpy as np
import pandas as pd

from .config import config

logger = logging.getLogger(__name__)


class ExchangeClient:
    """Thin wrapper around ccxt for Hyperliquid.

    Notes:
        - Hyperliquid integration details may require exchange-specific params.
        - If additional params are needed, extend this class without altering strategy rules.
    """

    def __init__(self) -> None:
        exchange_cls = getattr(ccxt, "hyperliquid", None)
        if exchange_cls is None:
            raise RuntimeError("ccxt missing hyperliquid exchange implementation")
        self.exchange = exchange_cls({
            "apiKey": config.api_key,
            "secret": config.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "swap"},
            "urls": {"test": "https://api.hyperliquid-testnet.xyz"} if config.testnet else None,
        })

    def fetch_ticker_price(self) -> float:
        ticker = self.exchange.fetch_ticker(config.symbol)
        return float(ticker.get("last"))

    def fetch_candles(self) -> pd.DataFrame:
        candles: List[List[Any]] = self.exchange.fetch_ohlcv(
            config.symbol, timeframe="1m", limit=config.vwap_window
        )
        df = pd.DataFrame(
            candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        return df

    def fetch_order_book(self) -> Dict[str, Any]:
        return self.exchange.fetch_order_book(config.symbol, limit=20)

    def fetch_funding_rate(self) -> float:
        funding = self.exchange.fetch_funding_rate(config.symbol)
        return float(funding.get("fundingRate", 0.0))


def compute_vwap_and_atr(df: pd.DataFrame) -> Tuple[float, float]:
    if df.empty:
        raise ValueError("Candle dataframe is empty")

    close = df["close"].astype(float)
    volume = df["volume"].astype(float)
    typical_price = close
    cumulative_price_volume = (typical_price * volume).cumsum()
    cumulative_volume = volume.cumsum()
    vwap_series = cumulative_price_volume / cumulative_volume
    vwap = float(vwap_series.iloc[-1])

    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close_shifted = close.shift(1)
    tr = pd.DataFrame(
        {
            "hl": high - low,
            "hc": (high - close_shifted).abs(),
            "lc": (low - close_shifted).abs(),
        }
    ).max(axis=1)
    atr_series = tr.rolling(window=config.atr_window, min_periods=config.atr_window).mean()
    atr = float(atr_series.iloc[-1])
    if np.isnan(atr):
        raise ValueError("ATR could not be computed; insufficient data")
    return vwap, atr


def compute_lower_band(vwap: float, atr: float) -> float:
    return vwap - config.vwap_atr_multiplier * atr


def compute_orderbook_imbalance(order_book: Dict[str, Any]) -> float:
    bids: List[List[float]] = order_book.get("bids", [])[:20]
    asks: List[List[float]] = order_book.get("asks", [])[:20]
    bids_vol = sum(float(b[1]) for b in bids)
    asks_vol = sum(float(a[1]) for a in asks)
    if asks_vol == 0:
        return float("inf")
    return bids_vol / asks_vol
