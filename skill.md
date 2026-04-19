---
name: LogEarn-skills
description: >-
  This skill should be used when the user asks to query "AI signal", "AI综合信号",
  "hot tokens", "热门榜单", "pool list", "池子信息", "liquidity pool",
  "k-line", "K线", "candlestick", "token info", "token details", "Token详情",
  "get kline", "查K线", "查信号", "查热门", "查仓位", "wallet positions",
  "coin balance", "查余额", "trade logs", "交易明细", "limit order", "限价单",
  "buy token", "sell token", "solana swap", "bsc swap",
  or mentions on-chain data queries or trading for Solana / BSC via LogEarn Open API.
version: 1.0.0
allowed-tools: Bash, Read, AskUserQuestion
metadata:
  openclaw:
    requires:
      env: ["LOGEARN_API_KEY"]
      bins: ["python3"]
    primaryEnv: "LOGEARN_API_KEY"
    emoji: "📡"
    homepage: "https://logearn.com"
---

# LogEarn Skills

On-chain data queries, AI signal access, and trading for Solana and BSC via LogEarn Open API.

## Setup

Required environment variable:
- `LOGEARN_API_KEY` — Your LogEarn API Key (`sk_xxxxxxxx`)
- `LOGEARN_API_BASE` (optional) — defaults to `https://logearn.com/logearn`

**Runtime**: Python 3.7+ (no dependencies needed, stdlib only)

All commands: `python logearn-cli.py log-<command> [options]`

---

## Data Commands

### AI综合信号 — `log-get-24h-signals` (3 credits)

```bash
# All chains (Solana + BSC)
python logearn-cli.py log-get-24h-signals

# Solana only
python logearn-cli.py log-get-24h-signals --chain 3

# BSC only
python logearn-cli.py log-get-24h-signals --chain 56
```

### 热门榜单 — `log-get-hot` (1 credit)

```bash
# Default: all chains, recent 5 min
python logearn-cli.py log-get-hot

# Solana, last 1 hour
python logearn-cli.py log-get-hot --chain 3 --group 1h
```

`--group`: `5m`=最近5分钟（默认）, `1h`=最近1小时

### K线数据 — `log-get-kline` (2 credits)

```bash
# Default: 15min interval, last 96 bars
python logearn-cli.py log-get-kline --token <tokenAddress>

# 1h candles, 48 bars
python logearn-cli.py log-get-kline --token <tokenAddress> --interval 3600 --size 48

# Custom end time
python logearn-cli.py log-get-kline --token <tokenAddress> --interval 900 --end 1775883812
```

`--interval`: `60`=1m, `300`=5m, `900`=15m, `3600`=1h, `86400`=1d

### Token详情 — `log-get-token-info` (1 credit)

```bash
python logearn-cli.py log-get-token-info --token <tokenAddress>

# BSC token
python logearn-cli.py log-get-token-info --token <tokenAddress> --chain 56
```

### Token历史信号 — `log-get-token-signal` (1 credit)

`--chain` 为必填。

```bash
# Solana
python logearn-cli.py log-get-token-signal --token <tokenAddress> --chain 3

# BSC
python logearn-cli.py log-get-token-signal --token <tokenAddress> --chain 56
```

### 账号Coin余额 — `log-get-balance` (1 credit)

`--chain` 为必填。

```bash
# SOL balance (Solana)
python logearn-cli.py log-get-balance --address <walletAddress> --chain 3

# BNB balance (BSC)
python logearn-cli.py log-get-balance --address <walletAddress> --chain 56
```

### 仓位查询 — `log-get-positions` (free, 1/s)

```bash
# Default
python logearn-cli.py log-get-positions --address <walletAddress>

# Paginated, sorted by open_position_time desc
python logearn-cli.py log-get-positions --address <walletAddress> --size 20 --page 0 --sort open_position_time --dir desc

# Multi-address (comma-separated, Solana + EVM mixed)
python logearn-cli.py log-get-positions --address "<solanaAddr>,<evmAddr>"
```

### 交易明细 — `log-get-trade-logs` (free, 1/s)

```bash
# Solana wallet
python logearn-cli.py log-get-trade-logs --address <walletAddress>

# BSC wallet
python logearn-cli.py log-get-trade-logs --address <walletAddress> --chain 56

# With pagination
python logearn-cli.py log-get-trade-logs --address <walletAddress> --size 50 --page 1
```

### 查询限价单 — `log-get-limit-orders` (free, 1/s)

```bash
# Pending orders (default)
python logearn-cli.py log-get-limit-orders --address <walletAddress>

# By status: -1=cancelled, 0=pending, 1=executed, 2=expired
python logearn-cli.py log-get-limit-orders --address <walletAddress> --status 0
```

---

## Trade Commands ⚠️

> **WARNING**: The following commands execute real on-chain transactions using real funds. Operations are irreversible. Always confirm parameters before running.

### Solana交易 — `log-swap-solana` (5 credits)

```bash
# Buy
python logearn-cli.py log-swap-solana \
  --caller <walletAddress> \
  --event buy \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<tokenAddress>","amountIn":"11904761","antiMev":1,"autoMaxFee":0.2,"stopProfit1":100,"stopProfit1Percent":50,"stopLoss1":30,"stopLoss1Percent":100}'

# Sell
python logearn-cli.py log-swap-solana \
  --caller <walletAddress> \
  --event sell \
  --action '{"tokenIn":"<tokenAddress>","tokenOut":"So11111111111111111111111111111111111111112","amountIn":"<amountRaw>","antiMev":1}'
```

### BSC交易 — `log-swap-bsc` (5 credits)

```bash
# Buy
python logearn-cli.py log-swap-bsc \
  --caller <evmWalletAddress> \
  --event buy \
  --action '{"tokenIn":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c","tokenOut":"<tokenAddress>","amountIn":"<amountRaw>","antiMev":1}'

# Sell
python logearn-cli.py log-swap-bsc \
  --caller <evmWalletAddress> \
  --event sell \
  --action '{"tokenIn":"<tokenAddress>","tokenOut":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c","amountIn":"<amountRaw>","antiMev":1}'
```

### 挂限价单 — `log-limit-order` (free, 1/s)

> Auto-executes when price condition is met.

`limitNumber` = 币本位目标价（已处理精度）；`limitType`: `1`=价格, `2`=市值；`direction`: `1`=向上触发（买单等价格下跌）, `2`=向下触发（卖单等价格上涨）。

```bash
# Solana limit buy at target price
python logearn-cli.py log-limit-order \
  --caller <walletAddress> \
  --token <tokenAddress> \
  --chain 3 \
  --event 1 \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<tokenAddress>","amountIn":"11904761","limitNumber":0.00013789,"limitType":1,"direction":1,"antiMev":1,"autoMaxFee":0.2}'

# With expiry (unix timestamp)
python logearn-cli.py log-limit-order \
  --caller <walletAddress> \
  --token <tokenAddress> \
  --chain 3 \
  --event 1 \
  --expires 1807445030 \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<tokenAddress>","amountIn":"11904761","limitNumber":0.00013789,"limitType":1,"direction":1,"antiMev":1}'
```

`--event`: `1`=买入, `2`=卖出 | `--chain`: `3`=Solana, `56`=BSC

---

## Account Commands

```bash
# Query credit balance
python logearn-cli.py log-quota

# Call statistics (last 30 days)
python logearn-cli.py log-stats

# List API Keys
python logearn-cli.py log-keys
```

---

## Error Handling

All commands output JSON. Check `code`:

| code | meaning |
|------|---------|
| `200` | success — data in `data` field |
| non-200 | error — reason in `msg` field |
| `"Quota insufficient"` | recharge credits needed |
| `"Credits per minute exceeded"` | rate limit hit (600/min), slow down |
| `"Invalid or disabled API Key"` | check `LOGEARN_API_KEY` |
| `"Unknown skillCode"` | invalid command path |
