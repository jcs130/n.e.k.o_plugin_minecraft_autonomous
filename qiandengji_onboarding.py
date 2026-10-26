"""Local file-picker and invitation form storage; never starts a game."""

import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .qiandengji_account import (
    NAME,
    AccountError,
    _private_write_same,
    configured_identity,
    parse_identity,
    private_path,
    read_identity,
)


def account_root():
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')
    else:
        base = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
    root = base / 'Neko' / 'minecraft-autonomous' / 'accounts'
    private_path(str(root / 'selected.json'), missing=True)
    return root


def _selection():
    path = private_path(str(account_root() / 'selected.json'), missing=True)
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text('utf-8'))
        if not isinstance(value, dict) or not NAME.fullmatch(value.get('username', '')):
            raise ValueError()
        private_path(value['identity_file'], missing=True)
        if value.get('invite_url_file'):
            private_path(value['invite_url_file'])
        return value
    except (KeyError, TypeError, ValueError, OSError):
        raise AccountError('private_file_unavailable') from None


def _select(path, username, invite_path=None):
    target = private_path(str(account_root() / 'selected.json'), missing=True)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    value = {'identity_file': str(path), 'username': username}
    if invite_path:
        value['invite_url_file'] = str(invite_path)
    temporary = target.with_name('selection-' + uuid.uuid4().hex + '.tmp')
    _private_write_same(temporary, (json.dumps(value) + '\n').encode('utf-8'))
    os.replace(temporary, target)


def selected_identity():
    value = _selection()
    return Path(value['identity_file']) if value else None


def public_selection(raw):
    try:
        configured = configured_identity(raw)
        path = Path(configured) if configured else selected_identity()
        if path is None:
            return {'selected': False}
        if not path.exists():
            return {'selected': True, 'username': _selection()['username'], 'imported': False}
        _, identity = read_identity(str(path))
        return {'selected': True, 'username': identity['username'], 'imported': bool(configured)}
    except (OSError, ValueError, KeyError):
        return {'selected': False, 'unavailable': True}


def store_identity(text):
    identity = parse_identity(text)
    path = private_path(str(account_root() / identity['clientId'] / 'identity.json'), missing=True)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _private_write_same(path, (json.dumps(identity, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    _select(path, identity['username'])
    return path


def prepare_invitation(username, invitation):
    if not isinstance(username, str) or not NAME.fullmatch(username):
        raise AccountError('invalid_agent_name')
    try:
        if not isinstance(invitation, str) or len(invitation) > 512:
            raise ValueError()
        url = urlsplit(invitation.strip())
        params = parse_qs(url.fragment, strict_parsing=True)
        if (url.scheme != 'https' or url.netloc != 'mc.kangqiang.site' or url.path != '/join' or url.query
                or set(params) != {'invite'} or len(params['invite']) != 1
                or not re.fullmatch(r'qdi_[A-Za-z0-9_-]{43}', params['invite'][0])):
            raise ValueError()
    except ValueError:
        raise AccountError('invalid_private_invitation') from None
    previous = _selection()
    if previous:
        if previous['username'] != username or not previous.get('invite_url_file'):
            raise AccountError('identity_exists_query_status')
        path = Path(previous['identity_file'])
        invitation_path = Path(previous['invite_url_file'])
    else:
        directory = account_root() / uuid.uuid4().hex
        path = private_path(str(directory / 'identity.json'), missing=True)
        invitation_path = private_path(str(directory / 'invite.private'), missing=True)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    _private_write_same(invitation_path, (invitation.strip() + '\n').encode('utf-8'))
    _select(path, username, invitation_path)
    return path, invitation_path
