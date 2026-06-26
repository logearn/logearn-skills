# LogEarn Skills

LogEarn 作为专注筹码分析的交易平台，提供了动态筹码分析，实时资金流向指标，早期精选金狗信号等丰富且专业功能， 大大的提升了行业用户交易的胜率。本 Skill 通过 CLI 工具对接 LogEarn Open API, 实现 AI 信号查询、资金流向、筹码分析、热门榜单、K 线数据、钱包管理、链上交易等功能，旨在帮助开发者和交易者更好地利用这些专业数据。将自己的 AI Agent 打造成最聪明的交易 Agent。

## 快速开始

### 1. 配置环境变量

```bash
export LOGEARN_API_KEY="sk_xxxxxxxx"                      # 必填：登录 https://logearn.com 获取
export LOGEARN_API_BASE="https://api.logearn.com/logearn"     # 可选，默认此值
```

### 2. 运行

```bash
python logearn-cli.py <命令> [参数]
```

---

## 命令速查

| 命令 | 说明 | 必填参数 |
|------|------|---------|
| `log-get-native-price` | SOL/BNB 实时价格（公开，免费） | — |
| `log-get-24h-signals` | 24h 内所有 AI 信号（3 credits） | — |
| `log-filter-signal` | AI 信号搜索，按类型/时间区间/触发次数（2 credits） | — |
| `log-get-hot` | 热门代币榜单（1 credit） | `--group 5m\|1h` |
| `log-get-token-info` | 代币详情 + 八大持仓指标（1 credit） | `--token` `--chain` |
| `log-get-token-signal` | 代币历史 AI 信号（2 credits） | `--token` `--chain` |
| `log-get-follow-tx` | 关注的聪明钱最新链上交易（2 credits） | — |
| `log-get-kline` | 历史 K 线（1 credit） | `--token` `--chain` |
| `log-get-balance` | 钱包余额（免费） | `--address` `--chain`（均可选） |
| `log-get-positions` | 持仓列表（免费） | `--address`（可选） |
| `log-get-trade-logs` | 交易明细（免费） | `--address`（可选） |
| `log-get-limit-orders` | 限价单列表（免费） | `--address`（可选） |
| `log-swap-solana` | Solana 买卖 （免费） | `--caller` `--event` `--action` |
| `log-swap-bsc` | BSC 买卖 （免费） | `--caller` `--event` `--action` |
| `log-limit-order` | 挂限价单 （免费） | `--caller` `--token` `--action` |
| `log-quota` | 查询 Credit 余额（免费） | — |

---

## 使用示例

```bash
# 查询 5 分钟热门榜单（Solana）
python logearn-cli.py log-get-hot --group 5m --chain 3

# 查询 24 小时所有 AI 信号
python logearn-cli.py log-get-24h-signals

# 筛选 Solana 上的鲸鱼信号（AI 信号搜索）
python logearn-cli.py log-filter-signal --chain 3 --type whale

# 查询代币八大持仓指标
python logearn-cli.py log-get-token-info \
  --token FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump \
  --chain 3

# 查询代币历史 AI 信号
python logearn-cli.py log-get-token-signal \
  --token FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump \
  --chain 3

# 查询过去 24 小时 K 线（15 分钟周期）
python logearn-cli.py log-get-kline \
  --token FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump \
  --chain 3 --interval 900 --size 96

# 查询 Solana 钱包余额
python logearn-cli.py log-get-balance \
  --address Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY \
  --chain 3

# 查询持仓情况
python logearn-cli.py log-get-positions \
  --address Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY

# 用 0.1 SOL 买入代币（0.1 SOL = 100000000 lamports）
python logearn-cli.py log-swap-solana \
  --caller Ax2dHBwWJ2DBoe2z5gjjeuGQuyqvnyzDCZXyc3FMSPBY \
  --event buy \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<token>","amountIn":"100000000","antiMev":1}'

# 查询 Credit 余额
python logearn-cli.py log-quota
```

---

## AI 信号类型

| 信号字段名 | 中文名 | 说明 |
|-----------|--------|------|
| `continue_breakout_volume` | 早期精选 | 早期小市值、有潜力的金狗 |
| `v_breakout_volume` | 回撤反弹 | 价格回撤后出现反弹迹象 |
| `breakout_volume_10x` | 休眠苏醒 | 沉寂后重新活跃，有 10x 潜力 |
| `whale` | 蓝筹共振 | 巨鲸资金介入，多维度共振 |
| `followed` | 关注信号 | 所有关注的钱包的链上交易明细 |

---

## 链 ID

| 链 | ID |
|----|----|
| Solana | `3` |
| BSC | `56` |

---

## 实时数据（WebSocket）

LogEarn 提供 5 种 WebSocket 实时数据流，无需轮询即可订阅最新行情、AI 信号推送、关注地址交易、K 线及链上买卖明细：

| 数据流 | Topic 格式 | 说明 |
|--------|-----------|------|
| 实时代币行情 | `/token_stream_v2:<chainID>` | 全量代币实时价格与指标更新 |
| 全量 AI 信号 | `/notification_stream` | 所有类型 AI 信号实时推送 |
| 关注地址交易 | `/notification_stream/<uid>` | 我关注的聪明钱实时链上交易 |
| 实时 K 线 | `/kline_v2:<chainID>:<token>:<resolution>` | 指定代币实时 K 线 |
| 代币交易明细 | `/token:tx:<chainID>:<token>` | 指定代币实时买卖记录 |

完整接口文档：[ws_api.md](./ws_api.md)　　完整 Python Demo：[test_ws.py](./test_ws.py)

---

## 文档

- 详细接口说明：[api.md](./api.md)
- WebSocket 实时数据：[ws_api.md](./ws_api.md)
- AI Agent 接入指南：[skill.md](./skill.md)
