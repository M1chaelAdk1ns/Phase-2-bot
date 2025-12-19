"""Persistent state management for the bot."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class Entry:
    price: float
    size: float


@dataclass
class BotState:
    entries: List[Entry] = field(default_factory=list)
    session_high: float | None = None
    partial_one_done: bool = False
    partial_two_done: bool = False
    daily_pnl: float = 0.0
    last_reset_date: str = field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

    @classmethod
    def from_dict(cls, data: dict) -> "BotState":
        entries = [Entry(**e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            session_high=data.get("session_high"),
            partial_one_done=data.get("partial_one_done", False),
            partial_two_done=data.get("partial_two_done", False),
            daily_pnl=data.get("daily_pnl", 0.0),
            last_reset_date=data.get("last_reset_date")
            or datetime.now(timezone.utc).date().isoformat(),
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["entries"] = [asdict(e) for e in self.entries]
        return data


class StateManager:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or config.state_path

    def load(self) -> BotState:
        if not os.path.exists(self.path):
            logger.info("State file not found; initializing new state")
            return BotState()
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BotState.from_dict(data)

    def save(self, state: BotState) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)


state_manager = StateManager()
