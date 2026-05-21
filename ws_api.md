# LogEarn WebSocket 实时数据 API

> HTTP REST 接口请参阅 [api.md](./api.md)

LogEarn WebSocket API 提供 5 种实时数据流，无需轮询即可获取最新行情、AI 信号、K 线及链上交易数据。

## 连接端点

```
wss://logearn.com/logearn/ws-skill?apiKey=<your_api_key>
```

| 字段 | 说明 |
|------|------|
| 协议 | `ws://` / `wss://` |
| 地址 | `${LOGEARN_API_BASE:-wss://logearn.com/logearn}/ws-skill` |
| 鉴权 | Query 参数 `apiKey=<your_api_key>` |

连接建立后，服务端立即推送 `connected` 消息：

```json
{
  "type": "connected",
  "data": {
    "sessionId": "b2c1d63f-5087-dc87-e846-12bf238502d2",
    "remainingPoints": 979780
  },
  "timestamp": 1779307197275
}
```

---

## 计费规则

| 规则 | 说明 |
|------|------|
| 计费单位 | **每累计推送 100 KB 扣 1 积分** |
| 连接时检查 | 连接时检查积分余额 ≥ 1，否则拒绝连接 |
| 实时扣费 | 累计满 100 KB 时实时扣除，不等连接结束 |
| 断开尾数 | 不足 100 KB 的尾数不扣（对用户友好） |

---

## 通用消息格式

所有消息均为 JSON，顶层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `string` | 消息类型（见下表） |
| `data` | `object` | 消息体（因 type 不同而异） |
| `timestamp` | `integer` | 服务端时间戳（毫秒） |

| type 值 | 含义 |
|---------|------|
| `connected` | 连接成功 |
| `subscribe` | 订阅操作响应 |
| `data` | 所有数据推送（代币行情、AI 信号、K 线、交易明细均用此类型） |
| `error` | 错误 |

---

## 心跳

建议每 **30 秒**发送一次，防止连接超时：

```json
{"type": "heartbeat"}
```

---

## 订阅 / 取消订阅

```json
{"type": "subscribe",   "topic": "<topic>"}
{"type": "unsubscribe", "topic": "<topic>"}
```

订阅成功响应：

```json
{
  "type": "subscribe",
  "data": {
    "status": "subscribed",
    "message": "Successfully subscribed to /token:tx:3:Hs78...",
    "topic": "/token:tx:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"
  },
  "timestamp": 1779307200801
}
```

---

## 可订阅 Topic 一览

| Topic | 说明 | 格式化文件 |
|-------|------|-----------|
| `/token_stream_v2:3` | Solana 实时代币行情 | `fmt_token_stream.py` |
| `/token_stream_v2:56` | BSC 实时代币行情 | `fmt_token_stream.py` |
| `/notification_stream` | 全量 AI 信号推送（早期精选、回撤反弹、苏醒、蓝筹共振） | `fmt_notification_stream.py` |
| `/notification_stream/${uid}` | 我关注的地址实时交易明细 | `fmt_follow_stream.py` |
| `/kline_v2:${chainID}:${token_address}:${resolution}` | 指定代币实时 K 线 | `fmt_kline_stream.py` |
| `/token:tx:${chainID}:${token_address}` | 指定代币实时交易 | `fmt_tx_stream.py` |

> `uid`：登录 https://logearn.com 从个人设置页面获取。
> `chainID`：Solana=`3`，BSC=`56`。

---

## K 线时间粒度（resolution）

```
1       1 秒
5       5 秒
15      15 秒
30      30 秒
60      1 分钟
300     5 分钟
900     15 分钟
1800    30 分钟
3600    1 小时
14400   4 小时
86400   1 天
```

---

## 数据流详情

### 1. 实时代币行情 `/token_stream_v2`

订阅 Solana 或 BSC 链上代币的实时行情更新。格式化后结构与 `get_token_info` 返回一致。

**订阅示例**：

```json
{"type": "subscribe", "topic": "/token_stream_v2:3"}
{"type": "subscribe", "topic": "/token_stream_v2:56"}
```

**推送消息**（实际格式）：

```json
{
  "type": "data",
  "bytes": 399717,
  "data": {
    "data": {
      "<timestamp_ms>": [
        { "1": "<token_address>", "2": "<symbol>", "mp": { "mp_1": "<pool>", ... }, ... },
        ...
      ]
    }
  }
}
```

> ⚠️ Token 对象字段经过压缩（如 `"1"` → `token_address`，`"mp"` → `main_pool`），**必须先经 `decompress_token()` 解压**再传给 `format_token()`。完整 key 映射见 `src/tools/ws/fmt_token_stream.py`。

**格式化**：`src/tools/ws/fmt_token_stream.py` — `decompress_token()` → `format_token()`

---

### 2. 全量 AI 信号推送 `/notification_stream`

所有新产生的 AI 信号（早期精选、回撤反弹、休眠苏醒、蓝筹共振）实时推送。格式化后结构与 `get_all_signal` 单条一致。

**订阅示例**：

```json
{"type": "subscribe", "topic": "/notification_stream"}
```

**推送消息**（实际格式）：

```json
{
  "type": "data",
  "bytes": 1234,
  "data": {
    "data": "{\"type\":\"s15\",\"detail\":\"{...token+signal JSON string...}\"}"
  }
}
```

> `data.data` 是 JSON 字符串，需要两次解析：
> 1. `JSON.parse(data.data)` → `{ type, detail, ... }`
> 2. `JSON.parse(detail)` → 实际 token+signal 对象
>
> 内层 `type` 取值及对应信号类型：
>
> | `type` | 信号类型 |
> |--------|----------|
> | `follow` / `public` | `followed`（关注地址交易） |
> | `whale` | `whale`（蓝筹共振） |
> | `kline_pattern` | `v_breakout_volume`（回撤反弹） |
> | `s300` | `breakout_volume_10x`（休眠苏醒） |
> | `s15` | `continue_breakout_volume`（早期精选） |

**格式化**：`src/tools/ws/fmt_notification_stream.py` — 自动处理双层解析与字段重映射，复用 `format_signal()`

---

### 3. 关注地址实时交易明细 `/notification_stream/${uid}`

订阅我在 LogEarn 平台关注的聪明钱地址的实时链上交易。需先登录 https://logearn.com 获取个人 `uid`。

**订阅示例**：

```json
{"type": "subscribe", "topic": "/notification_stream/12345"}
```

**推送消息**（格式待验收，与 `/notification_stream` 结构相同）：

```json
{
  "type": "data",
  "bytes": 1234,
  "data": {
    "data": "{\"type\":\"follow\",\"detail\":\"{...follow tx JSON string...}\"}"
  }
}
```

**格式化**：`src/tools/ws/fmt_follow_stream.py`（下一版本完善，当前为直传）

---

### 4. 实时 K 线 `/kline_v2`

订阅指定代币指定周期的实时 K 线更新。

**订阅示例**：

```json
{"type": "subscribe", "topic": "/kline_v2:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump:60"}
```

**推送消息**：

```json
{
  "type": "kline",
  "data": { "<K 线 bar 对象，结构与 get_kline_list 单条一致>" },
  "timestamp": 1715745600700
}
```

**格式化**：`src/tools/ws/fmt_kline_stream.py`（下一版本完善，当前为直传）

---

### 5. 实时交易明细 `/token:tx`

订阅指定代币的实时链上买卖交易。

**订阅示例**：

```json
{"type": "subscribe", "topic": "/token:tx:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"}
```

**推送消息**：

```json
{
  "type": "tx",
  "data": { "<链上交易对象，结构与 get_trade_logs 单条一致>" },
  "timestamp": 1715745600800
}
```

**格式化**：`src/tools/ws/fmt_tx_stream.py`（下一版本完善，当前为直传）

---

## 数据格式化

原始推送数据需格式化后才易于阅读。LogEarn 在 `src/tools/ws/` 目录提供了各流的格式化器：

| 文件 | 适用 Topic | 复用逻辑 |
|------|-----------|---------|
| `fmt_token_stream.py` | `/token_stream_v2:*` | `fmt_token_info.format_token()` |
| `fmt_notification_stream.py` | `/notification_stream` | `fmt_signal_info.format_signal()` |
| `fmt_follow_stream.py` | `/notification_stream/${uid}` | 下一版本完善 |
| `fmt_kline_stream.py` | `/kline_v2:*` | 下一版本完善 |
| `fmt_tx_stream.py` | `/token:tx:*` | 下一版本完善 |

格式化器以 **Python** 编写，可借助 AI 翻译为 TypeScript / Go / Rust 等版本。

**Python 使用示例**：

```python
import json
from tools.ws.fmt_token_stream import format_token_stream_msg
from tools.ws.fmt_notification_stream import format_notification_stream_msg

# 收到 WS 消息后（所有数据推送 type 均为 "data"，通过订阅的 topic 区分流）
msg = json.loads(raw_message)
if msg.get("type") == "data":
    # 根据当前订阅的 topic 选择对应格式化器
    formatted_token  = format_token_stream_msg(msg)          # token_stream_v2
    formatted_signal = format_notification_stream_msg(msg)   # notification_stream

print(json.dumps(formatted_token or formatted_signal, ensure_ascii=False, indent=2))
```

---

## 错误码

| code | 含义 |
|------|------|
| `MISSING_API_KEY` | 连接缺少 `apiKey` 参数 |
| `INVALID_API_KEY` | API Key 无效或过期 |
| `INSUFFICIENT_POINTS` | 积分不足，拒绝连接 |
| `POINTS_EXHAUSTED` | 推送过程中积分耗尽，终止流 |
| `UNKNOWN_ACTION` | 不支持的 action 类型 |

错误消息格式：

```json
{
  "type": "error",
  "code": "POINTS_EXHAUSTED",
  "message": "Points exhausted, stream terminated",
  "timestamp": 1715745620000
}
```

---

## 完整示例

```python
import asyncio
import json
import websockets
from tools.ws.fmt_token_stream import format_token_stream_msg
from tools.ws.fmt_notification_stream import format_notification_stream_msg


async def main():
    uri = "wss://logearn.com/logearn/ws-skill?apiKey=sk_YOUR_KEY"
    async with websockets.connect(uri) as ws:
        # 订阅 Solana 实时行情 + 全量信号
        await ws.send(json.dumps({"type": "subscribe", "topic": "/token_stream_v2:3"}))
        await ws.send(json.dumps({"type": "subscribe", "topic": "/notification_stream"}))

        async for raw in ws:
            msg = json.loads(raw)
            t = msg.get("type")

            if t == "data":
                # 根据订阅的 topic 选对应格式化器
                print(json.dumps(format_token_stream_msg(msg), ensure_ascii=False, indent=2))
                # 或：print(json.dumps(format_notification_stream_msg(msg), ensure_ascii=False, indent=2))
            elif t == "error":
                print(f"[ERROR] {msg['code']}: {msg['message']}")
                break


asyncio.run(main())
```

> 依赖：`pip install websockets`

---

## 完整 Demo

项目根目录的 **[test_ws.py](./test_ws.py)** 包含全部 5 种数据流的完整使用案例，每种数据流均有独立的测试函数，注释掉其他四个逐一验证即可直接运行：

```bash
# 设置 API Key 后直接运行
export LOGEARN_API_KEY="sk_xxxxxxxx"
/usr/bin/python3 test_ws.py
```

各数据流对应的格式化工具位于 `src/tools/ws/` 目录，可直接将 Python 代码用 AI 翻译为 TypeScript / Go / Rust 等版本。
