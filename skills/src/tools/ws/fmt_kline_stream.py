"""
WebSocket formatter: /kline_v2:${chainID}:${token_address}:${resolution}

Received message format:
    {
      "type": "data",
      "bytes": <int>,
      "data": {
        "<timestamp_ms>": [<kline_bar_obj>, <kline_bar_obj>, ...]
      }
    }

TODO: Full formatting (OHLCV normalization, USD conversion, volume annotation)
      will be implemented in the next release.
      Current implementation is a pass-through stub.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.fmt_token_info import recursive_json_parse
from typing import List, Optional


def format_kline_stream_msg(
    msg: dict,
    native_prices: Optional[dict] = None,  # reserved for next version
) -> Optional[List[dict]]:
    # msg: => {'type': 'data', 'bytes': <int>, 'data': {'<ts>': [kline_bar_obj, ...], ...}}
    # TODO: replace pass-through with full formatting in next version
    if msg.get("type") != "data":
        return None

    results = []
    for ts, items in (msg.get("data") or {}).items():
        for raw in (items or []):
            item = recursive_json_parse(raw)
            if not isinstance(item, dict):
                continue
            item["_ws_ts"] = ts
            results.append(item)
    return results or None
