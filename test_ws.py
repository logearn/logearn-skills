"""
test_ws.py — LogEarn WebSocket 5 种数据流本地测试

使用方法：
  1. 设置环境变量：export LOGEARN_API_KEY=sk_xxx
  2. 运行：python test_ws.py
  3. 当前只开启 Case 1（token_stream_v2），其余四个已注释。
     挨个取消注释 / 注释来切换测试目标。

依赖：pip install websockets
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.ws.fmt_token_stream        import format_token_stream_msg
from tools.ws.fmt_notification_stream import format_notification_stream_msg
from tools.ws.fmt_follow_stream       import format_follow_stream_msg
from tools.ws.fmt_kline_stream        import format_kline_stream_msg
from tools.ws.fmt_tx_stream           import format_tx_stream_msg

import websockets

API_KEY  = "xxxxxxxx"
BASE     = "wss://dev.logearn.com/logearn"
WS_URI   = f"{BASE}/ws-skill?apiKey={API_KEY}"

MAX_MESSAGES = 10          # 每个 case 收到多少条后自动退出，方便快速验证

# ---------------------------------------------------------------------------
# 公共工具
# ---------------------------------------------------------------------------

def _send(ws, payload: dict):
    return ws.send(json.dumps(payload))


def _print(label: str, data):
    print(f"\n[{label}]")
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def _heartbeat(ws, interval: int = 20):
    """后台定时发心跳，防止连接超时。"""
    while True:
        await asyncio.sleep(interval)
        await _send(ws, {"type": "heartbeat"})


async def _listen(ws, handler, label: str, max_msg: int = MAX_MESSAGES):
    """通用收消息循环。handler 返回 list[dict] 或 None。"""
    count = 0
    async for raw in ws:
        msg = json.loads(raw)
        t   = msg.get("type")

        if t == "connected":
            print(f"[connected] sessionId={msg['data']['sessionId']}  "
                  f"remainingPoints={msg['data']['remainingPoints']}")
            continue
        if t in ("subscribe", "unsubscribe"):
            print(f"[{t}] {msg['data'].get('message', '')}")
            continue
        if t == "error":
            print(f"[ERROR] {msg['code']}: {msg['message']}")
            break

        # DEBUG: print raw msg structure (remove after confirming format)
        print(f"\n[RAW] type={msg.get('type')} bytes={msg.get('bytes')} "
              f"data_type={type(msg.get('data')).__name__} "
              f"data_preview={str(msg.get('data'))[:300]}")

        result = handler(msg)
        if result is None:
            # 未识别的 type，打印原始消息供调试
            _print(f"{label}/raw", msg)
            count += 1
        else:
            # handler 可能返回 list[dict] 或单个 dict
            items = result if isinstance(result, list) else [result]
            print(f"\n[{label}] bytes={msg.get('bytes', '?')}  items={len(items)}")
            for i, item in enumerate(items):
                _print(f"{label}[{i}]", item)
            count += len(items)

        if count >= max_msg:
            print(f"\n[{label}] 已收到 ≥{max_msg} 条，自动退出。")
            break


# ===========================================================================
# Case 1 ✅ 实时代币行情  /token_stream_v2
# ===========================================================================
async def test_token_stream():
    """
    订阅 Solana 实时代币行情。
    格式化器：fmt_token_stream.py → format_token()
    """
    print("=" * 60)
    print("Case 1: /token_stream_v2:3  (Solana 实时代币行情)")
    print("=" * 60)
    async with websockets.connect(WS_URI) as ws:
        asyncio.ensure_future(_heartbeat(ws))
        await _send(ws, {"type": "subscribe", "topic": "/token_stream_v2:3"})
        await _listen(ws, format_token_stream_msg, "token_stream")


# ===========================================================================
# Case 2  ✅ 全量 AI 信号  /notification_stream
# ===========================================================================
async def test_notification_stream():
    """
    订阅全量 AI 信号推送（早期精选、回撤反弹、苏醒、蓝筹共振）。
    格式化器：fmt_notification_stream.py → format_signal()
    """
    print("=" * 60)
    print("Case 2: /notification_stream  (全量 AI 信号)")
    print("=" * 60)
    async with websockets.connect(WS_URI) as ws:
        asyncio.ensure_future(_heartbeat(ws))
        await _send(ws, {"type": "subscribe", "topic": "/notification_stream"})
        await _listen(ws, format_notification_stream_msg, "notification")


# ===========================================================================
# Case 3   关注地址实时交易  /notification_stream/${uid}
# ===========================================================================
FOLLOW_UID = "xxxxx"    # 登录 https://logearn.com 获取你的 uid

async def test_follow_stream():
    """
    订阅我关注的聪明钱地址实时交易明细。
    格式化器：fmt_follow_stream.py（当前直传，下版本完善）
    """
    print("=" * 60)
    print(f"Case 3: /notification_stream/{FOLLOW_UID}  (关注地址交易)")
    print("=" * 60)
    async with websockets.connect(WS_URI) as ws:
        asyncio.ensure_future(_heartbeat(ws))
        await _send(ws, {"type": "subscribe", "topic": f"/notification_stream/{FOLLOW_UID}"})
        await _listen(ws, format_follow_stream_msg, "follow_stream")


# ===========================================================================
# Case 4   实时 K 线  /kline_v2
# ===========================================================================
KLINE_CHAIN      = 3
KLINE_TOKEN      = "Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"
KLINE_RESOLUTION = 60   # 1 分钟；可选值见 ws_api.md

async def test_kline_stream():
    """
    订阅指定代币实时 K 线。
    格式化器：fmt_kline_stream.py（当前直传，下版本完善）
    """
    topic = f"/kline_v2:{KLINE_CHAIN}:{KLINE_TOKEN}:{KLINE_RESOLUTION}"
    print("=" * 60)
    print(f"Case 4: {topic}  (实时 K 线)")
    print("=" * 60)
    async with websockets.connect(WS_URI) as ws:
        asyncio.ensure_future(_heartbeat(ws))
        await _send(ws, {"type": "subscribe", "topic": topic})
        await _listen(ws, format_kline_stream_msg, "kline_stream")


# ===========================================================================
# Case 5   实时交易明细  /token:tx
# ===========================================================================
TX_CHAIN = 3
TX_TOKEN = "Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"

async def test_tx_stream():
    """
    订阅指定代币实时链上买卖交易。
    格式化器：fmt_tx_stream.py（当前直传，下版本完善）
    """
    topic = f"/token:tx:{TX_CHAIN}:{TX_TOKEN}"
    print("=" * 60)
    print(f"Case 5: {topic}  (实时交易明细)")
    print("=" * 60)
    async with websockets.connect(WS_URI) as ws:
        asyncio.ensure_future(_heartbeat(ws))
        await _send(ws, {"type": "subscribe", "topic": topic})
        await _listen(ws, format_tx_stream_msg, "tx_stream")


# ===========================================================================
# 入口 — 取消注释你想运行的 case
# ===========================================================================
async def main():
    if not API_KEY:
        print("[ERROR] 请先设置环境变量：export LOGEARN_API_KEY=sk_xxx")
        return

    # await test_token_stream()          # Case 1  ✅ 当前运行
    # await test_notification_stream() # Case 2  ✅
    await test_follow_stream()       # Case 3  （需填 FOLLOW_UID）
    # await test_kline_stream()        # Case 4  （需填 KLINE_TOKEN）
    # await test_tx_stream()           # Case 5  （需填 TX_TOKEN）


if __name__ == "__main__":
    asyncio.run(main())
