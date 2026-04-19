"""
LogEarn — response formatting helpers
"""

from datetime import datetime, timezone
from typing import Any
from tools.fmt_signal_info import format_signal as fmt_tools_format_signal
from tools.fmt_position_info import format_position as fmt_tools_format_position
from tools.fmt_trade_log_info import format_trade_log as fmt_tools_format_trade_log
from tools.fmt_limit_order_info import format_limit_order as fmt_tools_format_limit_order


# ---------------------------------------------------------------------------
# ApiResponse helpers
# ---------------------------------------------------------------------------

def is_ok(res: dict) -> bool:
    return res.get('code') == 200 and res.get('data') is not None


def unwrap(res: dict, label: str) -> Any:
    if not is_ok(res):
        raise RuntimeError(f'[{label}] error {res.get("code")}: {res.get("msg", "unknown")}')
    return res['data']


# ---------------------------------------------------------------------------
# Signal  (item keys: chain, symbol, token_address, latest_price, main_pool,
#          token_tag, token_change, ai_signal)
# ---------------------------------------------------------------------------
def fmt_signals(data: dict) -> list:
    """
    data: {'3': [{...}, ...], '56': [{...}, ...]}
    Returns a flat list of formatted token dicts across all chains.
    Chains that are missing or empty are skipped.
    """
    result = []
    for chain_tokens in data.values():
        if not isinstance(chain_tokens, list):
            continue

        formatted = fmt_tools_format_signal(chain_tokens[2])
        result.append(formatted) 
        # for token in chain_tokens:
        #     formatted = fmt_tools_format_signal(token)
        #     if formatted is not None:
        #         result.append(formatted)    
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
    d = res.get('data') or {}
    return f'status: {res.get("status")}  txId: {d.get("txId", "n/a")}  tx_status: {d.get("status", "n/a")}'
