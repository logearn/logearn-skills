### B.4 ✅ Skills 开放 6大实时数据API 服务

1、 tokenStream 实时行情 
2、 signalStream  实时信号
3、 实时关注信号 
4、实时 Kline
5、实时交易明细

所有实时数据统一按（积分计费）

**端点**：`ws://${LOGEARN_API_BASE:-https://api.logearn.com/logearn}/ws-skill?apiKey=<your_api_key>`

**鉴权**：连接时通过 query 参数 `apiKey` 鉴权，服务端验证 API Key 有效性并检查积分余额 ≥ 1，否则拒绝连接。

**计费规则**：

| 规则 | 说明 |
|------|------|
| 计费单位 | **每累计推送 100KB 扣 1 积分** |
| 订阅检查 | 连接时 & 每次请求时检查积分余额，不足则推 `POINTS_EXHAUSTED` 并关闭 |
| 扣费时机 | 推送数据累计满 100KB 时实时扣除，不等请求结束 |
| 断开尾数 | 不足 100KB 的尾数不扣（对用户友好） |

**支持的 action**：

| topic | 说明 | 必填参数 |
|--------|------|----------|
| `{"type": "subscribe", "topic": "/token_stream_v2:56"}` | 订阅 BSC 实时行情 | 无 |
| `{"type": "subscribe", "topic": "/token_stream_v2:3"}` | 订阅 SOL 实时行情 | 无 |
| `{"type": "unsubscribe", "topic": "/token_stream_v2:56"}` | 取消订阅 BSC 实时行情 | 无 |
| `{"type": "unsubscribe", "topic": "/token_stream_v2:3"}` | 取消订阅 SOL 实时行情 | 无 |

| `{"type": "subscribe", "topic": "/notification_stream"}` | 订阅全部信号通知(早起精选信号、苏醒信号、回调反弹信号、蓝筹共振信号) | 无 |
| `{"type": "unsubscribe", "topic": "/notification_stream"}` | 取消全部信号订阅 | 无 |

| `{"type": "subscribe", "topic": "/notification_stream/${uid}"}` | 订阅我关注的地址的实时交易明细通知 | uid 从官网获取 |
| `{"type": "unsubscribe", "topic": "/notification_stream/${uid}"}` | 取消订阅我关注的地址的实时交易明细通知 | uid 从官网获取 |

| `{"type": "subscribe", "topic": "/kline_v2:${chainID}:${token_address}:${resolution}"}` | 订阅K线 | chainID取值[ SOL:3, BSC: 56], resolution 取值见下面的配置 |
| `{"type": "unsubscribe", "topic": "/kline_v2:${chainID}:${token_address}:${resolution}"}` | 取消订阅K线 | 同上 |

| `{"type": "subscribe", "topic": "/token:tx:${chainID}:${token_address}"}` | 订阅交易 | chainID取值[ SOL:3, BSC: 56] |
| `{"type": "unsubscribe", "topic": "/token:tx:${chainID}:${token_address}"}` | 取消订阅交易 | 同上 |

| `{"type": "heartbeat"}` | 心跳 | 无 |

K线时间粒度，可选项，resolution
resolutionMap: any = [
  1, // 1秒
  5, // 5秒
  15, // 15秒
  30, // 30秒
  60, // 1分钟
  300, // 5分钟
  900, // 15分钟
  1800, // 30分钟
  3600, // 1小时
  14400, // 4小时
  86400, // 1天
]


**请求示例**：
```json
// 订阅全部信号
{"type": "subscribe", "topic": "/notification_stream"}

// 订阅K线
{"type": "subscribe", "topic": "/kline_v2:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump:60"}

// 订阅交易明细
{"type": "subscribe", "topic": "/token:tx:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"}
```

**推送消息格式**：
```json
// 连接成功
{"data": {"sessionId":"b2c1d63f-5087-dc87-e846-12bf238502d2","remainingPoints":979780},"type":"connected","timestamp":1779307197275}

// tokenStream 推送
{"type": "token", "data": {"token": "Hello", "bytes": 5, "totalBytes": 5}, "timestamp": 1715745600100}

// signalStream 推送
{"type": "signal", "data": {"data": {"symbol": "SOL", "price": 108.5, "signal": "BUY", "confidence": 0.92, "timestamp": 1715745600000}, "bytes": 120, "totalBytes": 1200}, "timestamp": 1715745600500}

// 订阅K线成功
{"data":{"status":"subscribed","message":"Successfully subscribed to /token:tx:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump","topic":"/token:tx:3:Hs78KxVJhxVrk6E5YasrLgj5HqQckEscRdUERnzmpump"},"type":"subscribe","timestamp":1779307200801}

// 错误
{"type": "error", "code": "POINTS_EXHAUSTED", "message": "Points exhausted, stream terminated", "timestamp": 1715745620000}
```

**错误码**：

| code | 含义 |
|------|------|
| `MISSING_API_KEY` | 连接缺少 apiKey 参数 |
| `INVALID_API_KEY` | API Key 无效或过期 |
| `INSUFFICIENT_POINTS` | 积分不足，拒绝连接 |
| `POINTS_EXHAUSTED` | 推送过程中积分耗尽，终止流 |
| `MISSING_PROMPT` | tokenStream 缺少 prompt |
| `MISSING_SYMBOL` | signalStream 缺少 symbol |
| `UNKNOWN_ACTION` | 不支持的 action |

**实现代码**：`SkillWebSocketHandler`，路由 `/ws-skill`（`WebSocketConfig` 注册）。

