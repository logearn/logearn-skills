"""
LogEarn — signal token formatter (Python translation of format_v2_degen_signals)
"""

import json
import time
from datetime import datetime, timezone
from typing import Optional

from tools.fmt_token_info import (
    format_token,
    recursive_json_parse,
    ALL_SUPPORT_CHAINS,
)
# ---------------------------------------------------------------------------
# Platform registry  (mirrors platformOptions in JS)
# ---------------------------------------------------------------------------
PLATFORM_OPTIONS: dict[str, dict] = {
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": {"label": "Pump",         "type": "trench",    "chain": 3},
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": {"label": "Pump AMM",      "type": "swap",      "chain": 3},
    "mayhem":                                        {"label": "Pump Mayhem",   "type": "trench",    "chain": 3},
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": {"label": "Raydium",       "type": "swap",      "chain": 3},
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": {"label": "CPMM",          "type": "swap",      "chain": 3},
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": {"label": "CAMM",          "type": "swap",      "chain": 3},
    "9SkAtSxgNUMvT9bGb93v6rLU5MjW1XibykqoGtqT9dbg": {"label": "WenDev",        "type": "trench",     "chain": 3},
    "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj":  {"label": "Launpad",       "type": "trench",     "chain": 3},
    "FfYek5vEz23cMkWsdJwG2oa6EphsvXSHrGpdALN4g6W1": {"label": "LetsBonk 1",   "type": "trench",     "chain": 3},
    "BuM6KDpWiTcxvrpXywWFiw45R2RNH8WURdvqoTDV1BW4": {"label": "LetsBonk 2",   "type": "trench",     "chain": 3},
    "4Bu96XjU84XjPDSpveTVf6LYGCkfW5FK7SNkREWcEfV4": {"label": "Labs",          "type": "trench",     "chain": 3},
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": {"label": "Pools",         "type": "swap",      "chain": 3, "is_meteora": True},
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo":  {"label": "DLMM",          "type": "trench",    "chain": 3, "is_meteora": True},
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG":  {"label": "DLMM V2",       "type": "trench",    "chain": 3, "is_meteora": True},
    "dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN":  {"label": "Meteora DBC",   "type": "trench",    "chain": 3, "is_meteora": True},
    "FbKf76ucsQssF7XZBuzScdJfugtsSKwZFYztKsMEhWZM": {"label": "Moonshit",      "type": "trench",    "chain": 3, "is_meteora": True},
    "Bov7gMQ88BQbtFMTxQ5e8grtrwG4ryQGAV9Mih2j9SxK": {"label": "Dynamic DBC",  "type": "swap",      "chain": 3, "is_meteora": True},
    "BAGSB9TpGrZxQbEsrEznv5jXXdwyP6AXerN8aVRiAmcv": {"label": "Bags",          "type": "trench",     "chain": 3, "is_meteora": True},
    "GybkUNYVNk1FZMt9myAfvpSVgoKBgaueMTvszwBN4qYx": {"label": "AnoncoinIt",   "type": "trench",      "chain": 3, "is_meteora": True},
    "8rE9CtCjwhSmbwL5fbJBtRFsS3ohfMcDFeTTC7t4ciUA": {"label": "Studio",        "type": "trench",     "chain": 3, "is_meteora": True},
    "7UNpFBfTdWrcfS7aBQzEaPgZCfPJe8BDgHzwmWUZaMaF": {"label": "TrendFun",      "type": "trench",     "chain": 3, "is_meteora": True},
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc":  {"label": "Whirl",         "type": "swap",      "chain": 3},
    "MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG":  {"label": "Moonshot",      "type": "trench",     "chain": 3},
    "boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4":  {"label": "Boop",          "type": "trench",     "chain": 3},
    "HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o": {"label": "Heaven",        "type": "trench",     "chain": 3},
    "pancake":                                       {"label": "Pancake",       "type": "swap",       "chain": 56},
    "pancake_v2":                                    {"label": "Pancake V2",    "type": "swap",       "chain": 56},
    "pancake_v3":                                    {"label": "Pancake V3",    "type": "swap",       "chain": 56},
    "four.meme":                                     {"label": "Four",          "type": "trench",     "chain": 56},
    "binance_four.meme":                             {"label": "Binance Four",  "type": "trench",     "chain": 56},
    "flap":                                          {"label": "Flap",          "type": "trench",     "chain": 56},
}


def _platform_config(token: dict) -> Optional[dict]:
    """Mirror platformConfig(token) from JS."""
    platform: str = token.get("platform") or ""
    if not platform:
        return None
    parts = platform.split("_")
    if len(parts) > 1 and len(platform) > 40 and not PLATFORM_OPTIONS.get(platform):
        platform = parts[1] if PLATFORM_OPTIONS.get(parts[1]) else parts[0]
    return PLATFORM_OPTIONS.get(platform)


def _calc_is_hot(whale_count: int) -> str:
    """Mirror calc_is_hot — returns fire-emoji string based on whale signal count."""
    if whale_count > 11:
        return "🔥🔥🔥"
    elif whale_count > 5:
        return "🔥🔥"
    elif whale_count >= 3:
        return "🔥"
    return ""


def _calc_featured_index(token: dict, whale_count: int) -> float:
    """Mirror calc_featured_index — scoring heuristic for hot-token ranking."""
    score: float = 0.0
    mcap         = float(token.get("mcap") or 0)
    max_up_mcap  = float(token.get("max_up_mcap") or 0)
    swap_begin   = float(token.get("swap_begin_time") or 0)
    now          = time.time()
    age          = now - swap_begin

    p1d  = float(token.get("price_change_1d")  or 0)
    p6h  = float(token.get("price_change_6h")  or 0)
    p1h  = float(token.get("price_change_1h")  or 0)
    p5m  = float(token.get("price_change_5m")  or 0)

    if p1d < -80 or p6h < -30 or (max_up_mcap * 0.3 > mcap > 0) or p1d < -30:
        return -10.0
    if age > 30 * 60 and (token.get("buyer_count_d1", 0) + token.get("seller_count_d1", 0)) < 300:
        return -10.0
    if 3 * 3600 < age < 24 * 3600 and p1d < 1000:
        return -10.0

    if p1h > 70:
        score += 1
    if p5m > 30:
        score += 1
    if whale_count >= 3:
        score += 2
    if token.get("analysis_whale_signal_time"):
        score += 1
    if age < 24 * 3600:
        score += 0.5
    if p1h < 10 or p6h < 10:
        score -= 2
    if max_up_mcap > 0 and max_up_mcap / 2 > mcap:
        score -= 2
    if token.get("is_meteora"):
        score -= 1
    if token.get("is_fake"):
        score -= 1
    if float(token.get("signal_max_ratio") or 0) < 100:
        score -= 1.5
    return score


def _format_hot_index(token: dict, whale_count: int) -> None:
    """Mirror format_hot_index — mutates token in-place."""
    hot = _calc_is_hot(whale_count)
    token["hot"]       = hot
    token["hot_index"] = len(hot)

    pc = _platform_config(token)
    chain_cfg = ALL_SUPPORT_CHAINS.get(token.get("chain", 3), {})

    token["is_trench_token"] = (
        bool(token.get("is_trench_token"))
        or hot != ""
        or bool(pc and pc.get("type") == "trench")
    )
    token["is_meteora"]     = bool(pc.get("is_meteora")) if pc else False
    token["platform_icon"]  = (pc or {}).get("icon")  or chain_cfg.get("logo", "")
    token["platform_name"]  = (pc or {}).get("label") or chain_cfg.get("full_name", "")

    token["m5_featured_index"] = _calc_featured_index(token, whale_count)
    token["h1_featured_index"] = _calc_featured_index(token, whale_count)

    now          = time.time()
    swap_begin   = float(token.get("swap_begin_time") or 0)
    is_recent    = now - swap_begin < 6 * 30 * 24 * 3600
    addr         = token.get("token_address", "")
    pc_label     = (pc or {}).get("label", "")
    whale_ok     = not token.get("analysis_whale_signal_time")
    not_top      = not token.get("is_top_token")
    not_diamond  = not token.get("is_diamond_token")

    token["is_fake_pump"] = bool(
        "pump" in addr
        and pc_label not in ("Pump", "Pump AMM")
        and whale_ok and is_recent and not_top and not_diamond
    )
    token["is_fake_four"] = bool(
        "4444" in addr
        and pc_label not in ("Four V1", "Four V2", "Four", "Binance Four")
        and whale_ok and is_recent and not_top and not_diamond
    )
    token["is_fake_bonk"] = bool(
        "bonk" in addr
        and pc_label not in ("Launpad", "LetsBonk 1", "LetsBonk 2", "Labs")
        and whale_ok and is_recent and not_top and not_diamond
    )
    token["is_fake"] = token["is_fake_pump"] or token["is_fake_four"] or token["is_fake_bonk"]


# maps signal_type → raw field name in the API token object
_SIGNALS_TYPE_AND_DATA_FIELD_MAP = {
  'whale': 'whale_list',
  'continue_breakout_volume': 's15_list',
  'breakout_volume_10x': 's300_list',
  'v_breakout_volume': 'kline_list',
  'followed': 'notification_list'
}


def _parse_block_time(block_time: str) -> float:
    """ISO-8601 blockTime → unix seconds (whale signal)."""
    if not block_time:
        return 0.0
    try:
        dt = datetime.fromisoformat(block_time.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        try:
            return float(block_time) / 1000
        except Exception:
            return 0.0


def format_signal(
    token_signals: Optional[dict],
    native_prices: Optional[dict] = None,
) -> Optional[dict]:
    """
    Translate a raw signal token object into a normalised dict with
    per-signal-type alert lists attached.

    Args:
        token_signals:  Raw token+signal dict from the API.
        native_prices:  Live native-token USD prices, e.g. {56: 630, 3: 86}.
                        Defaults to {56: 630, 3: 86}.
    """
    if not token_signals:
        return None

    if native_prices is None:
        native_prices = {56: 630, 3: 86}

    _token = format_token(token_signals, native_prices)
    if not _token:
        return None

    chain         = _token["chain"]
    chain_cfg     = ALL_SUPPORT_CHAINS[chain]
    w_decimals    = chain_cfg["decimal"]
    native_price  = native_prices.get(chain, 1.0)
    token_decimals = _token["decimals"]
    total_supply  = _token["total_supply"]

    price_scale = (
        10 ** (token_decimals - w_decimals)
        if token_decimals >= w_decimals
        else 1 / (10 ** (w_decimals - token_decimals))
    )

    last_traded: float = float(_token.get("last_traded") or 0)
    all_signals_list = {}

    for signals_type, data_field in _SIGNALS_TYPE_AND_DATA_FIELD_MAP.items():
        raw = token_signals.get(data_field) or "[]"
        try:
            tnex = json.loads(raw)
        except Exception:
            tnex = []
        if not isinstance(tnex, list):
            tnex = [tnex]
        tnex = [x for x in tnex if x]  # compact

        alerts = []
        for tx_temp in tnex:
            # whale items may be double-JSON-encoded
            alert = recursive_json_parse(tx_temp) if signals_type == "whale" else tx_temp

            # --- signalTime ---
            if signals_type == "whale":
                signal_time = _parse_block_time(alert.get("blockTime") or "")
            else:
                signal_time = float(alert.get("signal_time") or 0)

            if signals_type == "v_breakout_volume":
                signal_time = max(
                    float(alert.get("fibon_break1_time") or 0),
                    float(alert.get("fibon_break2_time") or 0),
                    float(alert.get("fibon_break3_time") or 0),
                    float(alert.get("fibon_break4_time") or 0),
                )
                alert['fibon_break1'] = float(alert.get("fibon_break1") or 0) * price_scale * total_supply * native_price
                alert['fibon_break2'] = float(alert.get("fibon_break2") or 0) * price_scale * total_supply * native_price
                alert['fibon_break3'] = float(alert.get("fibon_break3") or 0) * price_scale * total_supply * native_price
                alert['fibon_break4'] = float(alert.get("fibon_break4") or 0) * price_scale * total_supply * native_price

                top_price_mcap = float(alert.get("top_price") or 0) * price_scale * total_supply * native_price
                low_price_mcap = float(alert.get("low_price") or 0) * price_scale * total_supply * native_price
            elif signals_type in ("breakout_volume_10x", "continue_breakout_volume"):
                created_time = float(alert.get("created_time") or 0)
                if created_time > 1:
                    signal_time = created_time
                top_price_mcap = None
                low_price_mcap = None
            elif signals_type == 'followed':
                signal_time = float(alert.get("block_time") or 0)
                top_price_mcap = None
                low_price_mcap = None
            else:
                top_price_mcap = None
                low_price_mcap = None

            notice: dict = {
                **alert,
                "signalTime":    signal_time,
                "max_up_mcap":   _token.get("max_up_mcap"),
                "type":          signals_type,
                "top_price_mcap": top_price_mcap,
                "low_price_mcap": low_price_mcap,
                "decimals":      token_decimals,
                "symbol":        _token["symbol"],
                "token_address": _token["token_address"],
                "total_supply":  total_supply,
                "chain":         chain,
                "swap_begin_time": _token.get("swap_begin_time"),
            }

            # --- notice_mcap per signal type ---
            if signals_type == "breakout_volume_10x":
                notice["notice_mcap"] = (
                    float(alert.get("current_close_price") or 0) * total_supply * native_price
                )
                notice["max_up_mcap_time"] = _token.get("max_up_mcap_time")
            elif signals_type == "continue_breakout_volume":
                notice["notice_mcap"] = (
                    float(alert.get("signal_price") or 0) * total_supply * native_price
                )
            elif signals_type == "whale":
                notice["notice_mcap"] = (
                    float(alert.get("signal_price_v1") or 0) * total_supply * price_scale * native_price
                )
            elif signals_type == 'followed':
                time = int(alert.get("block_time") or 0)
                trade_type = alert.get("trade_type")
                if int(alert.get("trade_type") or 0) == 3:
                    trade_type = 'transfer-out' if alert.get("is_followed") else 'transfer-in'

                amount = int(alert.get("amount_token") or 0)
                value = int(alert.get("amount_coin") or 0)
                price = value / amount

                notice["amount"] = amount / (10 ** token_decimals)
                notice["value"] = value / chain_cfg['full_decimal']
                notice["time"] = time
                notice["signalTime"] = time
                notice["trade_type"] = trade_type
                notice["wallet"] = alert.get("caller")
                notice["notice_mcap"] = price * total_supply * price_scale * native_price

            alerts.append(notice)
            last_traded = max(last_traded, signal_time or 0)

        all_signals_list[f"{signals_type}_list"] = sorted(
            alerts, key=lambda x: float(x.get("signalTime") or 0), reverse=True
        )

    _token["all_signals_list"] = all_signals_list

    whale_count = len(all_signals_list.get("whale", []))
    _format_hot_index(_token, whale_count)

    _token["last_traded"] = last_traded
    return _token