"""Configuration for Phase-2 HYPE Dip-Buying Bot.

Environment variables can override defaults for deployment flexibility.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    symbol: str = os.getenv("SYMBOL", "HYPE/USDC:USDC")
    base_size: float = float(os.getenv("BASE_SIZE", 7.7))
    normal_size: float = float(os.getenv("NORMAL_SIZE", 23.8))
    deep_size: float = float(os.getenv("DEEP_SIZE", 170))
    nuclear_multiplier: float = float(os.getenv("NUCLEAR_MULTIPLIER", 1.5))

    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", 1500))
    funding_max: float = float(os.getenv("FUNDING_MAX", 0.0003))
    imbalance_min: float = float(os.getenv("IMBALANCE_MIN", 1.8))

    profit_targets = [1.008, 1.015]
    final_target: float = float(os.getenv("FINAL_TARGET", 1.025))

    no_trade_start: int = int(os.getenv("NO_TRADE_START", 3))
    no_trade_end: int = int(os.getenv("NO_TRADE_END", 7))

    vwap_window: int = int(os.getenv("VWAP_WINDOW", 1440))
    atr_window: int = int(os.getenv("ATR_WINDOW", 120))
    vwap_atr_multiplier: float = float(os.getenv("VWAP_ATR_MULTIPLIER", 1.2))

    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    testnet: bool = os.getenv("TESTNET", "false").lower() == "true"
    telegram_token: str | None = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID")

    api_key: str | None = os.getenv("HYPERLIQUID_API_KEY")
    api_secret: str | None = os.getenv("HYPERLIQUID_API_SECRET")

    state_path: str = os.getenv("STATE_PATH", "bot_state.json")


config = Config()
