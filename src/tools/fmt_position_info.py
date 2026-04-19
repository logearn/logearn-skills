"""
LogEarn — position PnL formatter (Python translation of formate_positon_pnl)
"""

from typing import Optional
from tools.fmt_token_info import ALL_SUPPORT_CHAINS


def format_position(position: Optional[dict]) -> Optional[dict]:
    """
    Normalise raw position fields and compute PnL metrics.

    Raw amounts from the API are integers scaled by chain / token decimals.
    This mirrors formate_positon_pnl() in JS.
    """
    if not position:
        return None

    try:
        pos = dict(position)

        chain: int = int(pos.get("chain") or 3)
        chain_cfg  = ALL_SUPPORT_CHAINS.get(chain, ALL_SUPPORT_CHAINS[3])
        w_decimals: int  = chain_cfg["decimal"]          # 18 (BSC) | 9 (SOL)
        tk_decimals: int = int(pos.get("decimals") or 0)

        price_exp = w_decimals - tk_decimals             # exponent for price fields

        # --- price fields ---
        price_div = 10 ** price_exp if price_exp >= 0 else 1.0 / (10 ** (-price_exp))
        pos["last_price"] = float(pos.get("last_price") or 0) / price_div
        pos["avg_price"]  = float(pos.get("avg_price")  or 0) / price_div
        pos["max_price"]  = float(pos.get("max_price")  or 0) / price_div

        # --- coin-denominated fields ---
        native_div = 10 ** w_decimals
        pos["total_receive_coin"] = float(pos.get("total_receive_coin") or 0) / native_div
        pos["total_cost_coin"]    = float(pos.get("total_cost_coin")    or 0) / native_div
        pos["hold_cost_coin"]     = float(pos.get("hold_cost_coin")     or 0) / native_div
        pos["unrelized_pnl"]      = float(pos.get("unrelized_pnl")      or 0) / native_div

        # --- token amount ---
        pos["hold_amount"] = float(pos.get("hold_amount") or 0) / (10 ** tk_decimals)

        # --- derived PnL ---
        total_receive = pos["total_receive_coin"]
        total_cost    = pos["total_cost_coin"]
        hold_amount   = pos["hold_amount"]
        last_price    = pos["last_price"]
        hold_cost     = pos["hold_cost_coin"]

        pos["total_pnl"]    = (total_receive + hold_amount * last_price) - total_cost
        pos["total_return"] = pos["total_pnl"] / total_cost if total_cost else 0.0

        realized_cost       = total_cost - hold_cost
        pos["realized_cost"]   = realized_cost
        pos["realized_pnl"]    = total_receive - realized_cost
        pos["realized_return"] = pos["realized_pnl"] / realized_cost if realized_cost else 0.0

        return pos

    except Exception as exc:
        print(f"[format_position] error: {exc}")
        return None
