"""
LogEarn — response formatting helpers
"""

import json
import os
import tempfile
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

# 缓存目录可用 LOGEARN_CACHE_DIR 指定；默认放系统临时目录。不能放在代码目录下：容器里代码目录归 root，
# 非 root 进程写不进去（线上报 Permission denied，导致所有 CA 查询失败）。
_CACHE_DIR        = os.environ.get('LOGEARN_CACHE_DIR') or os.path.join(tempfile.gettempdir(), 'logearn-cache')
_PRICE_CACHE_FILE = os.path.join(_CACHE_DIR, 'native_prices.json')
_PRICE_CACHE_TTL  = 600  # seconds


_STALE_MAX_AGE = 3600


def _read_price_cache(max_age: float):
    try:
        if os.path.exists(_PRICE_CACHE_FILE):
            with open(_PRICE_CACHE_FILE, 'r') as f:
                cached = json.load(f)
            if time.time() - cached.get('_ts', 0) < max_age:
                return {int(k): float(v) for k, v in cached.items() if k != '_ts'}
    except Exception:
        pass
    return None


def _write_price_cache(prices: dict) -> None:
    """写缓存只是优化：写失败（目录不可写等）只记一行日志，不能让价格查询本身失败。"""
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_PRICE_CACHE_FILE, 'w') as f:
            json.dump({str(k): v for k, v in prices.items()} | {'_ts': time.time()}, f)
    except OSError as e:
        import sys
        print(f'[logearn] native price cache not written: {e}', file=sys.stderr)


def get_cached_native_prices() -> dict:
    """Return {3: sol_usd, 56: bnb_usd}。缓存 10 分钟；刷新失败时只允许用 1 小时内的旧缓存，
    再旧 / 没有就抛 ApiError——绝不返回空值或写死价格（格式化层对缺失价格会按 1.0 算市值，结果会静默错误）。"""
    fresh = _read_price_cache(_PRICE_CACHE_TTL)
    if fresh:
        return fresh
    import api as _api
    try:
        res    = _api.get_native_price()
        prices = {3: float(res.get('sol', 0) or 0), 56: float(res.get('bnb', 0) or 0)}
        if not all(v > 0 for v in prices.values()):
            raise _api.ApiError(f'native price invalid: {prices}')
        _write_price_cache(prices)
        return prices
    except Exception as e:
        stale = _read_price_cache(_STALE_MAX_AGE)
        if stale:
            import sys
            print(f'[logearn] native price refresh failed, using cache < 1h old: {e}', file=sys.stderr)
            return stale
        raise _api.ApiError(f'native price unavailable ({e})')


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
    if not isinstance(data, dict):
        # unwrap() failed (e.g. API returned data=null) — pass the error through
        # instead of crashing on data.values().
        return data

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
    if not isinstance(data, list):
        return data
    formatted = [fmt_tools_format_position(p) for p in data]
    return formatted


# ---------------------------------------------------------------------------
# Trade logs
# ---------------------------------------------------------------------------

def fmt_trade_logs(data: dict) -> dict:
    if not isinstance(data, list):
        return data
    formatted = [fmt_tools_format_trade_log(p) for p in data]
    return formatted

# ---------------------------------------------------------------------------
# Limit orders
# ---------------------------------------------------------------------------
def fmt_limit_orders(data: dict) -> dict:
    if not isinstance(data, list):
        return data
    formatted = [fmt_tools_format_limit_order(p) for p in data]
    return formatted

# ---------------------------------------------------------------------------
# Swap result
# ---------------------------------------------------------------------------

def fmt_swap_result(res: dict) -> str:
    return res