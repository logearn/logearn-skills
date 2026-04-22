"""
LogEarn — response formatting helpers
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from tools.fmt_signal_info import format_signal as fmt_tools_format_signal
from tools.fmt_position_info import format_position as fmt_tools_format_position
from tools.fmt_trade_log_info import format_trade_log as fmt_tools_format_trade_log
from tools.fmt_limit_order_info import format_limit_order as fmt_tools_format_limit_order


# ---------------------------------------------------------------------------
# Native price cache  (.cache/native_prices.json, TTL = 10 min)
# ---------------------------------------------------------------------------

_CACHE_DIR        = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.cache')
_PRICE_CACHE_FILE = os.path.join(_CACHE_DIR, 'native_prices.json')
_PRICE_CACHE_TTL  = 600  # seconds


def get_cached_native_prices() -> dict:
    """Return {3: sol_usd, 56: bnb_usd}, refreshing from API when cache is missing or stale."""
    try:
        if os.path.exists(_PRICE_CACHE_FILE):
            with open(_PRICE_CACHE_FILE, 'r') as f:
                cached = json.load(f)
            if time.time() - cached.get('_ts', 0) < _PRICE_CACHE_TTL:
                return {int(k): float(v) for k, v in cached.items() if k != '_ts'}
    except Exception:
        pass

    import api as _api
    try:
        res    = _api.get_native_price()
        prices = {3: float(res.get('sol', 0) or 0), 56: float(res.get('bnb', 0) or 0)}
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_PRICE_CACHE_FILE, 'w') as f:
            json.dump({str(k): v for k, v in prices.items()} | {'_ts': time.time()}, f)
        return prices
    except Exception:
        return {3: 86, 56: 630}  # fallback


# ---------------------------------------------------------------------------
# ApiResponse helpers
# ---------------------------------------------------------------------------

def is_ok(res: dict) -> bool:
    return res.get('code') == 200 and res.get('data') is not None


def unwrap(res: dict, label: str) -> Any:
    if not is_ok(res):
        return f'[{label}] error {res.get("code")}: {res.get("message", "unknown")}'
    return res['data']


# ---------------------------------------------------------------------------
# Signal  (item keys: chain, symbol, token_address, latest_price, main_pool,
#          token_tag, token_change, ai_signal)
# ---------------------------------------------------------------------------
def fmt_signals(data: dict, native_prices: dict = None) -> list:
    """
    data: {'3': [{...}, ...], '56': [{...}, ...]}
    Returns a flat list of formatted token dicts across all chains.
    Chains that are missing or empty are skipped.
    """
    result = []
    for chain_tokens in data.values():
        if not isinstance(chain_tokens, list):
            continue

        for token in chain_tokens:
            formatted = fmt_tools_format_signal(token, native_prices)
            if formatted is not None:
                result.append(formatted)    
    return [result]

# ---------------------------------------------------------------------------
# Wallet positions
# ---------------------------------------------------------------------------
def fmt_positions(data: dict) -> dict:
    formatted = [fmt_tools_format_position(p) for p in data]
    return formatted


# ---------------------------------------------------------------------------
# Trade logs
# ---------------------------------------------------------------------------

def fmt_trade_logs(data: dict) -> dict:
    formatted = [fmt_tools_format_trade_log(p) for p in data]
    return formatted

# ---------------------------------------------------------------------------
# Limit orders
# ---------------------------------------------------------------------------
def fmt_limit_orders(data: dict) -> dict:
    print(data)
    formatted = [fmt_tools_format_limit_order(p) for p in data]
    return formatted    

# ---------------------------------------------------------------------------
# Swap result
# ---------------------------------------------------------------------------

def fmt_swap_result(res: dict) -> str:
    return res