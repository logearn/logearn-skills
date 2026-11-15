#!/usr/bin/env python3
"""
LogEarn CLI  (Python 3.7+  |  env: LOGEARN_API_KEY)
Usage: python logearn-cli.py <command> [--key value ...]
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import api
import helpers
import json

# ---------------------------------------------------------------------------
# Arg parser: --key value  →  { 'key': value }
# ---------------------------------------------------------------------------

def parse_args(argv: list) -> dict:
    opts = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith('--'):
            key = argv[i][2:]
            opts[key] = argv[i + 1] if i + 1 < len(argv) else True
            i += 2
        else:
            i += 1
    return opts


def die(msg: str):
    print(f'Error: {msg}', file=sys.stderr)
    sys.exit(1)


USAGE = """
LogEarn CLI  (Python 3.7+  |  env: LOGEARN_API_KEY)

Usage: python logearn-cli.py <command> [options]

Data:
  log-get-native-price  查询 SOL/BNB 最新行情价格（公开，无需鉴权）  [--chain 3|56]
  log-get-24h-signals   查询24小时内所有【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】信号以及相关代币   [--chain 3,56]
  log-filter-signal     AI信号搜索（按类型/时间区间/触发次数）   [--chain 3,56] [--type s15|s300|kline|whale] [--begin <unix>] [--end <unix>] [--min <n>] [--max <n>] [--page 0] [--size 500]
  log-get-hot           查询五分钟/1小时热门代币榜单         [--chain 3,56] [--group 5m|1h]
  log-get-token-info    查询代币详情，包括八大实时持仓指标     --token <addr> [--chain 3]
  log-get-token-signal  查询某一个代币所有历史信号，包括【早期精选、 回撤反弹、休眠后苏醒、蓝筹共振】    --token <addr> [--chain 3]
  log-get-follow-tx     查询关注的聪明錢最新链上交易         [--chain 3,56]
  log-get-kline         获取代币的历史K线数据             --token <addr> [--chain 3] [--interval 900] [--size 96] [--end <unix>]
  log-get-balance       查询所有交易账号余额              [--address <wallet>] [--chain 3]

  log-get-positions     所有交易账户仓位查询              [--address <wallet>] [--size 20] [--page 0] [--sort field] [--dir asc|desc]
  log-get-trade-logs    查询所有交易明细                [--address <wallet>] [--chain 3] [--size 100] [--page 0]
  log-get-limit-orders  查询所有限价单                  [--address <wallet>] [--status -1|0|1|2]

Trade  real funds:
  log-swap-solana       Solana 买卖                    --caller <wallet> --event buy|sell --action '<json:tokenIn,tokenOut,amountIn>' [--slippage 0.5] [--min-out <n>]
  log-swap-bsc          BSC 买卖                       --caller <wallet> --event buy|sell --action '<json:tokenIn,tokenOut,amountIn>' [--slippage 0.5] [--min-out <n>]
  log-limit-order       挂限价单（买单自动签授权）     --caller <wallet> --token <addr> --action '<json>' [--chain 3] [--event 1|2]

Account:
  log-quota             配额余额

Config:
  config                查看如何配置（去网页创建 API Key，复制配置块）
  config --check        检查是否已配置（退出码 0=已配置并自检通过，1=未配置/无效）
  config --apply        从标准输入读取网页复制的配置块，写入 ~/.config/logearn/.env 并自检
""".strip()


_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'logearn')
_ENV_FILE   = os.path.join(_CONFIG_DIR, '.env')
_WEB_URL    = os.environ.get('LOGEARN_WEB_URL', 'https://logearn.com')


def _write_env(kv: dict):
    """把 kv 写进 ~/.config/logearn/.env（保留其它行，覆盖这几项），权限 0600。"""
    lines = []
    managed = set(kv.keys())
    if os.path.exists(_ENV_FILE):
        for line in open(_ENV_FILE, encoding='utf-8'):
            k = line.split('=', 1)[0].strip()
            if k and k not in managed:
                lines.append(line.rstrip('\n'))
    for k, v in kv.items():
        lines.append(f'{k}={v}')
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_ENV_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    try:
        os.chmod(_ENV_FILE, 0o600)
    except Exception:
        pass


def cmd_config(opts: dict):
    # --check：exit 0=已配置并自检通过，1=未配置/无效
    if opts.get('check'):
        if not api.KEY:
            print('LOGEARN_API_KEY 未配置', file=sys.stderr)
            sys.exit(1)
        try:
            res = api.get_quota()  # 轻量、只要 X-Api-Key
            if isinstance(res, dict) and str(res.get('code')) == '200':
                print('配置有效，可以开始使用。')
                sys.exit(0)
            print(f'配置验证失败：{res.get("message") if isinstance(res, dict) else res}', file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f'配置已写入，但自检请求失败（可能是网络问题），可先尝试使用：{e}', file=sys.stderr)
            sys.exit(1)

    # --apply：从 stdin 读网页复制的配置块（含 LOGEARN_API_KEY= / LOGEARN_API_SECRET= / 可选 LOGEARN_API_BASE=）
    if opts.get('apply'):
        pasted = sys.stdin.read()
        kv = {}
        for line in pasted.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, _, v = line.partition('=')
            k = k.strip()
            if k in ('LOGEARN_API_KEY', 'LOGEARN_API_SECRET', 'LOGEARN_API_BASE', 'LOGEARN_CLIENT_ID', 'LOGEARN_ACCOUNT_ID', 'LOGEARN_CLIENT_KEY'):
                kv[k] = v.strip().strip('"').strip("'")
        if 'LOGEARN_API_KEY' not in kv:
            die('粘贴内容里没有 LOGEARN_API_KEY=...，请在网页点「复制配置」拿到完整配置块再粘贴')
        _write_env(kv)
        print(f'已写入 {_ENV_FILE}')
        # 新进程自检（本进程 api.KEY 在 import 时已固定，用子进程读取新写入的配置文件）
        import subprocess
        r = subprocess.run([sys.executable, os.path.abspath(__file__), 'config', '--check'])
        sys.exit(r.returncode)

    # 默认：打印引导
    print(f"""请按以下步骤配置 LogEarn API Key：
1. 打开 {_WEB_URL} 登录后进入「API」页，点「创建 API Key」。
2. 创建时浏览器会生成密钥对：API Key 可随时复制；**API Secret 只显示一次**（账户读 / 交易才需要它）。
3. 点页面上的「复制配置」拿到配置块，然后运行：
     python logearn-cli.py config --apply   # 然后把配置块粘贴进来，回车后按 Ctrl-D 结束
   或手动写入 {_ENV_FILE}（每行 KEY=VALUE，权限 600）。
提示：公开读（信号 / 热门 / K 线 / 代币详情）只要 API Key；账户读（余额 / 仓位 / 成交 / 限价单）和交易需要 API Secret。
不要把 API Secret 贴进聊天、截图或提交进代码仓库。""")


def _swap(fn, chain_id, solana, opts):
    """交易：只给 CA / 金额即可。min_amount_out 默认用 token 详情 + native 价格自动估算（默认滑点 50%，--slippage 0.3 = 30%），
    也可用 --min-out 直接指定（最小单位整数）。CLI 用 API Secret 本地签交易意图（10 分钟有效）后提交。"""
    action = json.loads(opts['action'])
    for k in ('tokenIn', 'tokenOut', 'amountIn'):
        if k not in action: die(f"--action 里缺少 {k}")
    try:
        if 'min-out' in opts:
            min_out, usd = opts['min-out'], opts.get('usd', '0')
        else:
            est = api.estimate_min_out(chain_id=chain_id, token_in=action['tokenIn'], token_out=action['tokenOut'],
                                       amount_in=action['amountIn'], slippage=float(opts.get('slippage', api.DEFAULT_SLIPPAGE)))
            min_out, usd = est['min_amount_out'], opts.get('usd', est['amount_usd'])
            print(f"[estimate] min_amount_out={min_out} ≈${float(usd):.2f}（预期 {est['expected_out']}，滑点 {opts.get('slippage', api.DEFAULT_SLIPPAGE)}）", file=sys.stderr)
        auth = api.build_trade_auth(chain_id=chain_id, wallet=opts['caller'], token_in=action['tokenIn'],
                                    token_out=action['tokenOut'], amount_in=action['amountIn'],
                                    min_amount_out=min_out, amount_usd=usd, solana=solana)
    except api.ApiError as e:
        die(str(e))
    return fn(caller=opts['caller'], event_type=opts['event'], action=action, tee_auth=auth)


def main():
    argv = sys.argv[1:]
    if not argv:
        print(USAGE)
        sys.exit(0)

    cmd, *rest = argv
    opts = parse_args(rest)

    if cmd == 'config':
        cmd_config(opts)
        return

    if not os.environ.get('LOGEARN_API_KEY'):
        die('LOGEARN_API_KEY 未配置。运行: python logearn-cli.py config')

    if cmd == 'log-get-native-price':
        chain = int(opts['chain']) if 'chain' in opts else None
        res   = api.get_native_price(chain=chain)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif cmd == 'log-get-24h-signals':
        chain  = opts['chain'].split(',') if 'chain' in opts else None
        res    = api.get_all_signal(chain=chain)
        data   = helpers.unwrap(res, 'get-24h-signals')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-filter-signal':
        chain = opts['chain'].split(',') if 'chain' in opts else None
        res   = api.filter_signal(
            chain             = chain,
            signal_type       = opts.get('type'),
            signal_begin_time = int(opts['begin']) if 'begin' in opts else None,
            signal_end_time   = int(opts['end'])   if 'end'   in opts else None,
            min_signal_count  = int(opts['min'])   if 'min'   in opts else None,
            max_signal_count  = int(opts['max'])   if 'max'   in opts else None,
            page_num          = int(opts['page'])  if 'page'  in opts else None,
            page_size         = int(opts['size'])  if 'size'  in opts else None,
        )
        data = helpers.unwrap(res, 'filter-signal')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-hot':
        chain = opts['chain'].split(',') if 'chain' in opts else None
        gid = 13 if opts.get('group') == '1h' else 12
        res   = api.get_hot_list(chain=chain, token_group_id=gid)
        data  = helpers.unwrap(res, 'get-hot')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-token-info':
        if 'token' not in opts: die('--token <address> required')
        if 'chain' not in opts: die('--chain <chain> required')

        chain = [int(opts['chain'])] if 'chain' in opts else None
        res   = api.get_token_info(base=opts['token'], chain=chain)
        data  = helpers.unwrap(res, 'get-token-info')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-token-signal':
        if 'token' not in opts: die('--token <address> required')
        if 'chain' not in opts: die('--chain <chain> required')        
        res  = api.get_token_signal(index_token_address=opts['token'],
                                    chain=opts.get('chain'))
        data = helpers.unwrap(res, 'get-token-signal')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-get-follow-tx':
        chain     = opts['chain'].split(',') if 'chain' in opts else None
        res  = api.get_follow_tx(chain=chain)
        data = helpers.unwrap(res, 'get-follow-tx')
        native_prices = helpers.get_cached_native_prices()
        print(json.dumps(helpers.fmt_signals(data, native_prices), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-kline':
        if 'token' not in opts: die('--token <address> required')
        if 'chain' not in opts: die('--chain <chain> required')        

        res  = api.get_kline_list(
            base          = opts['token'],
            chain         = opts.get('chain'),
            interval_time = int(opts['interval']) if 'interval' in opts else None,
            page_size     = int(opts['size'])     if 'size'     in opts else None,
            end_time      = int(opts['end'])      if 'end'      in opts else None,
        )
        data = helpers.unwrap(res, 'get-kline')      
        print(json.dumps(data['body'], ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-get-balance':
        # if 'address' not in opts: die('--address <wallet> required')
        # if 'chain' not in opts: die('--chain <chain> required')

        res  = api.get_coin_balance(address=opts.get('address'), chain=int(opts['chain']) if 'chain' in opts else None)
        data = helpers.unwrap(res, 'get-balance')
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-positions':
        res  = api.get_wallet_positions(
            address        = opts.get('address'),
            page_size      = int(opts['size']) if 'size' in opts else None,
            page_num       = int(opts['page']) if 'page' in opts else None,
            sort_field     = opts.get('sort'),
            sort_direction = opts.get('dir'),
            hold_amount    = opts.get('min'),
        )
        data = helpers.unwrap(res, 'get-positions')
        print(json.dumps(helpers.fmt_positions(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-trade-logs':
        res  = api.get_trade_logs(
            address   = opts.get('address'),
            chain     = opts.get('chain'),
            page_size = int(opts['size']) if 'size' in opts else None,
            page_num  = int(opts['page']) if 'page' in opts else None,
        )
        data = helpers.unwrap(res, 'get-trade-logs')
        print(json.dumps(helpers.fmt_trade_logs(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-limit-orders':
        res  = api.get_limit_orders(
            address   = opts.get('address'),
            status    = int(opts['status']) if 'status' in opts else None,
            page_size = int(opts['size'])   if 'size'   in opts else None,
            page_num  = int(opts['page'])   if 'page'   in opts else None,
        )
        data = helpers.unwrap(res, 'get-limit-orders')
        print(json.dumps(helpers.fmt_limit_orders(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-swap-solana':
        if 'caller' not in opts: die('--caller <wallet> required')
        if 'event'  not in opts: die('--event buy|sell required')
        if 'action' not in opts: die("--action '{\"tokenIn\":...}' required")
        res  = _swap(api.solana_swap, 3, True, opts)
        data = helpers.unwrap(res, 'swap-solana')
        print(json.dumps(helpers.fmt_swap_result(data), ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-swap-bsc':
        if 'caller' not in opts: die('--caller <wallet> required')
        if 'event'  not in opts: die('--event buy|sell required')
        if 'action' not in opts: die("--action '{\"tokenIn\":...}' required")
        res  = _swap(api.bsc_swap, 56, False, opts)
        data = helpers.unwrap(res, 'swap-bsc')
        print(json.dumps(helpers.fmt_swap_result(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-limit-order':
        if 'caller' not in opts: die('--caller <wallet> required')
        if 'token'  not in opts: die('--token <address> required')
        if 'action' not in opts: die("--action '{\"limitNumber\":...}' required")
        try:
            res  = api.limit_order(
                caller        = opts['caller'],
                token_address = opts['token'],
                action        = json.loads(opts['action']),
                chain_id      = int(opts['chain']) if 'chain' in opts else None,
                event_type    = int(opts['event']) if 'event' in opts else None,
                expired_at    = int(opts['expires']) if 'expires' in opts else None,
            )
        except api.ApiError as e:
            die(str(e))
        data = helpers.unwrap(res, 'limit-order')
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-quota':
        res = api.get_quota()
        print(json.dumps(helpers.unwrap(res, 'quota'), indent=2, ensure_ascii=False))

    else:
        print(f'Unknown command: {cmd}\n', file=sys.stderr)
        print(USAGE)
        sys.exit(1)


if __name__ == '__main__':
    main()
