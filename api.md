# LogEarn Open API

通过 LogEarn Open API 可以访问 LogEarn 任何专业的分析数据，以及信号。同时使用 LogEarn Open API 可以享受全网最低低至 0.1% 的优惠费率。

## 前置条件

使用前请设置以下环境变量：
- `LOGEARN_API_KEY`（必填）— 您的 LogEarn Open API Key（格式：`sk_xxxxxxxx`），登录 https://logearn.com 官网 获取。
- `LOGEARN_API_BASE`（可选）— API 基础地址，默认为 `https://logearn.com/logearn`

## 鉴权方式

根据接口类型使用以下鉴权方式：

| 模式 | 适用接口 | 方式 |
|------|-----------|-----|
| API Key | 所有 `/call/*`、`/quota`、`/stats`、`/keys`（GET/DELETE） | 请求头 `X-Api-Key: sk_xxx` |

## 计费说明

- 大部分 API 不消耗 Credits，只有频率限制；部分高耗资源的 API 会有 Credits 调用限制，具体消耗情况参考下面表格
- **限速**：每个 API Key 独立限速，默认上限 **600 credits/min**, 若需要调高，联系客服 [@chickenbro_logearn](href="https://t.me/chickenbro_logearn)
- **充值**：0.5 SOL = 100,000 credits，最低充值 100,000 credits
- 所有 API Keys 共享所有的 Credits

## 链 ID

| 链 | ID |
|-------|----|
| Solana | `3` |
| BSC | `56` |

## API 参考文档

>
> 完整接口列表：
> - `POST /open/api/v1/call/{skillCode}` — 调用技能
> - `GET  /open/api/v1/quota` — 查询配额余额

---

#### 技能列表（skillCode 枚举）

| skillCode | 名称 | 消耗            | 必填参数 |
|-----------|------|---------------|---------|
| `get_all_signal` | 查询根据【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】信号形成的信号榜单 | **5 credits** | — |
| `get_hot_list` | 查询五分钟/1小时热门代币榜单 | 3 credit      | — |
| `get_token_signal` | 查询某一个Token 所有历史信号，包括【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】 | 2 credit      | `index_token_address`,`chain` |
| `get_kline_list` | 查询K线数据| 1 credit      | `base`,`chain` |
| `get_token_info` | 查询 Token 详情，包括8大实时持仓指标 | 1 credit      | `params.base`, `chain` |
| `get_coin_balance` | 查询账号 Coin余额 | **免费**（1次/s）| `address` |
| `get_wallet_positions` | 查询仓位 | **免费**（1次/s）  | `address` |
| `solana_swap` | Solana交易 | **免费**（1次/s）  | `caller`、`eventType`、`action` |
| `bsc_swap` | BSC交易 | **免费**（1次/s）  | `caller`、`eventType`、`action` |
| `limit_order` | 挂限价单 | **免费**（1次/s）  | `caller`、`tokenAddress`、`action` |
| `get_limit_orders` | 查询限价单 | **免费**（1次/s）  | `address` |
| `get_trade_logs` | 交易明细 | **免费**（1次/s）  | `address` |

---

### POST /open/api/v1/call/{skillCode}

技能调用核心接口。每次调用消耗 对应的 **credit**，受 API Key 的 `credits_per_minute` 限速约束。

**鉴权**: 请求头 `X-Api-Key: sk_xxx`

**Path 参数**:

| 参数 | 说明 |
|------|------|
| `skillCode` | 技能标识，取值见下方技能列表 |

**通用响应结构**:

```json
{
  "code": 200,
  "msg": "success",
  "data": { }
}
```

**调用失败响应**:

```json
{
  "code": 500,
  "msg": "Credits per minute exceeded: 600 credits/min",
  "data": null
}
```


#### Skill: `get_all_signal` — 查询根据【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】信号形成的信号榜单

LogEarn 独家核心高质量信号榜单。按照 Token 聚合后，返回每个 Token 24 小时范围内的，所有【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】信号，根据返回的结果，可以对 List 进行各种筛选排序，以便在早期就能筛选出潜力的大金额。涵盖 Solana 和 BSC。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `chain` | `string[]` | 否 | `["3","56"]` | 链 ID 列表（3=Solana，56=BSC） |

**请求示例**:

```bash
# 默认参数（Solana + BSC 全链信号）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_all_signal" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**响应结构**:

`data` 以链 ID 为 key 分组，每条为一个 [包含信号数据的 Token 对象](#token-信号对象-signal-token)。


```json
[ 
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },  
]
```

---

#### Skill: `get_hot_list` — 查询五分钟/1小时热门代币榜单 

LogEarn 根据多纬度算法，准确的计算了，当前市场最有热度的代币。形成了榜单。方便查询。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明                                         |
|------|------|------|--------|--------------------------------------------|
| `chain` | `string[]` | 否 | `["3","56"]` | 链 ID 列表                                    |
| `tokenGroupId` | `string` | 否 | `12` | 热门分组ID, 最近5分钟：12，最近1小时：13 |

**请求示例**:

```bash
# 指定分组
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_hot_list" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"chain":["3","56"],"tokenGroupId":12}'
```

**响应结构**:

```json
[ 
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },  
]
```

---

#### Skill: `get_token_info` — 查询 Token 详情，包括8大实时持仓指标 

除了查询 Token 的一些基本信息以外，查询结果包含，8大实时持仓指标。他们分别是：

| `smart_volume` | `float` | 聪明钱地址持仓占比 |
| `whale_volume` | `float` | 巨鲸地址持仓占比 |
| `new_volume` | `float` | 新地址持仓占比 |
| `old_volume` | `float` | 老地址持仓占比 |
| `frequent_volume` | `float` | 高频交易地址持仓占比 |
| `amm_volume` | `float` | AMM / 做市商地址持仓占比 |
| `exchange_volume` | `float` | 交易所地址持仓占比 |
| `scam_volume` | `float` | 诈骗地址持仓占比 |
| `shit_volume` | `float` | 垃圾地址持仓占比 |


**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `chain` | `integer[]` |  **必填** |- | Solana: 3, BSC: 56 |
| `params.base` | `string` | **必填** | — | Token 合约地址 |

**请求示例**:

```bash
# 查询 Solana Token 详情
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_token_info" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"chain":[3],"params":{"base":"DSSXu6XbYDgWnjMVzagcVF9QpVWXY2H9iexAc4mpump"}}'
```

**响应结构**:

```json
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },  
```

---

#### Skill: `get_token_signal` — 查询某一个Token 所有历史信号，包括【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】

其他接口默认情况下返回的都是 24小时范围的信号，但是本接口就是查询所有的 Token 历史信号。方便我们做历史回测。比如过去一个月内，有4次以上的苏醒 Token 是不是真苏醒，此时，就可以使用历史数据去回溯了。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `index_token_address` | `string` | **必填** | — | Token 合约地址 |
| `chain` | `string` | **必填**  | -- | 链 ID：`"3"`=Solana，`"56"`=BSC |


**请求示例**:

```bash
# 查询某 Token 的所有历史 AI 信号, 指定链（（SOLANA）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_token_signal" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"index_token_address":"FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump","chain":"3"}'
```

**响应结构**:

```json
  { "...包含信号数据的 Token 对象, 见文末数据对象说明" },  
```

---

#### Skill: `get_kline_list` — K线数据

获取 Token K线（蜡烛图）数据，支持多周期。`base` 为必填。如果要翻页，使用 作为 endTime 游标向钱翻页即可

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `chain` | `string` |  **必填** | — | 链 ID（字符串） |
| `base` | `string` | **必填** | — | Token 合约地址 |
| `intervalTime` | `integer` | 否 | `900` | K线周期（秒）：60/300/900/3600/86400 |
| `endTime` | `long` | 否 | 当前时间戳 | 结束时间（Unix 秒） |
| `pageSize` | `integer` | 否 | `96` | 返回条数（建议不超过 200） |

**intervalTime 常用取值**:

| 值 | 周期 |
|----|------|
| `60` | 1分钟 |
| `300` | 5分钟 |
| `900` | 15分钟 |
| `3600` | 1小时 |
| `86400` | 1天 |

**请求示例**:

```bash
# 最近96根15分钟K线（默认）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_kline_list" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"base":"7c5gm5fqvQuyteJ9G4pFaubqRVHuegsFXtfHJXBBpump", "chain": "3"}'

# 自定义周期和时间范围
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_kline_list" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"chain":"3","base":"7c5gm5fqvQuyteJ9G4pFaubqRVHuegsFXtfHJXBBpump","intervalTime":900,"endTime":1775883812,"pageSize":96}'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "body": [
      {
        "time": 1775883000,
        "open": "0.001234",
        "openU": "0.001234",
        "high": "0.001300",
        "highU": "0.001300",
        "low": "0.001200",
        "lowU": "0.001200",
        "close": "0.001280",
        "closeU": "0.001280",
        "volume": "98765",
        "volumeU": "98765"
      }
    ]
  }
}
```
带 **U** 结尾，表示以当时的U计价的价格，否则表示的时候以对应链的 Native Token 计价的价格。



---

#### Skill: `get_coin_balance` — 账号Coin余额

查询当前登录账户在 Solana 或 BSC 链上对应的的原生币余额（SOL / BNB）。直接读取链上 RPC，实时返回。默认返回所有链上面的所有地址余额，如果指定了 address 和 chain，则只返回指定地址的余额。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `address` | `string` | 否 | — | 钱包地址（Solana Base58 或 EVM 0x...） |
| `chain` | `integer` | 否 | — | 链 ID：3=Solana，56=BSC |

**请求示例**:

```bash
# Solana 账号 SOL 余额
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_coin_balance" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY"}'

# BSC 账号 BNB 余额
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_coin_balance" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"0xed2eebf5929f9230a48dfbae0ca085e7a1425e6f","chain":56}'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "address": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
    "chain": 3,
    "symbol": "SOL",
    "balance": "1.234567890",
    "balanceRaw": "1234567890"
  }
}
```

> `balance` 为人类可读格式（SOL/BNB 单位）；`balanceRaw` 为原始单位（lamports / wei）。


---

#### Skill: `get_wallet_positions` — 仓位查询

查询指定钱包地址当前持仓的 Token 列表，支持多地址、分页、排序。`address` 为必填。默认返回所有钱包的仓位情况，如果指定了 address 和 chain，则只返回指定地址的仓位情况。
**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `address` | `string` | 否 | — | 包地址，多地址用英文逗号分隔（支持 Solana / EVM 混合） |
| `chain` | `integer` | 否 | — | 链 ID：3=Solana，56=BSC |
| `page_size` | `integer` | 否 | `20` | 每页条数 |
| `page_num` | `integer` | 否 | `0` | 页码（从 0 开始） |
| `sort_field` | `string` | 否 | `open_position_time` | 排序字段（`open_position_time` / `value_usd` 等） |
| `sort_direction` | `string` | 否 | `desc` | 排序方向：`asc` / `desc` |
| `hold_amount` | `string` | 否 | `"1"` | 最低持仓数量过滤 |
| `wcoin_scale` | `integer` | 否 | `9` | 小数位精度 |

**请求示例**:

```bash
# 查询单地址持仓（默认参数）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_wallet_positions" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY"}'

# 多链多地址 + 分页
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_wallet_positions" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY,0xed2eebf5929f9230a48dfbae0ca085e7a1425e6f",
    "page_size": 20,
    "page_num": 0,
    "sort_field": "open_position_time",
    "sort_direction": "desc",
    "hold_amount": "1"
  }'
```

**响应结构**:

```json
[
  {
    "avg_price": 6.386222241764064,
    "chain": 3,
    "copied_address": "0x0",
    "copyer_address": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
    "created_time": "2026-04-12 02:55:08",
    "decimals": 9,
    "hold_amount": 0.001842201,
    "hold_cost_coin": 0.011764705,
    "id": 19119140,
    "is_trigger_entrust_stop_profit1": 0,
    "is_trigger_entrust_stop_profit2": 0,
    "is_trigger_entrust_stop_profit3": 0,
    "key": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY-0x0-PreLWGkkeqG1s4HEfFZSy9moCrJ7btsHuUtfcCeoRua-3-1775933706",
    "last_order_time": "1775933706",
    "last_price": 6.771265886540085,
    "last_swap_type": "buy",
    "max_price": 6.846866140340169,
    "open_position_time": 1775933706,
    "position_user_updated": 1,
    "quote_address": null,
    "realized_cost": 0.0,
    "realized_pnl": 0.0,
    "realized_return": 0.0,
    // 条件止盈相关
    "entrust_condition_stop_profit1": 50.0,
    "entrust_condition_stop_profit2": 0.0,
    "entrust_condition_stop_profit3": 0.0,
    "entrust_stop_profit1": 5.0,
    "entrust_stop_profit1_percent": 100.0,
    "entrust_stop_profit2": 0.0,
    "entrust_stop_profit2_percent": 0.0,
    "entrust_stop_profit3": 0.0,
    "entrust_stop_profit3_percent": 0.0,
    // 移动止盈止损
    "withdraw_condition_stop_loss1": 0.0,
    "withdraw_condition_stop_loss2": 0.0,
    "withdraw_condition_stop_loss3": 0.0,
    "withdraw_stop_loss1": 0.0,
    "withdraw_stop_loss1_percent": 0.0,
    "withdraw_stop_loss2": 0.0,
    "withdraw_stop_loss2_percent": 0.0,
    "withdraw_stop_loss3": 0.0,
    "withdraw_stop_loss3_percent": 0.0,
    "withdraw_stop_loss_number": 0,
    // 分批止损    
    "stop_loss1": 0.0,
    "stop_loss1_percent": 0.0,
    "stop_loss2": 0.0,
    "stop_loss2_percent": 0.0,
    "stop_loss3": 0.0,
    "stop_loss3_percent": 0.0,
    "stop_loss_number": 0,
    // 分批止盈  
    "stop_profit1": 100.0,
    "stop_profit1_percent": 50.0,
    "stop_profit2": 0.0,
    "stop_profit2_percent": 0.0,
    "stop_profit3": 0.0,
    "stop_profit3_percent": 0.0,
    "stop_profit4": 0.0,
    "stop_profit4_percent": 0.0,
    "stop_profit5": 0.0,
    "stop_profit5_percent": 0.0,
    "stop_profit_number": 0,
    "symbol": "KALSHI",
    "token_address": "PreLWGkkeqG1s4HEfFZSy9moCrJ7btsHuUtfcCeoRua",
    "total_cost_coin": 0.011764705,
    "total_pnl": 0.0007093277874500314,
    "total_receive_coin": 0.0,
    "total_record": 3,
    "total_return": 0.060292866455217656,
    "total_supply": "1311999515466",
    "total_volume": "1842201",
    "unrelized_pnl": 0.0007093277874500311,
    "unrelized_return_rate": "0.06029286645521762994",
    "updated_time": "2026-04-19 22:36:41",
  }  
]
```

---

#### Skill: `get_limit_orders` — 查询限价单

查询指定钱包地址的限价单列表，支持按状态筛选。默认返回所有钱包的限价单，如果指定了 address 和 chain，则只返回指定地址的限价单。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `address` | `string` | 否 | — | 钱包地址，多地址用英文逗号分隔 |
| `chain` | `integer` | 否 | — | 链 ID：3=Solana，56=BSC |
| `status` | `integer` | 否 | `1` | 订单状态：-1=已取消，0=未执行，1=已执行，2=已过期 |
| `page_size` | `integer` | 否 | `100` | 每页条数 |
| `page_num` | `integer` | 否 | `0` | 页码（从 0 开始） |

**请求示例**:

```bash
# 查询待执行的限价单（默认 status=1）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_limit_orders" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY,0xed2eebf5929f9230a48dfbae0ca085e7a1425e6f"}'

# 查询已取消的订单
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_limit_orders" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY","status":-1,"page_size":50}'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "rows": [
      {
        "id": 12345,
        "caller": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
        "tokenAddress": "FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
        "eventType": 1,
        "limitNumber": 0.00013789,
        "status": 1,
        "expiredAt": 1807445030,
        "chain": 3
      }
    ],
    "total": 3
  }
}
```

---

#### Skill: `get_trade_logs` — 交易明细

查询指定钉包的链上交易流水（买卖记录），支持 Solana 和 BSC 。默认返回所有钱包的交易明细，如果指定了 address 和 chain，则只返回指定地址的交易明细。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `address` | `string` | 否  | — | 钉包地址，多地址用英文逗号分隔（Solana / EVM 可混合） |
| `chain` | `string` | 否 | - | 链 ID：`"3"`=Solana，`"56"`=BSC（`protocol` 由服务端自动推导） |
| `wcoin` | `string` | 否 | chain=3 时自动填 SOL 地址 | 原生币合约地址 |
| `page_size` | `integer` | 否 | `100` | 每页条数 |
| `page_num` | `integer` | 否 | `0` | 页码（从 0 开始） |

**请求示例**:

```bash
# 查询 Solana 钉包交易明细（默认参数）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_trade_logs" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address":"Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY"}'

# 多地址查询（Solana + BSC 钉包交易合并）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_trade_logs" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
    "chain": "3",
    "page_size": 100,
    "page_num": 0
  }'

# 查询 BSC 钉包交易明细（protocol 由 chain 自动推导，无需传入）
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/get_trade_logs" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0xed2eebf5929f9230a48dfbae0ca085e7a1425e6f",
    "chain": "56"
  }'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "rows": [
      {
        "tx_hash": "5x3kL...",
        "caller": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
        "token_address": "xxx...pump",
        "symbol": "TOKEN",
        "event_type": "buy",
        "amount_in": "11904761",
        "amount_out": "98765432",
        "price_usd": "0.00123",
        "created_time": 1775909030,
        "chain": 3
      }
    ],
    "total": 256
  }
}
```

---

#### Skill: `solana_swap` / `bsc_swap` — 链上交易

两个 Skill 逻辑完全相同，**唯一区别是路由协议**：
- `solana_swap`：`protocol=swap`，`chainId=3`，`caller` 为 Solana Base58 地址
- `bsc_swap`：`protocol=pancake`，`chainId=56`，`caller` 为 EVM `0x...` 地址

以上路由字段由服务端自动补充，无需手动传入。

**顶层请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `caller` | `string` | **必填** | 执行交易的钱包地址（Solana Base58 或 EVM 0x...） |
| `eventType` | `string` | **必填** | 交易方向：`"buy"` / `"sell"` |
| `action` | `object` | **必填** | 交易参数对象，见下方 action 字段说明 |

**`action` 基础字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tokenIn` | `string` | **必填** | 输入 Token 地址（买入时为原生币地址，卖出时为 Token 地址） |
| `tokenOut` | `string` | **必填** | 输出 Token 地址（买入时为 Token 地址，卖出时为原生币地址） |
| `amountIn` | `string` | **必填** | 输入数量（未处理精度的原始整数，如 lamports / wei） |
| `timestamp` | `integer` | **必填** | 当前时间戳（毫秒） |
| `key` | `string` | **必填** | 操作方向，与 `eventType` 一致：`"buy"` / `"sell"` |
| `antiMev` | `integer` | 否 | 是否防夹子：`1`=开启，`0`=关闭，默认 `1` |
| `customRpc` | `string` | 否 | 自定义 RPC 地址，留空使用默认 |
| `autoMaxFee` | `float` | 否 | 最大网络费用（SOL/BNB），如 `0.2`，留空不限制 |

**`action` 分批止盈**（可选，不填则不挂止盈）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `stopProfit1` ~ `stopProfit5` | `float` | 第 1~5 档止盈触发涨幅（%），如 `100` 表示涨 100% 时止盈 |
| `stopProfit1Percent` ~ `stopProfit5Percent` | `float` | 对应档位卖出仓位比例（%），如 `50` 表示卖出 50% |

**`action` 分批止损**（可选）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `stopLoss1` ~ `stopLoss3` | `float` | 第 1~3 档止损触发跌幅（%），如 `30` 表示跌 30% 时止损 |
| `stopLoss1Percent` ~ `stopLoss3Percent` | `float` | 对应档位卖出仓位比例（%） |

**`action` 移动止损**（可选）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `withdrawStopLoss1` ~ `withdrawStopLoss3` | `float` | 第 1~3 档移动止损触发跌幅（%，从最高点回撤） |
| `withdrawStopLoss1Percent` ~ `withdrawStopLoss3Percent` | `float` | 对应档位卖出仓位比例（%） |

**`action` 条件止盈**（可选）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `entrustConditionStopProfit1` ~ `entrustConditionStopProfit3` | `float` | 第 1~3 档条件止盈触发涨幅（%） |
| `entrustStopProfit1` ~ `entrustStopProfit3` | `float` | 触发后的止盈目标涨幅（%） |
| `entrustStopProfit1Percent` ~ `entrustStopProfit3Percent` | `float` | 触发后卖出仓位比例（%） |

**请求示例**:

```bash
# Solana 买入
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/solana_swap" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "caller": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
    "eventType": "buy",
    "action": {
      "tokenIn": "So11111111111111111111111111111111111111112",
      "tokenOut": "2AmspLddd5rNmjCaG48UjAMPPKqs5FccnNbmvci8pump",
      "amountIn": "11904761",
      "timestamp": 1775895134134,
      "key": "buy",
      "antiMev": 1,
      "autoMaxFee": 0.2,
      "stopProfit1": 100,
      "stopProfit1Percent": 50,
      "stopLoss1": 30,
      "stopLoss1Percent": 100
    }
  }'

# BSC 卖出
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/bsc_swap" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "caller": "0xed2eebf5929f9230a48dfbae0ca085e7a1425e6f",
    "eventType": "sell",
    "action": {
      "tokenIn": "0x606c308be2dd3ff3da531134da51ccf831e24444",
      "tokenOut": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
      "amountIn": "81309622878565000000000",
      "timestamp": 1775896791257,
      "key": "sell",
      "antiMev": 1
    }
  }'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "code": 200,
    "status": "success",
    "data": {
      "txId": "5x3kL...交易哈希",
      "status": "pending"
    }
  }
}
```

---

#### Skill: `limit_order` — 挂限价单


在 Solana 或 BSC 链上创建限价单，当价格满足 `limitNumber` 条件时自动触发交易。

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `caller` | `string` | **必填** | — | 执行交易的钱包地址 |
| `tokenAddress` | `string` | **必填** | — | 目标 Token 合约地址 |
| `action` | `object` | **必填** | — | 交易参数对象，透传并存储到限价单 |
| `chainId` | `integer` | 否 | `3` | 链 ID：3=Solana，56=BSC（同时决定 `protocol`） |
| `eventType` | `integer` | 否 | `1` | 交易方向：1=买入，2=卖出 |
| `expiredAt` | `long` | 否 | 7天后 | 过期时间（Unix 秒） |

`action` 除包含与 `solana_swap` / `bsc_swap` 相同的基础字段（`tokenIn`、`tokenOut`、`amountIn`、`antiMev` 等）外，还需额外传入以下限价单专有字段。`protocol`（由 `chainId` 推导：3→`swap`，56→`pancake`）和 `status=1` 由服务端自动设置。

**`action` 限价单专有字段**（必填）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `limitNumber` | `float` | 触发条件目标值（币本位价格，已处理精度）|
| `limitType` | `integer` | 参考类型：`1` = 价格触发，`2` = 市值触发 |
| `direction` | `integer` | 触发方向：`1` = 向上触发（买单：等待价格下跌到目标价再买），`2` = 向下触发（卖单：等待价格上涨到目标价再卖） |

> **方向说明**：买单通常等价格跌到目标位（`direction=1`，价格从上方穿越 `limitNumber`）；卖单通常等价格涨到目标位（`direction=2`，价格从下方穿越 `limitNumber`）。若 `percent > 0`（目标价高于当前价）用 `direction=1`，`percent < 0` 用 `direction=2`。

**`action` 止盈止损字段**（可选，与 swap 接口完全相同）:

> 支持所有 `solana_swap` / `bsc_swap` 中的止盈止损参数：分批止盈（`stopProfit1~5`）、分批止损（`stopLoss1~3`）、移动止损（`withdrawStopLoss1~3`）、条件止盈（`entrustConditionStopProfit1~3`）。具体字段见[链上交易 action 止盈止损参数说明](#skill-solana_swap--bsc_swap--链上交易)。

**请求示例**:

```bash
curl -X POST "${LOGEARN_API_BASE:-https://logearn.com/logearn}/open/api/v1/call/limit_order" \
  -H "X-Api-Key: $LOGEARN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "caller": "Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY",
    "tokenAddress": "FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
    "chainId": 3,
    "eventType": 1,
    "expiredAt": 1807445030,
    "action": {
      "tokenIn": "So11111111111111111111111111111111111111112",
      "tokenOut": "FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
      "amountIn": "11904761",
      "timestamp": 1775909030424,
      "key": "buy",
      "antiMev": 1,
      "customRpc": "",
      "autoMaxFee": 0.2,
      "limitNumber": 0.00013788786148931755,
      "limitType": 1,
      "direction": 1,
      "stopProfit1": 100,
      "stopProfit1Percent": 50
    }
  }'
```

**响应结构**:

```json
{
  "code": 200,
  "data": {
    "id": 12345,
    "status": "created"
  }
}
```




---

## 错误码说明

| 错误码 | 含义 |
|------|---------|
| `200` | 成功 |
| `400` / 非 200 | 业务错误，请查看 `msg` 字段 |
| `"Invalid or disabled API Key"` | API Key 无效或已禁用 |
| `"Quota insufficient"` | Credit 不足，请充值 |
| `"Credits per minute exceeded"` | 触发限速，请降低请求频率 |
| `"Unknown skillCode"` | 路径中的 `{skillCode}` 无效 |
| `"get_pool_list requires tokenAddress or poolAddress"` | 缺少必填参数 |

## 快速接入流程

1. 登录 UniEarn 并获取 `logearn_token`
2. 调用 `POST /open/api/v1/keys` 创建 API Key，获得 `sk_xxx`
3. 调用 `POST /open/api/v1/recharge` 充值 Credit（最少 100,000）
4. 将 `sk_xxx` 作为 `X-Api-Key` 请求头调用任意技能
5. 通过 `GET /open/api/v1/quota` 和 `GET /open/api/v1/stats` 监控用量

---

## 数据对象说明

> 以下对象结构被多个 Skill 共用（`get_all_signal` / `get_hot_list` / `get_token_signal`）。

---

### 包含信号数据的 Token 对象（Signal Token）

#### 基础信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `token_address` | `string` | Token 合约地址 |
| `token_name` | `string` | Token 全称 |
| `symbol` | `string` | Token 符号 |
| `chain` | `integer` | 链 ID（3=Solana，56=BSC） |
| `decimals` | `integer` | Token 精度 |
| `total_supply` | `float` | 总供应量（已规范化） |
| `platform` | `string` | 发行平台标识（如 `6EF8rrecthR5...`=Pump.fun，`binance_four.meme`=Four.meme） |
| `platform_name` | `string` | 平台显示名称（如 `Pump`、`Binance Four`） |
| `platform_icon` | `string` | 平台图标相对路径 |
| `main_pool_address` | `string` | 主要流动性池地址 |
| `swap_begin_time` | `float` | 首笔交易时间（Unix 秒） |
| `launch_time` | `integer` | 内盘毕业时间（Unix 秒，空表示未毕业） |
| `launch_time_duration` | `integer` | 内盘毕业距离开盘时间差(秒) |

#### 价格 / 市值

| 字段 | 类型 | 说明 |
|------|------|------|
| `price_now` | `float` | 当前价格（原生币计价） |
| `mcap` | `float` | 当前市值（USD） |
| `current_mcap` | `float` | 同 `mcap`，实时市值 |
| `fdv` | `float` | 完全稀释估值（USD） |
| `pool_liquidity` | `float` | 主池流动性（USD） |
| `price_change_5m` | `float` | 5 分钟涨跌幅（%） |
| `price_change_1h` | `float` | 1 小时涨跌幅（%） |
| `price_change_6h` | `float` | 6 小时涨跌幅（%） |
| `price_change_1d` | `float` | 24 小时涨跌幅（%） |
| `progress` | `float` | 内盘毕业进度（%，如 Pump.fun bonding curve） |

#### 交易量 / 活跃度

| 字段 | 类型 | 说明 |
|------|------|------|
| `buy_tx_count_d1` | `integer` | 24h 买入笔数 |
| `sell_tx_count_d1` | `integer` | 24h 卖出笔数 |
| `buyer_count_d1` | `integer` | 24h 买入地址数 |
| `seller_count_d1` | `integer` | 24h 卖出地址数 |
| `buy_wcoin_amount_d1` | `float` | 24h 买入原生币总量 |
| `sell_wcoin_amount_d1` | `float` | 24h 卖出原生币总量 |
| `buy_wcoin_amount_h1` | `float` | 1h 买入原生币总量 |
| `buy_wcoin_amount_m5` | `float` | 5m 买入原生币总量 |
| `smart_money_address_buy_count_d1` | `integer` | 24h 聪明钱买入地址数 |
| `smart_money_address_sell_count_d1` | `integer` | 24h 聪明钱卖出地址数 |


#### 热门指数

| 字段 | 类型 | 说明 |
|------|------|------|
| `hot` | `string` | 热度标签（空字符串表示无热度） |
| `hot_index` | `integer` | 热度分值（0 = 不热） |
| `m5_featured_index` | `float` | 5 分钟精选评分（负值表示不在精选） |
| `h1_featured_index` | `float` | 1 小时精选评分（负值表示不在精选） |

#### 标签 / 安全

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_fake` | `boolean` | 是否仿盘（`is_fake_pump \|\| is_fake_four \|\| is_fake_bonk`） |
| `is_fake_pump` | `boolean` | 是否仿 Pump.fun 盘 |
| `is_fake_four` | `boolean` | 是否仿 Four.meme 盘 |
| `is_fake_bonk` | `boolean` | 是否仿 Bonk 盘 |
| `is_trench_token` | `boolean` | 是否为 内盘 类型（平台发行早期小市值） |
| `is_meteora` | `boolean` | 是否在 Meteora 平台 |
| `is_scam_token` | `boolean\|null` | 是否为诈骗 Token（null = 未检测） |
| `is_honey` | `boolean\|null` | 是否为貔貅盘（null = 未检测） |
| `is_diamond_token` | `boolean\|null` | 是否为钻石筹码 Token |
| `is_error_market_token` | `boolean\|null` | 是否存在异常市场行为 |
| `creator_address` | `string` | 创建者地址 |
| `creator_tag` | `array` | 创建者标签列表 |
| `total_record` | `integer` | 创建者历史发币数 |

---

### all_signals_list 信号列表, 信号类型说明

以信号类型为 key，每个 key 对应一个信号条目数组。

| Key | 说明 |
|-----|------|
| `whale_list` | 蓝筹共振信号 | 所有蓝筹代币的头部赢家，这些地址在短时间内多人买入某个 Token 时，产生了买入行为共振信号。就会发出蓝筹共振信号 |
| `continue_breakout_volume_list` | 早期精选信号 | 早期精选信号，代币创建后，首次出席资金流入时，会发出早期精选信号，精选时，如果最新的三根K线是连续上涨的，则为加强信号 |
| `breakout_volume_10x_list` | 休眠苏醒信号 | 休眠苏醒信号，当代币休眠一段时间后，突然开始放量活跃，会发出苏醒信号。苏醒时，往往会短时间内发出多次苏醒信号 |
| `v_breakout_volume_list` | 回撤反弹信号 | 回撤反弹信号，当代币价格回调幅度大于20%后，如果开始反弹，反弹20%，40%，60%， 新高，四个时间点，各通知一次 |


#### 所有信号通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `string` | 信号类型：`whale` / `v_breakout_volume` / `continue_breakout_volume` / `breakout_volume_10x` |
| `signalTime` | `float` | 信号触发时间（Unix 秒） |
| `signal_time` | `integer` | 信号对应的 K 线时间（Unix 秒） |
| `token_address` | `string` | Token 合约地址（`whale` 信号也有 `tokenAddress` 字段，内容相同） |
| `symbol` | `string` | Token 符号 |
| `chain` | `integer` | 链 ID（3=Solana，56=BSC） |
| `decimals` | `integer` | Token 精度 |
| `total_supply` | `float` | 总供应量（已规范化） |
| `swap_begin_time` | `float` | 首笔交易时间（Unix 秒） |
| `notice_mcap` | `float` | 信号发出时市值（USD） |
| `max_up_mcap` | `float` | 信号发出后追踪到的最高市值（USD） |
| `low_price_mcap` | `float\|null` | 底部市值（USD），无则为 `null` |
| `top_price_mcap` | `float\|null` | 高点市值（USD），无则为 `null` |

---

#### `v_breakout_volume` — 回撤反弹 专有字段

> 价格从高点回调 ≥20% 后开始反弹，在反弹 20% / 40% / 60% / 新高四个节点各触发一次信号。

| 字段 | 类型 | 说明 |
|------|------|------|
| `top_price` | `float` | 回撤起始高点价格 |
| `top_price_mcap` | `float` | 回撤起始高点市值（USD） |
| `top_price_time` | `integer` | 回撤起始高点时间（Unix 秒） |
| `low_price` | `float` | 回撤底部价格 |
| `low_price_mcap` | `float` | 回撤底部市值（USD） |
| `low_price_time` | `integer` | 回撤底部时间（Unix 秒） |
| `n_pattern_confirmed` | `boolean` | 本次回撤是否有效（回撤幅度 ≥20% 才为 `true`） |
| `n_pattern_retracement` | `float` | 从高点到底部的回撤幅度（小数，如 `0.4723` = 47.23%） |
| `current_breakout_ratio` | `float` | 当前从底部反弹了多少（小数，如 `0.9945` = 99.45%） |
| `price_rise_ratio` | `float` | 当前价格相对底部的涨幅（小数） |
| `fibon_break1` / `fibon_break1_time` | `float` / `integer` | 反弹 20% 时市值（USD）/ 时间（`0` = 未到达） |
| `fibon_break2` / `fibon_break2_time` | `float` / `integer` | 反弹 40% 时市值（USD）/ 时间 |
| `fibon_break3` / `fibon_break3_time` | `float` / `integer` | 反弹 60% 时市值（USD）/ 时间 |
| `fibon_break4` / `fibon_break4_time` | `float` / `integer` | 反弹创新高时市值（USD）/ 时间 |
| `max_price` / `max_price_time` | `float` / `integer` | 信号发出后追踪到的最高价 / 时间 |
| `current_price` / `current_price_time` | `float` / `integer` | 当前价格 / 时间 |

---

#### `breakout_volume_10x` — 休眠苏醒 专有字段

> 代币沉寂一段时间后成交量突然放大（当前量 / 历史均量 倍数显著），发出苏醒信号，短时间内可能连续触发多次。

| 字段 | 类型 | 说明 |
|------|------|------|
| `avg_history_volume` | `float` | 休眠时平均成交量（SOL / BNB） |
| `current_volume` | `float` | 当前 苏醒 K 线成交量 |
| `volume_ratio` | `float` | 当前量苏醒成交量 / 休眠时历史均量倍数（如 `15.8` = 当前量是均量的 15.8 倍） |
| `cv` | `float` | 休眠时价格的波动率（波动程度，值越大历史越不稳定） |
| `standardized_slope` | `float` | 休眠时价格标准化斜率（值越大，说明上升越快） |
| `current_open_price` / `current_close_price` | `float` / `float` | 当前 K 线开盘价 / 收盘价 |
| `current_kline_time` | `integer` | 当前 K 线时间（Unix 秒） |
| `current_bullish` | `boolean` | 当前 K 线是否收阳 |
| `history_kline_count` | `integer` | 参与统计的历史休眠 K 线数量 |
| `history_start_time` / `history_end_time` | `integer` / `integer` | 历史休眠K线数据起止时间（Unix 秒） |
| `max_up_mcap_time` | `float` | 历史最高市值对应时间（Unix 秒） |

---

#### `whale` — 蓝筹共振 专有字段

> 多个蓝筹代币的头部赢家地址在极短时间内同时买入同一 Token，产生行为共振，发出信号。

| 字段 | 类型 | 说明 |
|------|------|------|
| `whaleWalletCount` | `integer` | 触发共振的蓝筹巨鲸钱包数量 |
| `whaleTxCount` | `integer` | 巨鲸交易笔数 |
| `signal_price_v1` | `float` | 信号发出时精确价格 |
| `blockTime` | `string` | 区块时间（格式化字符串，如 `"2026-04-19 07:33:31"`） |
| `pastMinute` | `integer` | 信号触发距当前分钟数 |
| `swap_begin_time_duration` | `string` | 开盘时间文字描述（如 `"21 seconds ago"`） |
| `chainName` | `string` | 链名称（如 `"SOLANA"`） |
| `tokenName` | `string` | Token 名称 |
| `priceNative` | `string` | 原生代币价格（简化表示，如 `"0.0{6}770"`） |
| `priceM5` / `priceH1` / `priceH24` | `string` | 5m/1h/24h 价格变化，无数据时为 `"--"` |
| `volume` | `string` | 成交量（格式化字符串，如 `"9.23M"`） |
| `volumeRatio` | `float` | 成交量占比 |
| `fdv` | `string` | 完全稀释市值（格式化字符串，如 `"66.46K"`） |
| `marketCap` | `string` | 市值（格式化字符串） |
| `liquidity` | `string` | 流动性，无数据时为 `"--"` |

---

#### `continue_breakout_volume` — 早期精选 专有字段

> 代币上线后首次出现大量资金流入时触发，若最新 3 根 K 线全部收阳则升级为**加强信号**（`all_bullish=true`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `signal_price` | `float` | 信号发出时价格 |
| `notice_mcap` | `float` | 信号发出时市值（USD） |
| `all_bullish` | `boolean` | 最新 3 根 K 线是否全部收阳（加强信号标志） |
| `kline1_bullish` / `kline2_bullish` / `kline3_bullish` | `boolean` | 第 1/2/3 根 K 线是否收阳（kline1 最旧，kline3 最新） |
| `kline1_time` / `kline2_time` / `kline3_time` | `integer` | 对应 K 线时间（Unix 秒） |
| `kline1_buy_tx_count` / `kline1_sell_tx_count` | `integer` | 第 1 根 K 线买入/卖出笔数 |
| `kline2_buy_tx_count` / `kline2_sell_tx_count` | `integer` | 第 2 根 K 线买入/卖出笔数 |
| `kline3_buy_tx_count` / `kline3_sell_tx_count` | `integer` | 第 3 根 K 线买入/卖出笔数 |
| `volume1` / `volume2` / `volume3` | `float` | 三根 K 线成交量（SOL / BNB） |
| `max_amplitude` | `float` | 开盘到信号发出时所有K线中最大的振幅（%） |
| `max_amplitude_time` | `integer` | 最大振幅对应 K 线时间（Unix 秒） |

---


#### 当前 Token 在四种信号种最优信号摘要

| 字段 | 类型 | 说明 |
|------|------|------|
| `signal_best_type` | `string` | 最优信号类型（`whale` / `v_breakout_volume` / `continue_breakout_volume` / `breakout_volume_10x`） |
| `signal_max_ratio` | `float` | 最优信号最大涨幅（%） |
| `signal_max_mcap` | `float` | 最优信号最高市值（USD） |
| `signal_max_time` | `float` | 最高点时间（Unix 秒） |
| `signal_open_mcap` | `float` | 信号发出时市值（USD） |
| `signal_open_time` | `float` | 信号发出时间（Unix 秒） |
| `signal_count_d1` | `integer` | 24h 信号触发次数 |
| `last_traded` | `float` | 最新信号时间（Unix 秒） |
| `max_up_ratio` | `float` | 历史最大涨幅（%，从最低点到最高点） |
| `max_up_mcap` | `float` | 历史最高市值（USD） |
| `max_up_mcap_time` | `float` | 历史最高市值时间（Unix 秒） |
| `max_up_duration` | `float` | 开盘到最高市值时长（秒） |
| `ai_max_up_ratio` | `float\|null` | AI 狙击信号发出后最大涨幅（%） |
| `ai_max_up_ratio_mcap` | `float` | AI 狙击信号发出后最高市值（USD） |
| `ai_max_price_time` | `integer` | AI 狙击信号发出后最高价时间（Unix 秒） |

### all_signals_max_ratio 没中信号的收益数据摘要

以信号类型为 key，记录该 Token 在该类型下的最优信号表现。

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `string` | 信号类型 |
| `open_mcap` | `float` | 信号开仓市值（USD） |
| `open_time` | `float` | 信号开仓时间（Unix 秒） |
| `max_mcap` | `float` | 信号后最高市值（USD） |
| `max_ratio` | `float` | 最大涨幅（%，从 `open_mcap` 到 `max_mcap`） |
| `max_time` | `float` | 最高点时间（Unix 秒） |

---

### off_meta Token 元数据

平台发行时的社交 / 媒体信息，不同平台字段可能为空对象 `{}`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | `string` | 项目描述 |
| `image` | `string` | Token 图标 URL |
| `launchTime` | `integer` | 上线时间（毫秒时间戳） |
| `twitter` | `string` | Twitter / X 链接 |
| `website` | `string` | 官网链接 |

---

### tag_users_holding_percent 8大实时持仓指标

各类型地址当前持仓占比（%），总和不一定为 100。

| 字段 | 类型 | 说明 |
|------|------|------|
| `smart_volume` | `float` | 聪明钱地址持仓占比 |
| `whale_volume` | `float` | 巨鲸地址持仓占比 |
| `new_volume` | `float` | 新地址持仓占比 |
| `old_volume` | `float` | 老地址持仓占比 |
| `frequent_volume` | `float` | 高频交易地址持仓占比 |
| `amm_volume` | `float` | AMM / 做市商地址持仓占比 |
| `exchange_volume` | `float` | 交易所地址持仓占比 |
| `scam_volume` | `float` | 诈骗地址持仓占比 |
| `shit_volume` | `float` | 垃圾地址持仓占比 |