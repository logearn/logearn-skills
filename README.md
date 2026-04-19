# LogEarn Skills

> 基于 LogEarn Open API 的链上数据查询与交易 Python 工具集，支持 Solana 和 BSC。

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 功能概览

- **AI 综合信号** — 获取 Solana/BSC 全链实时 AI 信号
- **热门榜单** — 查询最近 5 分钟 / 1 小时热门 Token
- **K 线数据** — 获取任意 Token 的 OHLCV K 线
- **Token 详情** — 价格、市值、持仓分布等链上数据
- **Token 历史信号** — 查看特定 Token 的历史 AI 信号记录
- **仓位查询** — 多链多地址仓位一览
- **交易明细** — 历史买卖记录
- **限价单管理** — 查询/挂限价单（含止盈止损）
- **链上交易** — Solana / BSC 真实交易（`solana_swap` / `bsc_swap`）
- **账户管理** — Credits 余额、调用统计、API Key 列表

---

## 快速开始

### 1. 获取 API Key

登录 [https://logearn.com](https://logearn.com) 官网获取 `LOGEARN_API_KEY`（格式：`sk_xxxxxxxx`）。

### 2. 设置环境变量

```bash
export LOGEARN_API_KEY=sk_xxxxxxxx

# 可选：自定义 API 地址（默认 https://logearn.com/logearn）
export LOGEARN_API_BASE=https://logearn.com/logearn
```

### 3. 运行

无需安装任何依赖，Python 3.7+ 标准库即可运行：

```bash
python logearn-cli.py log-get-24h-signals
```

---

## CLI 命令速查

### 数据查询

```bash
# AI 综合信号（双链）
python logearn-cli.py log-get-24h-signals

# 热门榜单（5m / 1h）
python logearn-cli.py log-get-hot --group 5m
python logearn-cli.py log-get-hot --chain 3 --group 1h

# K 线（15m，96 根）
python logearn-cli.py log-get-kline --token <tokenAddress>

# Token 详情
python logearn-cli.py log-get-token-info --token <tokenAddress>

# Token 历史 AI 信号（--chain 必填）
python logearn-cli.py log-get-token-signal --token <tokenAddress> --chain 3

# 原生币余额（--chain 必填）
python logearn-cli.py log-get-balance --address <walletAddress> --chain 3

# 仓位
python logearn-cli.py log-get-positions --address <walletAddress>

# 交易明细
python logearn-cli.py log-get-trade-logs --address <walletAddress>

# 限价单列表
python logearn-cli.py log-get-limit-orders --address <walletAddress>
```

### 交易（⚠️ 真实资金）

```bash
# Solana 买入
python logearn-cli.py log-swap-solana \
  --caller <walletAddress> \
  --event buy \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<tokenAddress>","amountIn":"11904761","antiMev":1,"autoMaxFee":0.2}'

# BSC 卖出
python logearn-cli.py log-swap-bsc \
  --caller <evmWalletAddress> \
  --event sell \
  --action '{"tokenIn":"<tokenAddress>","tokenOut":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c","amountIn":"<amountRaw>","antiMev":1}'

# 挂限价单
python logearn-cli.py log-limit-order \
  --caller <walletAddress> \
  --token <tokenAddress> \
  --chain 3 --event 1 \
  --action '{"tokenIn":"So11111111111111111111111111111111111111112","tokenOut":"<tokenAddress>","amountIn":"11904761","limitNumber":0.00013789,"limitType":1,"direction":1,"antiMev":1}'
```

### 账户

```bash
python logearn-cli.py log-quota   # Credits 余额
python logearn-cli.py log-stats   # 近 30 天调用统计
python logearn-cli.py log-keys    # API Key 列表
```

---

## 链 ID

| 链 | ID |
|----|----|
| Solana | `3` |
| BSC | `56` |

---

## 计费说明

| 操作 | 消耗 |
|------|------|
| AI 综合信号 | 3 credits |
| 热门榜单 / K线 | 1–2 credits |
| Token 详情 / 历史信号 | 1 credit |
| 链上交易（swap） | 5 credits |
| 仓位 / 交易明细 / 限价单查询 | 免费（限速 1/s） |

充值：0.5 SOL = 100,000 credits（最低 100,000）。所有 API Key 共享 Credits。

---


## Python API 调用

除 CLI 外，也可直接在 Python 代码中引用：

```python
import sys
sys.path.insert(0, 'src')
import api

# 查询 AI 信号
data = api.get_all_signal(chain=['3', '56'])

# 查询仓位
data = api.get_wallet_positions(address='<walletAddress>', page_size=20)

# Solana 交易
data = api.solana_swap(
    caller='<walletAddress>',
    event_type='buy',
    action={
        'tokenIn': 'So11111111111111111111111111111111111111112',
        'tokenOut': '<tokenAddress>',
        'amountIn': '11904761',
        'antiMev': 1,
    }
)
```

详细接口文档见 [api.md](api.md)。

---

## 错误处理

所有命令输出 JSON，检查 `code` 字段：

| code | 含义 |
|------|------|
| `200` | 成功，数据在 `data` 字段 |
| 非 200 | 失败，原因在 `msg` 字段 |
| `"Quota insufficient"` | Credits 不足，需充值 |
| `"Credits per minute exceeded"` | 触发频率限制（600/min） |
| `"Invalid or disabled API Key"` | 检查 `LOGEARN_API_KEY` |

---

## 相关链接

- 官网：[https://logearn.com](https://logearn.com)
- 客服 Telegram：[@chickenbro_logearn](https://t.me/chickenbro_logearn)
