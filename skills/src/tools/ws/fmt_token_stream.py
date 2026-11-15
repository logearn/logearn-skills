"""
WebSocket formatter: /token_stream_v2:3  /token_stream_v2:56

Received message format:
    {
      "type": "data",
      "bytes": 399717,
      "data": {
        "data": {
          "<timestamp_ms>": [<compressed_token_obj>, ...]
        }
      }
    }

Token objects are key-compressed for bandwidth. decompress_token() restores
original field names before passing to format_token().
Translatable to TypeScript / Go / Rust — see ws_api.md for details.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.fmt_token_info import format_token, recursive_json_parse
from typing import Any, Dict, List, Optional

# ==================== 压缩 key 映射表 ====================

_TOP_KEY_MAP: Dict[str, str] = {
    '1':    'token_address',
    '2':    'symbol',
    '3':    'decimals',
    '4':    'total_supply',
    '5':    'inside_platform',
    '6':    'open_price',
    '7':    'open_price_time',
    '8':    'latest_price',
    '9':    'latest_price_time',
    '10':   'token_name',
    '11':   'creator_address',
    '12':   'launch_time',
    '13':   'swap_mode',
    '14':   'chain',
    'mp':   'main_pool',
    'ip':   'inside_pool',
    'om':   'off_meta',
    'as':   'ai_signal',
    'tt':   'token_tag',
    'tc':   'token_change',
    'ki':   'kline_indicators',
    'tc24': 'tag_chip_24h',
}

_MAIN_POOL_KEY_MAP: Dict[str, str] = {
    'mp_1':  'pool_address',
    'mp_2':  'mcp',
    'mp_3':  'liquidity',
    'mp_4':  'platform',
    'mp_5':  'last_price',
    'mp_6':  'last_price_time',
    'mp_7':  'token_a',
    'mp_8':  'token_b',
    'mp_9':  'vault_a',
    'mp_10': 'vault_b',
    'mp_11': 'amount_a',
    'mp_12': 'amount_b',
    'mp_13': 'symbol_a',
    'mp_14': 'symbol_b',
    'mp_15': 'decimals_a',
    'mp_16': 'decimals_b',
    'mp_17': 'total_supply_a',
    'mp_18': 'total_supply_b',
}

_AI_SIGNAL_KEY_MAP: Dict[str, str] = {
    'as_1': 'strategy_num',
    'as_2': 'strategy_info',
    'as_3': 'signal_price',
    'as_4': 'signal_time',
    'as_5': 'ai_max_price_time',
    'as_6': 'ai_max_price',
}

_TOKEN_TAG_KEY_MAP: Dict[str, str] = {
    'tt_1':  'is_honey',
    'tt_2':  'is_scam_token',
    'tt_3':  'is_diamond_token',
    'tt_4':  'is_top_token',
    'tt_5':  'is_error_market_token',
    'tt_6':  'profit_usernum',
    'tt_7':  'ai_open_price',
    'tt_8':  'ai_max_price',
    'tt_9':  'ai_max_price_time',
    'tt_10': 'ai_max_up_ratio',
    'tt_11': 'max_price',
    'tt_12': 'open_price',
    'tt_13': 'max_price_time',
    'tt_14': 'whale_signal_max_price',
    'tt_15': 'whale_signal_max_time',
    'tt_16': 'whale_signal_open_price',
    'tt_17': 'whale_signal_open_time',
    'tt_18': 's15_signal_max_price',
    'tt_19': 's15_signal_max_time',
    'tt_20': 's15_signal_open_price',
    'tt_21': 's15_signal_open_time',
    'tt_22': 's300_signal_max_price',
    'tt_23': 's300_signal_max_time',
    'tt_24': 's300_signal_open_price',
    'tt_25': 's300_signal_open_time',
    'tt_26': 'kline_signal_max_price',
    'tt_27': 'kline_signal_max_time',
    'tt_28': 'kline_signal_open_price',
    'tt_29': 'kline_signal_open_time',
}

_TOKEN_CHANGE_KEY_MAP: Dict[str, str] = {
    'tc_1':  'd1_ai_max_price',
    'tc_2':  'd1_s15_max_price',
    'tc_3':  'd1_s300_max_price',
    'tc_4':  'd1_whale_max_price',
    'tc_5':  'd1_kline_max_price',
    'tc_6':  'd1_ai_max_price_time',
    'tc_7':  'd1_s15_max_price_time',
    'tc_8':  'd1_s300_max_price_time',
    'tc_9':  'd1_whale_max_price_time',
    'tc_10': 'd1_kline_max_price_time',
    'tc_11': 'd1_s15_open_price',
    'tc_12': 'd1_s300_open_price',
    'tc_13': 'd1_whale_open_price',
    'tc_14': 'd1_kline_open_price',
    'tc_15': 'd1_s15_open_price_time',
    'tc_16': 'd1_s300_open_price_time',
    'tc_17': 'd1_whale_open_price_time',
    'tc_18': 'd1_kline_open_price_time',
    'tc_19': 'd1_whale_signal_count',
    'tc_20': 'd1_max_price',
    'tc_21': 'h6_max_price',
    'tc_22': 'h1_max_price',
    'tc_23': 'm5_max_price',
    'tc_24': 'd1_min_price',
    'tc_25': 'h6_min_price',
    'tc_26': 'h1_min_price',
    'tc_27': 'm5_min_price',
    'tc_28': 'd1_max_price_time',
    'tc_29': 'h6_max_price_time',
    'tc_30': 'h1_max_price_time',
    'tc_31': 'm5_max_price_time',
    'tc_32': 'd1_min_price_time',
    'tc_33': 'h6_min_price_time',
    'tc_34': 'h1_min_price_time',
    'tc_35': 'm5_min_price_time',
    'tc_36': 'd1_earliest_price',
    'tc_37': 'h6_earliest_price',
    'tc_38': 'h1_earliest_price',
    'tc_39': 'm5_earliest_price',
    'tc_40': 'd1_earliest_time',
    'tc_41': 'h6_earliest_time',
    'tc_42': 'h1_earliest_time',
    'tc_43': 'm5_earliest_time',
    'tc_44': 'd1_latest_time',
    'tc_45': 'h6_latest_time',
    'tc_46': 'h1_latest_time',
    'tc_47': 'm5_latest_time',
    'tc_48': 'd1_latest_price',
    'tc_49': 'h6_latest_price',
    'tc_50': 'h1_latest_price',
    'tc_51': 'm5_latest_price',
    'tc_52': 'd1_buy_count',
    'tc_53': 'h6_buy_count',
    'tc_54': 'h1_buy_count',
    'tc_55': 'm5_buy_count',
    'tc_56': 'd1_sell_count',
    'tc_57': 'h6_sell_count',
    'tc_58': 'h1_sell_count',
    'tc_59': 'm5_sell_count',
    'tc_60': 'd1_buyer_count',
    'tc_64': 'd1_seller_count',
    'tc_68': 'd1_buy_coin',
    'tc_72': 'd1_sell_coin',
    'tc_73': 'd1_sm_buyer_count',
    'tc_74': 'd1_sm_seller_count',
    'tc_75': 'm5_buy_coin',
    'tc_76': 'h1_buy_coin',
    'tc_77': 'm5_sell_coin',
    'tc_78': 'h6_buy_coin',
    'tc_79': 'h6_sell_coin',
    'tc_80': 'h1_sell_coin',
}

_KLINE_INDICATORS_KEY_MAP: Dict[str, str] = {
    'ki_1':  'already_push',
    'ki_2':  'current_price',
    'ki_3':  'current_price_time',
    'ki_4':  'max_price',
    'ki_5':  'max_price_time',
    'ki_6':  'max_price_mcp',
    'ki_7':  'min_price',
    'ki_8':  'min_price_time',
    'ki_9':  'min_price_mcp',
    'ki_10': 'top_price',
    'ki_11': 'top_price_time',
    'ki_12': 'low_price',
    'ki_13': 'low_price_time',
    'ki_14': 'low_price_mcp',
    'ki_15': 'top_price_mcp',
    'ki_16': 'pre_top_price',
    'ki_17': 'pre_top_price_time',
    'ki_18': 'pre_low_price',
    'ki_19': 'pre_low_price_time',
    'ki_20': 'fibon_break1',
    'ki_21': 'fibon_break1_time',
    'ki_22': 'fibon_break2',
    'ki_23': 'fibon_break2_time',
    'ki_24': 'fibon_break3',
    'ki_25': 'fibon_break3_time',
    'ki_26': 'fibon_break4',
    'ki_27': 'fibon_break4_time',
    'ki_28': 'n_pattern_retracement',
    'ki_29': 'current_breakout_ratio',
    'ki_30': 'price_rise_ratio',
    'ki_31': 'n_pattern_confirmed',
    'ki_32': 'is_uptrend',
    'ki_33': 'created_time',
}

_TAG_CHIP_24H_KEY_MAP: Dict[str, str] = {
    'tc24_1':  'granularity',
    'tc24_2':  'start_time',
    'tc24_3':  'end_time',
    'tc24_4':  'whale_volume',
    'tc24_5':  'frequent_volume',
    'tc24_6':  'smart_volume',
    'tc24_7':  'new_volume',
    'tc24_8':  'old_volume',
    'tc24_9':  'shit_volume',
    'tc24_10': 'scam_volume',
    'tc24_11': 'amm_volume',
    'tc24_12': 'exchange_volume',
}

_NESTED_KEY_MAPS: Dict[str, Dict[str, str]] = {
    'main_pool':        _MAIN_POOL_KEY_MAP,
    'ai_signal':        _AI_SIGNAL_KEY_MAP,
    'token_tag':        _TOKEN_TAG_KEY_MAP,
    'token_change':     _TOKEN_CHANGE_KEY_MAP,
    'kline_indicators': _KLINE_INDICATORS_KEY_MAP,
    'tag_chip_24h':     _TAG_CHIP_24H_KEY_MAP,
}


def decompress_token(compressed: Any) -> Any:
    """
    Decompress a WS token object — translates short keys back to full field names.
    Mirror of JS decompressToken().
    """
    if not isinstance(compressed, dict):
        return compressed

    result: Dict[str, Any] = {}
    for key, value in compressed.items():
        original_key = _TOP_KEY_MAP.get(key, key)

        if isinstance(value, dict):
            nested_map = _NESTED_KEY_MAPS.get(original_key)
            if nested_map:
                result[original_key] = {
                    nested_map.get(nk, nk): nv
                    for nk, nv in value.items()
                }
            else:
                result[original_key] = value
        else:
            result[original_key] = value

    return result


def format_token_stream_msg(
    msg: dict,
    native_prices: Optional[dict] = None,
) -> Optional[List[dict]]:
    # msg: => {'type': 'data', 'bytes': 399717, 'data': {'data': {'<ts>': [compressed_token, ...], ...}}}
    if msg.get("type") != "data":
        return None

    data = (msg.get("data") or {}).get("data") or {}
    if not isinstance(data, dict):
        return None

    results = []
    for ts, items in data.items():
        if not isinstance(items, list):
            continue
        for raw in items:
            token = decompress_token(recursive_json_parse(raw))
            if not isinstance(token, dict):
                continue
            formatted = format_token(token, native_prices)
            if formatted is not None:
                formatted["_ws_ts"] = ts
                results.append(formatted)
    return results or None
