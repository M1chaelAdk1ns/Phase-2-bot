"""Telegram alerting utilities."""
from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from .config import config

logger = logging.getLogger(__name__)


def send_alert(message: str) -> Dict[str, Any] | None:
    if not config.telegram_token or not config.telegram_chat_id:
        logger.warning("Telegram not configured; skipping alert: %s", message)
        return None

    url = f"https://api.telegram.org/bot{config.telegram_token}/sendMessage"
    payload = {"chat_id": config.telegram_chat_id, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Failed to send Telegram alert: %s", exc)
        return None
