"""
LogEarn Open API — HTTP layer
Uses only Python stdlib (urllib + json). urllib.request automatically reads
https_proxy / HTTPS_PROXY environment variables, so no proxy config is needed.
"""

import json
import os
import urllib.request
import time

BASE = os.environ.get('LOGEARN_API_BASE', 'https://logearn.com/logearn')
KEY  = os.environ.get('LOGEARN_API_KEY', '')


# ---------------------------------------------------------------------------
# Core HTTP helpers
# ---------------------------------------------------------------------------

def http_post(path: str, body: dict = None) -> dict:
    payload = json.dumps(body or {}).encode('utf-8')
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=payload,
        headers={
            'X-Api-Key':    KEY,
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def http_get(path: str) -> dict:
    req = urllib.request.Request(
        f'{BASE}{path}',
        headers={'X-Api-Key': KEY},
        method='GET',
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def call_skill(skill_code: str, body: dict = None) -> dict:
    return http_post(f'/open/api/v1/call/{skill_code}', body or {})


# ---------------------------------------------------------------------------
# Skill API functions
# ---------------------------------------------------------------------------

def get_all_signal(chain: list = None) -> dict:
    """AI综合信号 — 3 credits"""
    return call_skill('get_all_signal', {
        'chain':  chain or ['3', '56']
    })


def get_hot_list(chain: list = None, token_group_id: int = None) -> dict:
    """热门榜单 — 1 credit"""
    body = {'chain': chain or ['3', '56']}
    if token_group_id is not None:
        body['tokenGroupId'] = token_group_id
    return call_skill('get_hot_list', body)



def get_kline_list(base: str, chain: str = None, interval_time: int = None,
                   end_time: int = None, page_size: int = None) -> dict:
    """K线数据 — 2 credits"""
    body = {'base': base}
    if chain:         body['chain']        = chain
    if interval_time: body['intervalTime'] = interval_time
    if end_time:      body['endTime']      = end_time
    if page_size:     body['pageSize']     = page_size
    return call_skill('get_kline_list', body)


def get_token_info(base: str, chain: list = None) -> dict:
    """Token详情 — 1 credit"""
    params = {'base': base}
    return call_skill('get_token_info', {'chain': chain or [3], 'params': params})


def get_token_signal(index_token_address: str, chain: str = None) -> dict:
    """Token历史信号 — 1 credit"""
    body = {'index_token_address': index_token_address}
    if chain: body['chain'] = chain
    return call_skill('get_token_signal', body)


def get_coin_balance(address: str, chain: int = None) -> dict:
    """账号Coin余额 — 1 credit"""
    body = {'address': address}
    if chain is not None: body['chain'] = chain
    return call_skill('get_coin_balance', body)


def get_wallet_positions(address: str, page_size: int = None, page_num: int = None,
                         sort_field: str = None, sort_direction: str = None,
                         hold_amount: str = None) -> dict:
    """仓位查询 — free, 1/s"""
    body = {'address': address}
    if page_size:      body['page_size']      = page_size
    if page_num:       body['page_num']       = page_num
    if sort_field:     body['sort_field']     = sort_field
    if sort_direction: body['sort_direction'] = sort_direction
    if hold_amount:    body['hold_amount']    = hold_amount
    return call_skill('get_wallet_positions', body)


def get_trade_logs(address: str, chain: str = None, page_size: int = None,
                   page_num: int = None) -> dict:
    """交易明细 — free, 1/s"""
    body = {'address': address}
    if chain:     body['chain']     = chain
    if page_size: body['page_size'] = page_size
    if page_num:  body['page_num']  = page_num
    return call_skill('get_trade_logs', body)


def get_limit_orders(address: str, status: int = None, page_size: int = None,
                     page_num: int = None) -> dict:
    """查询限价单 — free, 1/s"""
    body = {'address': address}
    if status is not None: body['status']    = status
    if page_size:          body['page_size'] = page_size
    if page_num:           body['page_num']  = page_num
    return call_skill('get_limit_orders', body)


def solana_swap(caller: str, event_type: str, action: dict) -> dict:
    """Solana交易  real funds"""
    action['timestamp'] = int(time.time() * 1000)
    action['key'] = event_type
    return call_skill('solana_swap', {'caller': caller, 'eventType': event_type,
                                      'action': action})


def bsc_swap(caller: str, event_type: str, action: dict) -> dict:
    """BSC交易  real funds"""
    action['timestamp'] = int(time.time() * 1000)
    action['key'] = event_type
    return call_skill('bsc_swap', {'caller': caller, 'eventType': event_type,
                                   'action': action})


def limit_order(caller: str, token_address: str, action: dict,
                chain_id: int = None, event_type: int = None,
                expired_at: int = None) -> dict:
    """挂限价单  real funds"""
    body = {'caller': caller, 'tokenAddress': token_address, 'action': action}
    if chain_id is not None:   body['chainId']   = chain_id
    if event_type is not None: body['eventType'] = event_type
    if expired_at is not None: body['expiredAt'] = expired_at
    return call_skill('limit_order', body)


def get_quota() -> dict:
    """查询配额余额"""
    return http_get('/open/api/v1/quota')


def get_stats() -> dict:
    """调用统计（近30天）"""
    return http_get('/open/api/v1/stats')


def get_keys() -> dict:
    """API Key 列表"""
    return http_get('/open/api/v1/keys')
