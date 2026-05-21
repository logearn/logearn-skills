"""
WebSocket formatter: /notification_stream

Received message format:
    {
      "type": "data",
      "bytes": <int>,
      "data": {
        "data": "{JSON string}"   // parse → { type, detail, bytes, ... }
                                  // detail is another JSON string → token+signal obj
      }
    }

WS type field mapping (mirrors JS realTimeTypeMap):
    'follow'        → 'followed'                (notification_list)
    'public'        → 'followed'                (notification_list)
    'whale'         → 'whale'                   (whale_list)
    'kline_pattern' → 'v_breakout_volume'       (kline_list)
    's300'          → 'breakout_volume_10x'     (s300_list)
    's15'           → 'continue_breakout_volume'(s15_list)

The WS always delivers the notification item in notification_list regardless of type.
We remap it to the field name that format_signal() expects before calling it.

Translatable to TypeScript / Go / Rust — see ws_api.md for details.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.fmt_signal_info import format_signal
from tools.fmt_token_info import recursive_json_parse
from typing import Optional

# WS type → (signals_type, target_field_for_format_signal)
_WS_TYPE_MAP = {
    'follow':        ('followed',                 'notification_list'),
    'public':        ('followed',                 'notification_list'),
    'whale':         ('whale',                    'whale_list'),
    'kline_pattern': ('v_breakout_volume',        'kline_list'),
    's300':          ('breakout_volume_10x',      's300_list'),
    's15':           ('continue_breakout_volume', 's15_list'),
}


def format_notification_stream_msg(
    msg: dict,
    native_prices: Optional[dict] = None,
) -> Optional[dict]:
    """
    Parse and format a /notification_stream real-time push message.

    WS message data.data is a JSON string:
        { "type": "s15"/"s300"/"follow"/..., "detail": "{...token+signal obj...}" }

    Returns a formatted signal dict (same shape as format_signal output), or None.
    """
    if msg.get("type") != "data":
        return None

    # msg["data"]["data"] may be a JSON string or already a dict
    inner = recursive_json_parse((msg.get("data") or {}).get("data"))
    if not isinstance(inner, dict):
        return None

    ws_type = inner.get("type", "")
    mapping = _WS_TYPE_MAP.get(ws_type)
    if not mapping:
        return None

    signals_type, target_field = mapping

    # detail is a JSON string of the token+signal object
    token_signals = recursive_json_parse(inner.get("detail"))
    if not isinstance(token_signals, dict):
        return None

    # WS always puts the notification item in notification_list.
    # If this signal type needs a different field, remap it so format_signal finds it.
    if target_field != "notification_list" and token_signals.get("notification_list"):
        token_signals[target_field] = token_signals.pop("notification_list")

    formatted = format_signal(token_signals, native_prices)
    if formatted is not None:
        formatted["_ws_signal_type"] = signals_type
    return formatted
