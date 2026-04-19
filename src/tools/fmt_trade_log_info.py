"""
LogEarn — trade log formatter (Python translation of formate_logs)
"""

from typing import Optional

_ORDER_STATUS_DEFAULT = {
    0: "NEW",
    1: "DOING",
    2: "PACKAGE_SUCCESS",
    3: "PACKAGE_FAILED",
    4: "PAY_SUCCESS",
    6: "PACKAGE_FAILED",
    7: "PACKAGE_FAILED",
}


def format_trade_log(log: Optional[dict]) -> Optional[dict]:
    if not log:
        return None

    try:
        i = dict(log)

        copyer_type: str = (i.get("copyer_type") or "").lower()
        order_status = i.get("order_status")

        # --- order_status normalisation ---
        if copyer_type in ("stop-loss", "stop-profit"):
            i["order_status"] = "STOP_SUCCESS" if order_status == 5 else "STOP_FAILED"
        elif copyer_type == "manual-decrease":
            i["order_status"] = "MANUAL_SUCCESS" if order_status == 1 else "MANUAL_FAILED"
        else:
            i["order_status"] = _ORDER_STATUS_DEFAULT.get(order_status, str(order_status))

        # --- buy / sell split ---
        if "buy" in copyer_type:
            i["type"] = "buy"
            dec_in  = int(i.get("copyer_token_decimal_in")  or 0)
            dec_out = int(i.get("copyer_token_decimal_out") or 0)

            raw_coin   = i.get("amount_coin")  or i.get("copyer_collateral_delta") or 0
            raw_token  = i.get("amount_token") or i.get("copyer_size_delta")       or 0

            i["amount_coin"]    = float(raw_coin)  / (10 ** dec_in)  if dec_in  else float(raw_coin)
            i["coin_name"]      = (i.get("copyer_collateral_token_name") or "").replace("W", "")
            i["amount_token"]   = float(raw_token) / (10 ** dec_out) if dec_out else float(raw_token)
            i["token_name"]     = (i.get("copyer_index_token_name") or "").replace("W", "")
            i["token_address"]  = i.get("copyer_index_token_address")
            i["token_decimals"] = dec_out

            ts = float(i.get("total_supply") or 0)
            i["total_supply"]   = ts / (10 ** dec_out) if dec_out else ts

        else:
            i["type"] = "sell"
            dec_in  = int(i.get("copyer_token_decimal_in")  or 0)
            dec_out = int(i.get("copyer_token_decimal_out") or 0)

            raw_coin   = i.get("amount_coin")  or i.get("copyer_size_delta")       or 0
            raw_token  = i.get("amount_token") or i.get("copyer_collateral_delta") or 0

            i["amount_coin"]    = float(raw_coin)  / (10 ** dec_out) if dec_out else float(raw_coin)
            i["coin_name"]      = (i.get("copyer_index_token_name") or "").replace("W", "")
            i["amount_token"]   = float(raw_token) / (10 ** dec_in)  if dec_in  else float(raw_token)
            i["token_name"]     = (i.get("copyer_collateral_token_name") or "").replace("W", "")
            i["token_decimals"] = dec_in
            i["token_address"]  = i.get("copyer_collateral_token_address")

            ts = float(i.get("total_supply") or 0)
            i["total_supply"]   = ts / (10 ** dec_in) if dec_in else ts

        i["amount"] = i["amount_token"]
        i["price"]  = i["amount_coin"] / i["amount_token"] if i["amount_token"] else 0.0

        return i

    except Exception as exc:
        print(f"[format_trade_log] error: {exc}")
        return None