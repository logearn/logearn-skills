---
description: Query on-chain AI signals, hot tokens, K-lines, token details, wallet positions, trade logs, limit orders, and execute Solana/BSC swaps via LogEarn Open API.
---

# LogEarn Skills

Access LogEarn's on-chain data and AI signal APIs for Solana and BSC. Execute the commands below using `python logearn-cli.py`.

## Setup

```bash
export LOGEARN_API_KEY=sk_xxxxxxxx   # required — get from https://logearn.com
export LOGEARN_API_BASE=https://logearn.com/logearn  # optional
```

**Requires**: Python 3.7+, no extra dependencies.

## Commands

### Data Queries

```bash
# AI comprehensive signals (Solana + BSC)
python logearn-cli.py log-get-24h-signals [--chain 3|56]

# Hot token list
python logearn-cli.py log-get-hot [--chain 3|56] [--group 5m|1h]

# K-line / OHLCV  (--token required)
python logearn-cli.py log-get-kline --token <addr> [--chain 3] [--interval 900] [--size 96] [--end <unix>]

# Token on-chain details
python logearn-cli.py log-get-token-info --token <addr> [--chain 3]

# Token AI signal history  (--chain required)
python logearn-cli.py log-get-token-signal --token <addr> --chain 3|56

# Native coin balance  (--chain required)
python logearn-cli.py log-get-balance --address <wallet> --chain 3|56

# Wallet positions
python logearn-cli.py log-get-positions --address <wallet> [--size 20] [--page 0] [--sort open_position_time] [--dir desc]

# Trade history
python logearn-cli.py log-get-trade-logs --address <wallet> [--chain 3] [--size 100] [--page 0]

# Limit orders
python logearn-cli.py log-get-limit-orders --address <wallet> [--status -1|0|1|2]
```

### Trades ⚠️ Real Funds

```bash
# Solana buy/sell  (5 credits each)
python logearn-cli.py log-swap-solana \
  --caller <solanaWallet> --event buy|sell \
  --action '{"tokenIn":"<addr>","tokenOut":"<addr>","amountIn":"<raw>","antiMev":1,"autoMaxFee":0.2}'

# BSC buy/sell
python logearn-cli.py log-swap-bsc \
  --caller <evmWallet> --event buy|sell \
  --action '{"tokenIn":"<addr>","tokenOut":"<addr>","amountIn":"<raw>","antiMev":1}'

# Place limit order
python logearn-cli.py log-limit-order \
  --caller <wallet> --token <addr> --chain 3 --event 1|2 \
  --action '{"tokenIn":"<addr>","tokenOut":"<addr>","amountIn":"<raw>","limitNumber":<price>,"limitType":1,"direction":1,"antiMev":1}'
```

### Account

```bash
python logearn-cli.py log-quota
python logearn-cli.py log-stats
python logearn-cli.py log-keys
```

## Chain IDs: Solana=`3`, BSC=`56`
