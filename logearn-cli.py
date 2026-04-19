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
  log-get-24h-signals   24小时所有信号     [--chain 3,56]
  log-get-hot           热门榜单       [--chain 3,56] [--group 5m|1h]
  log-get-token-info    Token详情      --token <addr> [--chain 3]
  log-get-token-signal  历史AI信号     --token <addr> [--chain 3]
  log-get-kline         K线数据        --token <addr> [--chain 3] [--interval 900] [--size 96] [--end <unix>]
  log-get-balance       Coin余额       --address <wallet> [--chain 3]

  log-get-positions     仓位查询       --address <wallet> [--size 20] [--page 0] [--sort field] [--dir asc|desc]
  log-get-trade-logs    交易明细       --address <wallet> [--chain 3] [--size 100] [--page 0]
  log-get-limit-orders  限价单列表     --address <wallet> [--status -1|0|1|2]

Trade  ⚠️ real funds:
  log-swap-solana       Solana买卖     --caller <wallet> --event buy|sell --action '<json>'
  log-swap-bsc          BSC买卖        --caller <wallet> --event buy|sell --action '<json>'
  log-limit-order       挂限价单       --caller <wallet> --token <addr> --action '<json>' [--chain 3] [--event 1|2]

Account:
  log-quota             配额余额
  log-stats             调用统计
  log-keys              API Key 列表
""".strip()


def main():
    if not os.environ.get('LOGEARN_API_KEY'):
        die('LOGEARN_API_KEY env is not set')

    argv = sys.argv[1:]
    if not argv:
        print(USAGE)
        sys.exit(0)

    cmd, *rest = argv
    opts = parse_args(rest)

    if cmd == 'log-get-24h-signals':
        chain  = opts['chain'].split(',') if 'chain' in opts else None
        res    = api.get_all_signal(chain=chain)
        data   = helpers.unwrap(res, 'get-24h-signals')
        print(json.dumps(helpers.fmt_signals(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-hot':
        chain = opts['chain'].split(',') if 'chain' in opts else None
        gid = 13 if opts['group'] == '1h' else 12
        res   = api.get_hot_list(chain=chain, token_group_id=gid)
        data  = helpers.unwrap(res, 'get-hot')
        print(json.dumps(helpers.fmt_signals(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-token-info':
        if 'token' not in opts: die('--token <address> required')
        if 'chain' not in opts: die('--chain <chain> required')

        chain = [int(opts['chain'])] if 'chain' in opts else None
        res   = api.get_token_info(base=opts['token'], chain=chain)
        data  = helpers.unwrap(res, 'get-token-info')
        # data = {'3': [{xxx}], '56': [{xxx}]}
        print(json.dumps(helpers.fmt_signals(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-token-signal':
        if 'token' not in opts: die('--token <address> required')
        if 'chain' not in opts: die('--chain <chain> required')        
        res  = api.get_token_signal(index_token_address=opts['token'],
                                    chain=opts.get('chain'))
        data = helpers.unwrap(res, 'get-token-signal')
        print(json.dumps(helpers.fmt_signals(data), ensure_ascii=False, indent=2, sort_keys=True))

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
        if 'address' not in opts: die('--address <wallet> required')
        if 'chain' not in opts: die('--chain <chain> required')

        res  = api.get_coin_balance(address=opts['address'], chain=int(opts['chain']))
        data = helpers.unwrap(res, 'get-balance')
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-positions':
        if 'address' not in opts: die('--address <wallet> required')
        res  = api.get_wallet_positions(
            address        = opts['address'],
            page_size      = int(opts['size']) if 'size' in opts else None,
            page_num       = int(opts['page']) if 'page' in opts else None,
            sort_field     = opts.get('sort'),
            sort_direction = opts.get('dir'),
            hold_amount    = opts.get('min'),
        )
        data = helpers.unwrap(res, 'get-positions')
        print(json.dumps(helpers.fmt_positions(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-trade-logs':
        if 'address' not in opts: die('--address <wallet> required')
        res  = api.get_trade_logs(
            address   = opts['address'],
            chain     = opts.get('chain'),
            page_size = int(opts['size']) if 'size' in opts else None,
            page_num  = int(opts['page']) if 'page' in opts else None,
        )
        data = helpers.unwrap(res, 'get-trade-logs')
        print(json.dumps(helpers.fmt_trade_logs(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-get-limit-orders':
        if 'address' not in opts: die('--address <wallet> required')
        res  = api.get_limit_orders(
            address   = opts['address'],
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
        res  = api.solana_swap(caller=opts['caller'], event_type=opts['event'],
                               action=json.loads(opts['action']))
        data = helpers.unwrap(res, 'swap-solana')
        print(json.dumps(helpers.fmt_swap_result(data), ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-swap-bsc':
        if 'caller' not in opts: die('--caller <wallet> required')
        if 'event'  not in opts: die('--event buy|sell required')
        if 'action' not in opts: die("--action '{\"tokenIn\":...}' required")
        res  = api.bsc_swap(caller=opts['caller'], event_type=opts['event'],
                            action=json.loads(opts['action']))
        data = helpers.unwrap(res, 'swap-bsc')
        print(json.dumps(helpers.fmt_swap_result(data), ensure_ascii=False, indent=2, sort_keys=True))

    elif cmd == 'log-limit-order':
        if 'caller' not in opts: die('--caller <wallet> required')
        if 'token'  not in opts: die('--token <address> required')
        if 'action' not in opts: die("--action '{\"limitNumber\":...}' required")
        res  = api.limit_order(
            caller        = opts['caller'],
            token_address = opts['token'],
            action        = json.loads(opts['action']),
            chain_id      = int(opts['chain']) if 'chain' in opts else None,
            event_type    = int(opts['event']) if 'event' in opts else None,
            expired_at    = int(opts['expires']) if 'expires' in opts else None,
        )
        data = helpers.unwrap(res, 'limit-order')
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


    elif cmd == 'log-quota':
        res = api.get_quota()
        print(json.dumps(helpers.unwrap(res, 'quota'), indent=2, ensure_ascii=False))

    elif cmd == 'log-stats':
        res = api.get_stats()
        print(json.dumps(helpers.unwrap(res, 'stats'), indent=2, ensure_ascii=False))

    elif cmd == 'log-keys':
        res = api.get_keys()
        print(json.dumps(helpers.unwrap(res, 'keys'), indent=2, ensure_ascii=False))

    else:
        print(f'Unknown command: {cmd}\n', file=sys.stderr)
        print(USAGE)
        sys.exit(1)


if __name__ == '__main__':
    main()
