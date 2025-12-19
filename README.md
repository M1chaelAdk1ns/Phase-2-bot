# Phase-2 HYPE Dip-Buying Bot

Production-ready automated trading bot for Hyperliquid HYPE/USDC perpetuals implementing the deterministic "Phase-2" dip-buying rules.

## Features
- Long-only martingale grid with fixed sizing tiers and nuclear scaling.
- VWAP/ATR-derived lower-band filter plus order book imbalance and funding-rate guardrails.
- Three-stage profit taking (25%/25%/50%) with reduce-only exits.
- Persistent state across restarts (entries, partial exits, session high, daily PnL).
- Daily loss cap and UTC blackout window (03:00–07:00) for new entries.
- Telegram alerts for lifecycle, trades, exits, errors, and daily resets.
- DRY_RUN mode and optional testnet connectivity.

## Requirements
- Python 3.11+
- Dependencies: `ccxt`, `pandas`, `numpy`, `requests`, `pytest`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration
Environment variables override defaults in `bot/config.py`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SYMBOL` | `HYPE/USDC:USDC` | Trading pair |
| `BASE_SIZE` | `7.7` | Level 1 size |
| `NORMAL_SIZE` | `23.8` | Levels 2–6 size |
| `DEEP_SIZE` | `170` | Levels 7–10 size |
| `NUCLEAR_MULTIPLIER` | `1.5` | Level 11+ scaling |
| `MAX_DAILY_LOSS` | `1500` | Loss cap (USDC) |
| `FUNDING_MAX` | `0.0003` | Max funding for entries |
| `IMBALANCE_MIN` | `1.8` | Min bid/ask volume ratio |
| `NO_TRADE_START` | `3` | UTC blackout start hour |
| `NO_TRADE_END` | `7` | UTC blackout end hour |
| `VWAP_WINDOW` | `1440` | 1m bars for VWAP |
| `ATR_WINDOW` | `120` | Periods for ATR |
| `VWAP_ATR_MULTIPLIER` | `1.2` | Lower band offset |
| `FINAL_TARGET` | `1.025` | Final full exit multiplier |
| `DRY_RUN` | `true` | Skip order placement |
| `TESTNET` | `false` | Toggle testnet (if supported) |
| `HYPERLIQUID_API_KEY` | - | API key |
| `HYPERLIQUID_API_SECRET` | - | API secret |
| `TELEGRAM_TOKEN` | - | Bot token |
| `TELEGRAM_CHAT_ID` | - | Chat ID |
| `STATE_PATH` | `bot_state.json` | Persistence file |

## Running the bot
```bash
python -m bot.main
```
The loop evaluates roughly every two seconds. In `DRY_RUN=true`, trades are logged and alerts sent without touching the exchange.

## Testing
Run unit tests:
```bash
pytest
```

## Notes
- Exchange integration uses CCXT's `hyperliquid` class; if exchange-specific params are required, extend `ExchangeClient` without altering strategy rules.
- Strategy logic is fully deterministic per specification; no additional indicators or dynamic behavior is introduced.
