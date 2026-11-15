"""
LogEarn — limit order formatter (Python translation of formate_order)
"""

import json
from typing import Optional
from tools.fmt_token_info import ALL_SUPPORT_CHAINS


def format_limit_order(
    order: Optional[dict],
    native_prices: Optional[dict] = None,
) -> Optional[dict]:
    if not order:
        return None

    if native_prices is None:
        native_prices = {56: 630, 3: 86}

    try:
        i = dict(order)

        # parse action JSON string
        action_raw = i.get("action")
        if isinstance(action_raw, str):
            i["action"] = json.loads(action_raw)
        action: dict = i["action"] or {}

        token_decimals: int = int(i.get("decimals") or 0)
        total_supply_raw    = float(i.get("total_supply") or 0)
        i["total_supply"]   = total_supply_raw / (10 ** token_decimals) if token_decimals else total_supply_raw

        chain_id: int = int(i.get("chain_id") or i.get("chainId") or 3)
        chain_cfg         = ALL_SUPPORT_CHAINS.get(chain_id, ALL_SUPPORT_CHAINS[3])
        w_decimals: int   = chain_cfg["decimal"]
        full_decimal: int = chain_cfg["full_decimal"]
        native_token: str = chain_cfg["native_token"]
        native_price: float = native_prices.get(chain_id, 1.0)

        limit_number = float(action.get("limitNumber") or 0)
        limit_type   = int(action.get("limitType") or 0)

        if limit_type == 2:
            # limitNumber is a USD market-cap value
            divisor = i["total_supply"] / (10 ** token_decimals) if token_decimals else i["total_supply"]
            i["target_price"] = (limit_number / divisor / native_price) if divisor else 0.0
        else:
            # limitNumber is a native-coin price (raw)
            price_exp = w_decimals - token_decimals
            price_div = 10 ** price_exp if price_exp >= 0 else 1.0 / (10 ** (-price_exp))
            i["target_price"] = limit_number / price_div if price_div else 0.0

        direction = int(action.get("direction") or 0)
        i["direction_text"] = "rise_to" if direction == 1 else "fall_to"

        if action.get("key") == "buy":
            amount_in = float(action.get("amountIn") or 0)
            human_in  = amount_in / full_decimal
            i["target_op_assets"]     = f"{human_in} {native_token}"
            i["target_op_assets_usd"] = f"${human_in * native_price}"
        else:
            amount_in = float(action.get("amountIn") or 0)
            human_in  = amount_in / (10 ** token_decimals) if token_decimals else amount_in
            symbol    = i.get("symbol") or ""
            i["target_op_assets"] = f"{human_in} {symbol}"

        i["chain"] = chain_id
        return i

    except Exception as exc:
        print(f"[format_limit_order] error: {exc}")
        return None