"""
LogEarn Open API — HTTP layer（统一客户端）

公共接口架构（见 logearn-web `docs/Telegram 和 Publick Skills/公共接口架构设计.md`）：
  - 所有 /open/api/v1/** 请求都带规范请求头：固定 UA（logearn-cli/<ver>）、X-Client-Instance、X-Request-Id
    （HMAC-SHA256(签名公钥, "v1|ts|rand|instance") 前 8 字节；签名密钥 = 该 API Key 自己登记的公钥，来自配置 LOGEARN_API_PUBLIC_KEY）。
  - 公开读（data）只要 X-Api-Key + 上面这些头；账户读（account）、交易（trade）另加 X-Signature
    （ECDSA P-256 对 §2.4 的 canonical 消息签名，输出 r‖s base64url；用 LOGEARN_API_SECRET 私钥，需要 cryptography 库）。
  - 不再回落任何硬编码默认值：缺 LOGEARN_API_KEY / LOGEARN_API_SECRET 时明确报错。

只用标准库即可完成公开读；账户读 / 交易用到 ECDSA，需要 `pip install cryptography`。
urllib.request 会自动读 https_proxy / HTTPS_PROXY 环境变量。
"""

import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
CLI_VERSION = "2.0.0"
USER_AGENT  = f"logearn-cli/{CLI_VERSION}"
TIMEOUT     = 8  # 秒，连接 + 读取总超时（urllib 单一 timeout）

_CONFIG_DIR     = os.path.join(os.path.expanduser('~'), '.config', 'logearn')


def _load_env_file(path: str):
    """把简单的 KEY=VALUE 行读进 os.environ（已存在的 key 不覆盖，实现优先级）。只用标准库。"""
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except FileNotFoundError:
        pass
    except Exception:
        pass


# 配置读取优先级：shell 环境变量 > 项目 .env（cwd）> 全局 ~/.config/logearn/.env（与 gmgn-cli 一致）。
# 先加载的不覆盖已有值，所以高优先级的源要先加载。
_load_env_file(os.path.join(os.getcwd(), '.env'))
_load_env_file(os.path.join(_CONFIG_DIR, '.env'))

BASE   = os.environ.get('LOGEARN_API_BASE', 'https://api.logearn.com/logearn').rstrip('/')
KEY    = os.environ.get('LOGEARN_API_KEY', '').strip()
SECRET = (os.environ.get('LOGEARN_API_SECRET', '') or '').replace('\\n', '\n').strip()

_INSTANCE_FILE  = os.path.join(_CONFIG_DIR, 'instance')

SIG_DOMAIN = "logearn/openapi/req/v1"

# 账户读 / 交易档：这些 skill 需要 X-Signature（与后端 SkillCode 分档一致）。其余为公开读，只需 API Key。
_ACCOUNT_SKILLS = {'get_coin_balance', 'get_wallet_positions', 'get_trade_logs', 'get_limit_orders'}
_TRADE_SKILLS   = {'solana_swap', 'bsc_swap', 'limit_order'}
_SIGNED_SKILLS  = _ACCOUNT_SKILLS | _TRADE_SKILLS


class ApiError(Exception):
    """网络 / 超时 / 鉴权失败；上层据此给用户「服务繁忙」或「请先配置」提示。"""


# ---------------------------------------------------------------------------
# 本机实例 id / 签名公钥缓存
# ---------------------------------------------------------------------------

def _instance_id() -> str:
    try:
        if os.path.exists(_INSTANCE_FILE):
            v = open(_INSTANCE_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    v = secrets.token_hex(8)
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        with open(_INSTANCE_FILE, 'w') as f:
            f.write(v)
        os.chmod(_INSTANCE_FILE, 0o600)
    except Exception:
        pass
    return v


def _client_key() -> str:
    """X-Request-Id 的 HMAC 密钥：该 API Key 自己登记的公钥（公开值，服务端本来就存着），来自配置 LOGEARN_API_PUBLIC_KEY
    （网页创建 API Key 时「复制配置」一并给出）。没有任何全站公钥，也就没有轮换问题。缺失直接报错，不再静默发出无签名的请求 id。"""
    k = _norm_key(os.environ.get('LOGEARN_API_PUBLIC_KEY', ''))
    if not k:
        raise ApiError('LOGEARN_API_PUBLIC_KEY 未配置：请在网页「API」页重新「复制配置」（含 LOGEARN_API_PUBLIC_KEY），写入 ~/.config/logearn/.env')
    return k


def _norm_key(k: str) -> str:
    k = (k or '').strip().lower()
    return k[2:] if k.startswith('0x') else k


def _request_id(instance: str) -> str:
    ts   = int(time.time() * 1000)
    rand = secrets.token_hex(6)                      # 12 hex
    key  = _client_key()
    mac  = hmac.new(key.encode('utf-8'), f'v1|{ts}|{rand}|{instance}'.encode('utf-8'), hashlib.sha256).digest()
    sig  = mac[:8].hex()
    return f'v1.{ts}.{rand}.{sig}'


# ---------------------------------------------------------------------------
# 签名（账户读 / 交易）
# ---------------------------------------------------------------------------

def _rfc3986(s: str) -> str:
    out = []
    for b in s.encode('utf-8'):
        c = chr(b)
        if c.isalnum() and b < 128 or c in '-_.~':
            out.append(c)
        else:
            out.append('%%%02X' % b)
    return ''.join(out)


def _canonical_query(query: str) -> str:
    if not query:
        return ''
    from urllib.parse import unquote_plus
    pairs = []
    for part in query.split('&'):
        if not part:
            continue
        k, _, v = part.partition('=')
        pairs.append(f'{_rfc3986(unquote_plus(k))}={_rfc3986(unquote_plus(v))}')
    pairs.sort()
    return '&'.join(pairs)


def _build_message(method: str, path: str, query: str, body: bytes, request_id: str, key_id: str) -> str:
    body_hash = hashlib.sha256(body or b'').hexdigest()
    return (f'{SIG_DOMAIN}\n{(method or "").upper()}\n{path or ""}\n'
            f'{_canonical_query(query)}\n{body_hash}\n{request_id or ""}\n{key_id or ""}')


def _sign(message: str) -> str:
    """ECDSA P-256 对 message 签名，返回 r‖s（各 32 字节）base64url。需要 LOGEARN_API_SECRET（PEM）与 cryptography 库。"""
    if not SECRET:
        raise ApiError('LOGEARN_API_SECRET 未配置：该命令需要 API Secret（创建 key 时只显示一次）；'
                       '已丢失请在网页删除这个 key 重新生成')
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils
    except Exception:
        raise ApiError('账户读 / 交易需要签名，请先安装：pip install cryptography')
    try:
        priv = serialization.load_pem_private_key(SECRET.encode('utf-8'), password=None)
        der = priv.sign(message.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
        r, s = asym_utils.decode_dss_signature(der)
        rs = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f'签名失败（API Secret 无效？）：{e}')
    import base64
    return base64.urlsafe_b64encode(rs).decode('ascii').rstrip('=')


# ---------------------------------------------------------------------------
# 统一请求
# ---------------------------------------------------------------------------

def _require_key():
    if not KEY:
        raise ApiError('LOGEARN_API_KEY 未配置：请到 https://logearn.com 创建 API Key，'
                       '把配置写入 ~/.config/logearn/.env（或 export）后重试')


def _http(method: str, path: str, body: dict = None, signed: bool = False) -> dict:
    _require_key()
    body_bytes = json.dumps(body or {}).encode('utf-8') if method == 'POST' else b''
    instance = _instance_id()
    request_id = _request_id(instance)
    headers = {
        'X-Api-Key':        KEY,
        'User-Agent':       USER_AGENT,
        'X-Client-Instance': instance,
        'X-Request-Id':     request_id,
        'X-Client-Version': CLI_VERSION,
        'X-Client-Os':      _os_name(),
    }
    if method == 'POST':
        headers['Content-Type'] = 'application/json'
    if signed:
        msg = _build_message(method, path, '', body_bytes, request_id, KEY)
        headers['X-Signature'] = _sign(msg)
    req = urllib.request.Request(f'{BASE}{path}', data=(body_bytes if method == 'POST' else None),
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:
            raise ApiError(f'HTTP {e.code} {method} {path}')
    except Exception as e:
        raise ApiError(f'request failed {method} {path}: {e}')


def _os_name() -> str:
    import platform
    s = platform.system().lower()
    return {'darwin': 'macos', 'windows': 'windows', 'linux': 'linux'}.get(s, 'other')


def call_skill(skill_code: str, body: dict = None) -> dict:
    return _http('POST', f'/open/api/v1/call/{skill_code}', body or {}, signed=skill_code in _SIGNED_SKILLS)


# ---------------------------------------------------------------------------
# 公开读
# ---------------------------------------------------------------------------

def get_native_price(chain: int = None) -> dict:
    """Native 币行情价格（公开读档 call/get_native_price）。
    chain=None → {"sol": "162.45", "bnb": "598.22"}；chain=3 → {"chain":3,"symbol":"SOL","price":"162.45"}。
    注意：取价失败直接抛 ApiError，**不再**回落到写死的 {3:86,56:630}（曾导致市值算错而不自知）。"""
    body = {}
    if chain is not None:
        body['chain'] = chain
    res = call_skill('get_native_price', body)
    if not isinstance(res, dict) or res.get('code') != 200 or res.get('data') is None:
        raise ApiError(f'{(res.get("msg") or res.get("message")) if isinstance(res, dict) else res}')
    return res['data']


def get_all_signal(chain: list = None) -> dict:
    """AI综合信号 — 3 credits"""
    return call_skill('get_all_signal', {'chain': chain or ['3', '56']})


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
    if chain:
        body['chain'] = chain
    return call_skill('get_token_signal', body)


def get_follow_tx(chain: list = None) -> dict:
    """关注地址交易 — 2 credits"""
    body = {}
    if chain is not None:
        body['chain'] = [str(c) for c in chain]
    return call_skill('get_follow_tx', body)


def filter_signal(chain: list = None, signal_type: str = None, signal_begin_time: int = None,
                  signal_end_time: int = None, min_signal_count: int = None,
                  max_signal_count: int = None, page_num: int = None, page_size: int = None) -> dict:
    """AI信号搜索 — 2 credits

    signal_begin_time 文档标注为选填，但服务端未传时返回 data=null，因此这里
    客户端兜底默认回退到 24 小时前，确保始终能拿到数据。
    """
    params = {
        'signal_begin_time': signal_begin_time if signal_begin_time is not None else int(time.time()) - 86400,
    }
    if signal_type is not None:      params['signal_type']      = signal_type
    if signal_end_time is not None:  params['signal_end_time']  = signal_end_time
    if min_signal_count is not None: params['min_signal_count'] = min_signal_count
    if max_signal_count is not None: params['max_signal_count'] = max_signal_count
    if page_num is not None:         params['page_num']         = page_num
    if page_size is not None:        params['page_size']        = page_size

    return call_skill('filter_signal', {'chain': chain or ['3'], 'params': params})


# ---------------------------------------------------------------------------
# 账户读（需 X-Signature）
# ---------------------------------------------------------------------------

def get_coin_balance(address: str = None, chain: int = None) -> dict:
    """账号Coin余额 — 1 credit（账户读，需签名）"""
    body = {}
    if chain is not None:   body['chain']   = chain
    if address is not None: body['address'] = address
    return call_skill('get_coin_balance', body)


def get_wallet_positions(address: str = None, page_size: int = None, page_num: int = None,
                         sort_field: str = None, sort_direction: str = None,
                         hold_amount: str = None) -> dict:
    """仓位查询（账户读，需签名）"""
    body = {}
    if address is not None: body['address'] = address
    if page_size:      body['page_size']      = page_size
    if page_num:       body['page_num']       = page_num
    if sort_field:     body['sort_field']     = sort_field
    if sort_direction: body['sort_direction'] = sort_direction
    if hold_amount:    body['hold_amount']    = hold_amount
    return call_skill('get_wallet_positions', body)


def get_trade_logs(address: str = None, chain: str = None, page_size: int = None,
                   page_num: int = None) -> dict:
    """交易明细（账户读，需签名）"""
    body = {}
    if address is not None: body['address'] = address
    if chain:     body['chain']     = chain
    if page_size: body['page_size'] = page_size
    if page_num:  body['page_num']  = page_num
    return call_skill('get_trade_logs', body)


def get_limit_orders(address: str = None, status: int = None, page_size: int = None,
                     page_num: int = None) -> dict:
    """查询限价单（账户读，需签名）"""
    body = {}
    if address is not None: body['address'] = address
    if status is not None:  body['status']    = status
    if page_size:           body['page_size'] = page_size
    if page_num:            body['page_num']  = page_num
    return call_skill('get_limit_orders', body)


# ---------------------------------------------------------------------------
# 交易（需 X-Signature；real funds）
# ---------------------------------------------------------------------------

TRADE_INTENT_DOMAIN = 'logearn/tee/trade-intent/v1|'


def _canonical_json(v) -> str:
    """与前端 canonicalJson / TEE 一致：键 ASCII 升序、无空白、仅安全整数。"""
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        if abs(v) > 2 ** 53 - 1:
            raise ValueError('canonical JSON: only safe integers allowed (use decimal strings)')
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return '[' + ','.join(_canonical_json(x) for x in v) + ']'
    if isinstance(v, dict):
        keys = sorted(k for k in v if v[k] is not None or True)
        return '{' + ','.join(json.dumps(k) + ':' + _canonical_json(v[k]) for k in keys) + '}'
    raise ValueError('canonical JSON: unsupported value')


def build_trade_auth(*, chain_id: int, wallet: str, token_in: str, token_out: str, amount_in: str,
                     min_amount_out: str, amount_usd: str = '0', solana: bool = False) -> dict:
    """本地签交易意图（TradeIntent v2，10 分钟有效），返回 params.teeAuth = {clientId, intent, intentSignature}。
    需要 LOGEARN_API_SECRET（私钥）+ LOGEARN_CLIENT_ID（创建 key 时登记的 br-… 设备 id）+ LOGEARN_ACCOUNT_ID。
    min_amount_out 必须由调用方按报价与滑点算好（最小单位整数字符串，>0），TEE 会完整解码交易校验，不会信任这里。"""
    client_id = os.environ.get('LOGEARN_CLIENT_ID', '').strip()
    account_id = os.environ.get('LOGEARN_ACCOUNT_ID', '').strip()
    if not client_id or not account_id:
        raise ApiError('缺少 LOGEARN_CLIENT_ID / LOGEARN_ACCOUNT_ID：请用网页「复制配置」得到完整配置块')
    if not str(min_amount_out).isdigit() or int(min_amount_out) <= 0:
        raise ApiError('min_amount_out 必须是 >0 的最小单位整数')
    addr = (lambda x: str(x).strip()) if solana else (lambda x: str(x).lower())
    ts = int(time.time())
    intent = {
        'v': 2, 'kind': 'TRADE', 'min_amount_out': str(min_amount_out),
        'account_id': int(account_id), 'client_id': client_id, 'chain_id': int(chain_id),
        'wallet': addr(wallet), 'token_in': addr(token_in), 'token_out': addr(token_out),
        'amount_in': str(amount_in), 'amount_usd': str(amount_usd or '0'),
        'ts': ts, 'expires_at': ts + 600, 'nonce': 'tr-' + secrets.token_hex(16),
    }
    if solana:
        intent['chain_family'] = 'solana'
    import base64
    sig = _sign_raw((TRADE_INTENT_DOMAIN + _canonical_json(intent)).encode('utf-8'))
    return {'clientId': client_id, 'intent': intent, 'intentSignature': base64.b64encode(sig).decode('ascii')}


def _sign_raw(data: bytes) -> bytes:
    """ECDSA P-256 / SHA-256，返回 r‖s 原始 64 字节。"""
    if not SECRET:
        raise ApiError('LOGEARN_API_SECRET 未配置')
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils
    except Exception:
        raise ApiError('交易需要签名，请先安装：pip install cryptography')
    priv = serialization.load_pem_private_key(SECRET.encode('utf-8'), password=None)
    r, s = asym_utils.decode_dss_signature(priv.sign(data, ec.ECDSA(hashes.SHA256())))
    return r.to_bytes(32, 'big') + s.to_bytes(32, 'big')


_NATIVE = {3: {'so11111111111111111111111111111111111111112', 'native'},
           56: {'0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c', '0x0000000000000000000000000000000000000000', 'native'}}
_NATIVE_DECIMALS = {3: 9, 56: 18}
DEFAULT_SLIPPAGE = 0.5


def _find_token(node):
    """在 get_token_info 的嵌套返回里找代币字典：带 decimals、total_supply，且有 main_pool 或 latest_price。"""
    if isinstance(node, dict):
        if node.get('decimals') is not None and node.get('total_supply') is not None \
                and (node.get('main_pool') or node.get('latest_price') is not None):
            return node
        for v in node.values():
            r = _find_token(v)
            if r:
                return r
    elif isinstance(node, list):
        for v in node:
            r = _find_token(v)
            if r:
                return r
    return None


def _token_price_usd(info: dict, native_usd, native_decimals: int):
    """单个 token 的 USD 价，口径同 fmt_token_info：优先 main_pool.mcp（USD 市值）/ 归一化总量，
    否则 main_pool.last_price（原生币计价，按精度差换算）× 原生币 USD 价。取不到返回 0。"""
    from decimal import Decimal
    tdec = int(info['decimals'])
    supply = Decimal(str(info['total_supply'])) / Decimal(10) ** tdec          # total_supply 是未归一化的原始值
    mp = info.get('main_pool')
    if isinstance(mp, str):
        try: mp = json.loads(mp)
        except Exception: mp = {}
    mp = mp if isinstance(mp, dict) else {}
    mcp = Decimal(str(mp.get('mcp') or 0))
    if mcp > 0 and supply > 0:
        return mcp / supply
    last = Decimal(str(mp.get('last_price') or info.get('latest_price') or 0))
    scale = Decimal(10) ** (tdec - native_decimals)
    return last * scale * native_usd


def estimate_min_out(*, chain_id: int, token_in: str, token_out: str, amount_in: str, slippage: float = DEFAULT_SLIPPAGE) -> dict:
    """用 token 详情（main_pool 的市值 / 价格、总量、精度）与 native 价格估算 min_amount_out，口径与网页一致：
    预期获得量 × (1 − 滑点) × 0.5（防灾下限；用户滑点本身由后端精确上链）。默认滑点 50%。
    返回 {min_amount_out, amount_usd, expected_out}；估不出（取不到价格 / 金额太小）抛 ApiError，不盲签。"""
    from decimal import Decimal
    chain_id = int(chain_id)
    if not (0 <= slippage < 1):
        raise ApiError('滑点必须在 [0,1) 之间，如 0.5 = 50%')
    nat = _NATIVE.get(chain_id)
    if nat is None:
        raise ApiError(f'不支持的链: {chain_id}')
    buying = str(token_in).lower() in nat
    token = token_out if buying else token_in
    info = _find_token((get_token_info(base=token, chain=[chain_id]) or {}).get('data'))
    if not info:
        raise ApiError('取不到该代币的详情（价格），无法估算最少获得量')
    nres = get_native_price(chain_id)
    native_usd = Decimal(str(nres.get('price') or 0))
    tdec = int(info['decimals']); ndec = _NATIVE_DECIMALS[chain_id]
    price_usd = _token_price_usd(info, native_usd, ndec)                    # 单个 token 的 USD 价
    if native_usd <= 0 or price_usd <= 0:
        raise ApiError('价格数据不可用，无法估算最少获得量')
    amt = Decimal(str(amount_in))
    if buying:
        native_amt = amt / Decimal(10) ** ndec
        usd = native_amt * native_usd
        out = usd / price_usd * Decimal(10) ** tdec
    else:
        tokens = amt / Decimal(10) ** tdec
        usd = tokens * price_usd
        out = usd / native_usd * Decimal(10) ** ndec
    min_out = int(out * (Decimal(1) - Decimal(str(slippage))) * Decimal('0.5'))
    if min_out <= 0:
        raise ApiError('金额太小，估算的最少获得量为 0')
    return {'min_amount_out': str(min_out), 'amount_usd': format(usd, 'f'), 'expected_out': str(int(out))}


def solana_swap(caller: str, event_type: str, action: dict, tee_auth: dict = None) -> dict:
    """Solana交易  real funds（需签名 + 交易意图 tee_auth，见 build_trade_auth）"""
    action['timestamp'] = int(time.time() * 1000)
    action['key'] = event_type
    return call_skill('solana_swap', {'caller': caller, 'eventType': event_type, 'action': action, 'teeAuth': tee_auth})


def bsc_swap(caller: str, event_type: str, action: dict, tee_auth: dict = None) -> dict:
    """BSC交易  real funds（需签名 + 交易意图 tee_auth，见 build_trade_auth）"""
    action['timestamp'] = int(time.time() * 1000)
    action['key'] = event_type
    return call_skill('bsc_swap', {'caller': caller, 'eventType': event_type, 'action': action, 'teeAuth': tee_auth})


LIMIT_BUY_DOMAIN = 'logearn/tee/limit-buy/v1|'
LIMIT_BUY_TTL = 7 * 86400


def build_limit_buy_auth(*, chain_id: int, wallet: str, token_in: str, token_out: str, amount_in: str) -> dict:
    """限价买单授权（与网页 buildLimitBuyAuth 同口径）：钱包、两种币、金额、7 天有效，本地用 API Secret 签名。
    返回 params.teeOrderAuth = {clientId, auth, authSignature}。卖单不需要授权。"""
    import base64
    client_id = os.environ.get('LOGEARN_CLIENT_ID', '').strip()
    account_id = os.environ.get('LOGEARN_ACCOUNT_ID', '').strip()
    if not client_id or not account_id:
        raise ApiError('缺少 LOGEARN_CLIENT_ID / LOGEARN_ACCOUNT_ID：请用网页「复制配置」得到完整配置块')
    solana = int(chain_id) == 3
    addr = (lambda x: str(x).strip()) if solana else (lambda x: str(x).lower())
    ts = int(time.time())
    auth = {
        'v': 1, 'kind': 'LIMIT_BUY', 'account_id': int(account_id), 'client_id': client_id, 'chain_id': int(chain_id),
        'wallet': addr(wallet), 'token_in': addr(token_in), 'token_out': addr(token_out),
        'amount_in': str(amount_in), 'order_id': 'lo-' + secrets.token_hex(12), 'ts': ts, 'expires_at': ts + LIMIT_BUY_TTL,
    }
    if solana:
        auth['chain_family'] = 'solana'
    sig = _sign_raw((LIMIT_BUY_DOMAIN + _canonical_json(auth)).encode('utf-8'))
    return {'clientId': client_id, 'auth': auth, 'authSignature': base64.b64encode(sig).decode('ascii')}


def limit_order(caller: str, token_address: str, action: dict,
                chain_id: int = None, event_type: int = None,
                expired_at: int = None) -> dict:
    """挂限价单  real funds（需签名）。买单（event_type=1，默认）自动本地签 LIMIT_BUY 授权；卖单不需要。"""
    body = {'caller': caller, 'tokenAddress': token_address, 'action': action}
    if chain_id is not None:   body['chainId']   = chain_id
    if event_type is not None: body['eventType'] = event_type
    if expired_at is not None: body['expiredAt'] = expired_at
    if (event_type if event_type is not None else 1) == 1:
        for k in ('tokenIn', 'tokenOut', 'amountIn'):
            if not action.get(k):
                raise ApiError(f'限价买单的 action 缺少 {k}（授权要绑定钱包、两种币和金额）')
        body['teeOrderAuth'] = build_limit_buy_auth(
            chain_id=chain_id if chain_id is not None else 3, wallet=caller,
            token_in=action.get('tokenIn'), token_out=action.get('tokenOut'), amount_in=action.get('amountIn'))
    return call_skill('limit_order', body)


# ---------------------------------------------------------------------------
# 元信息（X-Api-Key，不需要 X-Signature）
# ---------------------------------------------------------------------------

def get_quota() -> dict:
    """查询配额余额"""
    return _http('GET', '/open/api/v1/quota')


def get_stats() -> dict:
    """调用统计（近30天）"""
    return _http('GET', '/open/api/v1/stats')


def get_keys() -> dict:
    """API Key 列表"""
    return _http('GET', '/open/api/v1/keys')
