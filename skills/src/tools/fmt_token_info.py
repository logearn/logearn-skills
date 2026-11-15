"""
Python translation of src/tools/fmt_token_info/fmt.js :: _forate_token
"""

import json
import time
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Chain config  (mirrors all_support_chains in JS)
# BSC=56: native BNB, decimal=18
# Solana=3: native SOL, decimal=9
# ---------------------------------------------------------------------------
ALL_SUPPORT_CHAINS: dict[int, dict] = {
    56: {"decimal": 18, "full_decimal": 10 ** 18, "native_token": "BNB", "full_name": "BSC",    "logo": "/images/icons/chains/bsc.svg"},
    3:  {"decimal": 9,  "full_decimal": 10 ** 9,  "native_token": "SOL", "full_name": "Solana", "logo": "/images/icons/chains/sol.svg"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def recursive_json_parse(value: Any) -> Any:
    """Parse JSON strings recursively (mirrors recursiveJSONParse in JS)."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return recursive_json_parse(parsed)
        except (json.JSONDecodeError, ValueError):
            return value
    if isinstance(value, dict):
        return {k: recursive_json_parse(v) for k, v in value.items()}
    if isinstance(value, list):
        return [recursive_json_parse(i) for i in value]
    return value


def ms_time(t: Any) -> float:
    """Normalise timestamp to seconds (JS version divides ms → s)."""
    if t is None:
        return 0
    s = str(t)
    try:
        v = float(s)
        return v / 1000 if len(s.split('.')[0]) > 10 else v
    except (ValueError, TypeError):
        return 0


def _format_in_indicator(number: float) -> float:
    """foramte_in_indicatr — zero-floor near-zero negatives."""
    if number < -2:
        return number
    return 0 if number < 1 else number


def _calc_progress(token: dict) -> float:
    """calc_progress — bonding-curve progress estimate."""
    if not token.get("launch_time") and (token.get("mcap") or 0) < 80000:
        return (token.get("mcap") or 0) / 60000 * 100
    return 100.0


# ---------------------------------------------------------------------------
# Best-signal performance (mirrors calcBestSignalPerformance)
# native_prices: {56: <bnb_usd>, 3: <sol_usd>}  caller must supply
# ---------------------------------------------------------------------------

_SIGNALS_CONFIG = [
    {
        "type": "v_breakout_volume",
        "openKey": "kline_signal_open_price",
        "maxKey":  "kline_signal_max_price",
        "openTimeKey": "kline_signal_open_time",
        "maxTimeKey":  "kline_signal_max_time",
    },
    {
        "type": "continue_breakout_volume",
        "openKey": "s15_signal_open_price",
        "maxKey":  "s15_signal_max_price",
        "openTimeKey": "s15_signal_open_time",
        "maxTimeKey":  "s15_signal_max_time",
    },
    {
        "type": "breakout_volume_10x",
        "openKey": "s300_signal_open_price",
        "maxKey":  "s300_signal_max_price",
        "openTimeKey": "s300_signal_open_time",
        "maxTimeKey":  "s300_signal_max_time",
    },
    {
        "type": "whale",
        "openKey": "whale_signal_open_price",
        "maxKey":  "whale_signal_max_price",
        "openTimeKey": "whale_signal_open_time",
        "maxTimeKey":  "whale_signal_max_time",
    },
]


def calc_best_signal_performance(
    token_tag: dict,
    token: dict,
    chain: int,
    w_decimals: int,
    native_price: float = 1.0,
) -> dict:
    best = {
        "type": None,
        "open_price": 0,
        "max_price": 0,
        "open_time": 0,
        "max_time": 0,
        "open_mcap": 0,
        "max_mcap": 0,
        "max_ratio": 0,
    }
    all_signals_max_ratio: dict = {}

    token_decimals = int(token.get("decimals") or 0)
    total_supply = float(token.get("total_supply") or 0) / (10 ** token_decimals) if token_decimals else 0

    for cfg in _SIGNALS_CONFIG:
        open_price = float(token_tag.get(cfg["openKey"]) or 0)
        max_price  = float(token_tag.get(cfg["maxKey"])  or 0)
        if not open_price or not max_price:
            continue

        ratio = (max_price - open_price) / open_price * 100
        if ratio <= 0:
            continue

        price_scale = 10 ** (token_decimals - w_decimals)
        open_mcap = open_price * price_scale * total_supply * native_price
        max_mcap  = max_price  * price_scale * total_supply * native_price

        open_time = ms_time(token_tag.get(cfg["openTimeKey"]))
        max_time  = ms_time(token_tag.get(cfg["maxTimeKey"]))

        all_signals_max_ratio[cfg["type"]] = {
            "open_time": open_time,
            "open_mcap": open_mcap,
            "max_time":  max_time,
            "max_mcap":  max_mcap,
            "max_ratio": ratio,
            "type":      cfg["type"],
        }

        if ratio > best["max_ratio"]:
            best = {
                "type":       cfg["type"],
                "open_price": open_price,
                "max_price":  max_price,
                "open_time":  open_time,
                "max_time":   max_time,
                "open_mcap":  open_mcap,
                "max_mcap":   max_mcap,
                "max_ratio":  ratio,
            }

    return {**best, "all_signals_max_ratio": all_signals_max_ratio}


# ---------------------------------------------------------------------------
# Main formatter  (mirrors _forate_token)
# native_prices: {56: <bnb_usd>, 3: <sol_usd>}  — pass live prices from caller
# ---------------------------------------------------------------------------

def format_token(
    token: Optional[dict],
    native_prices: Optional[dict] = None,
) -> Optional[dict]:
    """
    Translate raw API token object into a normalised dict.

    Args:
        token:         Raw token dict from the API.
        native_prices: Live native-token USD prices, e.g. {56: 600.0, 3: 150.0}.
                       Defaults to {56: 1.0, 3: 1.0} (prices unknown).
    """
    if not token:
        token = {}

    if native_prices is None:
        native_prices = {56: 630, 3: 86}

    token_address: str = token.get("token_address") or ""
    chain: int = 56 if token_address.startswith("0x") else 3
    chain_cfg = ALL_SUPPORT_CHAINS[chain]
    w_decimals: int = chain_cfg["decimal"]
    full_decimal: float = chain_cfg["full_decimal"]
    native_price: float = native_prices.get(chain, 1.0)

    # --- parse nested JSON strings ---
    main_pool    = recursive_json_parse(token.get("main_pool")    or "{}")
    token_change = recursive_json_parse(token.get("token_change") or "{}")
    token_tag    = recursive_json_parse(token.get("token_tag")    or "{}")
    ai_signal    = recursive_json_parse(token.get("ai_signal")    or "{}")
    inside_pool  = recursive_json_parse(token.get("inside_pool")  or "{}")
    off_meta     = recursive_json_parse(token.get("off_meta")     or "{}")

    inside_platform = token.get("inside_platform")
    swap_mode = "mayhem" if token.get("swap_mode") == 1 else None # 1表示 pumpfun 混乱模式

    token_decimals: int = int(token.get("decimals") or 0)
    total_supply_raw: float = float(token.get("total_supply") or 0)
    total_supply: float = total_supply_raw / (10 ** token_decimals) if token_decimals else 0

    last_price: float = float(main_pool.get("last_price") or 0)
    price_scale: float = 10 ** (token_decimals - w_decimals) if token_decimals >= w_decimals else 1 / (10 ** (w_decimals - token_decimals))
    mcap_calc: float = last_price * price_scale * total_supply * native_price if last_price else 0
    mcap: float = float(main_pool.get("mcp") or 0) or mcap_calc

    best_signal = calc_best_signal_performance(token_tag, token, chain, w_decimals, native_price)

    try:
        # --- price changes ---
        def _pct_change(latest_key: str, earliest_key: str) -> float:
            latest   = float(token_change.get(latest_key)   or 0)
            earliest = float(token_change.get(earliest_key) or 0)
            if not latest or not earliest:
                return 0.0
            return (latest - earliest) / earliest * 100

        # --- AI sniper signal ---
        ai_signal_price: float = float(ai_signal.get("signal_price") or 0)
        ai_signal_time: float  = ms_time(ai_signal.get("signal_time"))
        open_price_time: float = ms_time(token.get("open_price_time"))
        launch_time: float     = ms_time(token.get("launch_time"))

        swap_begin_time: float = (
            min(open_price_time, launch_time)
            if token.get("launch_time") else open_price_time
        )

        # --- max-up from open ---
        max_price_tag: float = float(token_tag.get("max_price") or 0)
        open_price:    float = float(token.get("open_price") or token.get("latest_price") or 0)

        max_up_ratio = (
            (max_price_tag - open_price) / open_price * 100
            if max_price_tag and open_price else None
        )
        max_up_mcap = (
            max_price_tag * price_scale * total_supply * native_price
            if max_price_tag else None
        )

        # --- AI max up ---
        ai_max_price: float = float(token_tag.get("ai_max_price") or 0)
        ai_max_up_ratio = (
            (ai_max_price - ai_signal_price) / ai_signal_price
            if ai_max_price and ai_signal_price else None
        )

        # --- tag_chip_24h chip distribution ---
        tag_chip_24h = recursive_json_parse(token.get("tag_chip_24h") or "{}")
        chip_fields: dict = {}
        if tag_chip_24h and total_supply_raw:
            for field in [
                "amm_volume", "exchange_volume", "frequent_volume",
                "new_volume", "old_volume", "scam_volume",
                "shit_volume", "smart_volume", "whale_volume",
            ]:
                raw_val = float(tag_chip_24h.get(field) or 0)
                chip_fields[field] = _format_in_indicator(raw_val / total_supply_raw * 100)

        next_token: dict = {
            # identity
            "token_address": token_address,
            "symbol":        token.get("symbol") or "",
            "token_name":    token.get("token_name") or "",
            "total_supply":  total_supply,
            "decimals":      token_decimals,
            "chain":         chain,
            "platform":      swap_mode or inside_pool.get("platform") or inside_platform or main_pool.get("platform"),
            "creator_address": token.get("creator_address") or "",
            "creator_tag":   [],
            "main_pool_address": main_pool.get("pool_address"),
            "off_meta":      off_meta,

            # timing
            "swap_begin_time": swap_begin_time,
            "launch_time":     launch_time,
            "launch_time_duration": (launch_time - open_price_time) if token.get("launch_time") else 0,

            # price & market cap
            "price_now":      last_price * price_scale,
            "price_change_1d": _pct_change("d1_latest_price", "d1_earliest_price"),
            "price_change_6h": _pct_change("h6_latest_price", "h6_earliest_price"),
            "price_change_1h": _pct_change("h1_latest_price", "h1_earliest_price"),
            "price_change_5m": _pct_change("m5_latest_price", "m5_earliest_price"),
            "fdv":         mcap,
            "mcap":        mcap,
            "current_mcap":mcap,
            "pool_liquidity": float(main_pool.get("liquidity") or 0),

            # all-time high from open
            "max_up_duration": (
                ms_time(token_tag.get("max_price_time")) - open_price_time
                if token_tag.get("max_price_time") else None
            ),
            "max_up_ratio":    max_up_ratio,
            "max_up_mcap":     max_up_mcap,
            "max_up_mcap_time": ms_time(token_tag.get("max_price_time")),

            # 24h trading stats
            "smart_money_address_buy_count_d1":  int(token_change.get("d1_sm_buyer_count")  or 0),
            "smart_money_address_sell_count_d1": int(token_change.get("d1_sm_seller_count") or 0),
            "buyer_count_d1":  int(token_change.get("d1_buyer_count")  or 0),
            "seller_count_d1": int(token_change.get("d1_seller_count") or 0),
            "buy_tx_count_d1":  int(token_change.get("d1_buy_count")  or 0),
            "sell_tx_count_d1": int(token_change.get("d1_sell_count") or 0),
            "buy_wcoin_amount_d1":  float(token_change.get("d1_buy_coin")  or 0) / full_decimal,
            "sell_wcoin_amount_d1": float(token_change.get("d1_sell_coin") or 0) / full_decimal,
            "buy_wcoin_amount_m5":  float(token_change.get("m5_buy_coin")  or 0) / full_decimal,
            "buy_wcoin_amount_h1":  float(token_change.get("h1_sell_coin") or 0) / full_decimal,
            "signal_count_d1":  int(token_change.get("d1_whale_signal_count") or 0),

            # AI sniper
            "analysis_open_price":             ai_signal_price * price_scale,
            "analysis_whale_signal_time":      ai_signal_time,
            "analysis_whale_signal_mcap":      ai_signal_price * price_scale * total_supply,
            "analysis_whale_signal_time_duration": (
                ai_signal_time - open_price_time if ai_signal_time else 0
            ),

            # AI max up after signal
            "ai_max_up_ratio":      ai_max_up_ratio,
            "ai_max_price_time":    ms_time(token_tag.get("ai_max_price_time")),
            "ai_max_up_duration": (
                ms_time(token_tag.get("ai_max_price_time")) - ai_signal_time
                if token_tag.get("ai_max_price_time") and ai_signal_time else None
            ),
            "ai_max_up_ratio_mcap": ai_max_price * price_scale * total_supply,

            # best signal summary
            "signal_open_time":  best_signal["open_time"],
            "signal_open_mcap":  best_signal["open_mcap"],
            "signal_max_time":   best_signal["max_time"],
            "signal_max_mcap":   best_signal["max_mcap"],
            "signal_max_ratio":  best_signal["max_ratio"],
            "signal_best_type":  best_signal["type"],
            "all_signals_max_ratio": best_signal["all_signals_max_ratio"],

            # safety flags from token_tag
            "is_diamond_token":      token_tag.get("is_diamond_token"),
            "is_error_market_token": token_tag.get("is_error_market_token"),
            "is_honey":              token_tag.get("is_honey"),
            "is_scam_token":         token_tag.get("is_scam_token"),
            "is_top_token":          token_tag.get("is_top_token"),
            "profit_usernum":        token_tag.get("profit_usernum"),

            "total_record": token.get("total_record") or 0,

            # chip distribution (% of total supply, 24h)
            "tag_users_holding_percent": {
               **chip_fields,
            }
        }

        # progress (bonding curve)
        next_token["progress"] = _calc_progress(next_token)

        # is_trench_token: launched via bonding curve or has AI signal
        next_token["is_trench_token"] = bool(
            inside_pool.get("platform") or launch_time or ai_signal_time
        )

        return next_token

    except Exception as exc:
        print(f"[format_token] error: {exc}")
        return None