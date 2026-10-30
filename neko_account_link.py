"""Private, resumable Qiandengji device grant; never reads Neko's OAuth tokens."""

import hashlib
import json
import os
import secrets
import tempfile
import uuid
from urllib.parse import urlsplit

import httpx

from .qiandengji_account import ADDRESS, NAME, PORTAL, VERSION, AccountError, _private_write_same, private_path
from .qiandengji_onboarding import account_root

IMMUTABLE = ('clientId', 'clientSecret', 'requestId', 'username', 'gamePassword')
PHASES = {'new', 'authorization_required', 'approved', 'pending', 'unknown', 'ready', 'failed', 'configured', 'expired'}


def link_path():
    return private_path(str(account_root() / 'neko-plugin' / 'identity.json'), missing=True)


def load_link():
    path = link_path()
    if not path.exists():
        return None
    try:
        value = json.loads(private_path(str(path)).read_text('utf-8'))
        if not isinstance(value, dict) or value.get('schema') != 'qiandengji-neko-plugin/v1' or value.get('portal') != PORTAL:
            raise ValueError()
        for key in ('clientId', 'requestId'):
            if str(uuid.UUID(value[key])) != value[key]:
                raise ValueError()
        if not NAME.fullmatch(value['username']) or value.get('phase') not in PHASES:
            raise ValueError()
        for key in ('clientSecret', 'gamePassword'):
            if not isinstance(value[key], str) or not 32 <= len(value[key]) <= 64 or not all(c.isascii() and (c.isalnum() or c in '_-') for c in value[key]):
                raise ValueError()
        if len(value['clientSecret']) != 43 or any(type(value.get(k)) is not bool for k in ('request_sent', 'activation_sent', 'configuration_sent', 'renew_sent')):
            raise ValueError()
        return value
    except (OSError, ValueError, KeyError, TypeError):
        raise AccountError('neko_link_private_material_unavailable') from None


def save_link(value):
    path = link_path()
    old = load_link()
    if old and any(value.get(k) != old[k] for k in IMMUTABLE):
        raise AccountError('neko_link_identity_conflict')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = (json.dumps(value) + '\n').encode('utf-8')
    if old is None:
        _private_write_same(path, encoded)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.link-', delete=False) as handle:
            temporary = handle.name
            if os.name != 'nt':
                os.fchmod(handle.fileno(), 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def ensure_link(username=''):
    old = load_link()
    if old:
        if username and username != old['username']:
            raise AccountError('neko_link_identity_conflict')
        return old
    username = username or 'ag_Neko' + uuid.uuid4().hex[:8]
    if not NAME.fullmatch(username):
        raise AccountError('invalid_agent_name')
    value = {'schema': 'qiandengji-neko-plugin/v1', 'portal': PORTAL, 'clientId': str(uuid.uuid4()),
             'clientSecret': secrets.token_urlsafe(32), 'requestId': str(uuid.uuid4()), 'username': username,
             'gamePassword': secrets.token_urlsafe(24), 'request_sent': False, 'activation_sent': False, 'configuration_sent': False, 'renew_sent': False, 'phase': 'new'}
    save_link(value)
    return value


def public_link(value):
    if not value:
        return {'selected': False, 'phase': 'idle'}
    result = {'selected': True, 'username': value['username'], 'phase': value['phase'], 'configured': value['phase'] == 'configured'}
    if value['phase'] == 'expired':
        result['renewable'] = value.get('renewable') is True and not value['activation_sent'] and not value['renew_sent']
    if value['request_sent']:
        result['verification_url'] = PORTAL + '/join?neko_request=' + value['clientId']
    return result


def expected_uuid(username):
    return str(uuid.UUID(bytes=hashlib.md5(('OfflinePlayer:' + username).encode()).digest(), version=3))


async def request(client, method, path, value=None, *, body=None):
    headers = {'Authorization': 'Bearer qnp_' + value['clientSecret']} if value else {}
    try:
        async with client.stream(method, PORTAL + path, headers=headers, json=body) as response:
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > 32768:
                    raise ValueError()
            if response.status_code in (404, 503) and path == '/api/v1/auth/neko':
                return {'available': False}
            result = json.loads(data)
            if not isinstance(result, dict):
                raise ValueError()
            if response.status_code >= 300:
                raise ValueError()
            if value and (result.get('clientId') != value['clientId'] or result.get('username') != value['username']):
                raise ValueError()
            return result
    except (httpx.HTTPError, ValueError, KeyError, UnicodeError):
        raise AccountError('neko_link_result_unconfirmed') from None


async def advance_link(client, value, *, renew=False):
    """Only status is retried. Both admitting POSTs are durably marked first."""
    prefix = '/api/v1/neko-plugin/requests'
    if not value['request_sent']:
        capability = await request(client, 'GET', '/api/v1/auth/neko')
        if capability.get('available') is not True:
            return {**public_link(value), 'phase': 'provider_not_configured', 'configured': False}
        value['request_sent'] = True
        save_link(value)
        result = await request(client, 'POST', prefix, body={k: value[k] for k in ('clientId', 'clientSecret', 'username', 'requestId')})
        parsed = urlsplit(result.get('verificationUrl', ''))
        if parsed.geturl() != PORTAL + '/join?neko_request=' + value['clientId']:
            raise AccountError('neko_link_response_mismatch')
    result = await request(client, 'GET', prefix + '/' + value['clientId'] + '/status', value)
    phase = result.get('phase')
    if phase == 'expired' and renew and result.get('renewable') is True and not value['activation_sent'] and not value['renew_sent']:
        value['renew_sent'] = True
        save_link(value)
        result = await request(client, 'POST', prefix + '/' + value['clientId'] + '/renew', value)
        phase = result.get('phase')
    if phase != 'expired':
        value['renew_sent'] = False
    elif value['renew_sent']:
        phase = 'unknown'
    if phase == 'approved' and not value['activation_sent']:
        value['activation_sent'] = True
        save_link(value)
        result = await request(client, 'POST', prefix + '/' + value['clientId'] + '/activate', value,
                               body={k: value[k] for k in ('requestId', 'username', 'gamePassword')})
        phase = result.get('phase')
    if phase == 'approved' and value['activation_sent']:
        phase = 'unknown'
    if phase not in PHASES:
        raise AccountError('neko_link_response_mismatch')
    if phase == 'ready' and (result.get('ready') is not True or result.get('gameAccountCreated') is not True
                             or result.get('gameAddress') != ADDRESS or result.get('gameVersion') != VERSION
                             or result.get('playerUuid') != expected_uuid(value['username'])):
        raise AccountError('neko_link_response_mismatch')
    value['phase'] = phase
    value['renewable'] = result.get('renewable') is True
    save_link(value)
    return public_link(value)
