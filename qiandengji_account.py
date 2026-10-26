"""Explicit optional website-account adapter; never owns a game connection."""

import asyncio
import hashlib
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PORTAL = "https://mc.kangqiang.site"
ADDRESS = "micro.kangqiang.site:25702"
VERSION = "1.21.1"
HELPER = Path(__file__).parent / "assets/server-extensions/qiandengji/access/agent-register.mjs"
HELPER_SHA256 = "cfa9733c093a27093100b3c08b21de0727af24f486561a07bf5a7868d49ca5cd"
NAME = re.compile(r"ag_[A-Za-z0-9_]{1,13}\Z")
STATES = {"ready", "pending", "unknown", "not_created", "awaiting_game_bridge", "authenticated", "registered", "revoked", "expired"}


class AccountError(ValueError):
    """Only locally defined codes cross the host boundary, never API text."""


def start_failure(error):
    messages = {
        'private_absolute_file_required': '身份文件路径无效。请在“千灯纪网站账户接入”选择原私有身份文件。',
        'identity_outside_plugin_required': '身份文件须放在插件目录以外的本人私有目录，升级不会搬运凭据。',
        'private_file_unavailable': '原身份文件或登录文件不可读。请检查文件是否移动及当前用户权限。',
        'invalid_private_identity': '身份文件格式不匹配。请使用官网生成的原 Agent 身份文件，不能用登录配置或网站密码代替。',
        'imported_account_connection_mismatch': '连接与已导入身份不匹配。请核对服务器、端口、原昵称和游戏版本，或重新导入原身份连接。',
        'private_login_mismatch': '私有登录配置与该账号不匹配。请在“服务器登录密码”保存原账号的 /login 密码，或重新导入原身份。',
        'private_identity_changed': '核对期间身份文件发生变化。请保留原文件，重新查询原身份状态。',
        'account_result_unknown_query_status': '官网身份查询未确认。请检查网络和 Node 是否可用，再查询原身份状态；不要重新注册。',
        'official_helper_integrity_failed': '随包接入工具校验失败。请重新安装完整的正式插件包。',
        'account_response_mismatch_query_status': '官网返回的角色或地址与原身份不匹配。请查询原身份状态，未启动游戏。',
        'account_not_ready_query_status': '官网尚未确认原游戏账号 ready。请查询原身份状态；pending/unknown 时等待原请求结果，未启动游戏。',
    }
    reason = str(error) if str(error) in messages else 'account_check_failed'
    return {'code': 'qiandengji_account_not_ready', 'reason': reason,
            'message': messages.get(reason, '千灯纪身份核对未完成，请查询原身份状态。未启动游戏。')}


def private_path(value, *, missing=False):
    if not isinstance(value, str) or not value or len(value) > 4096 or any(ord(c) < 32 for c in value):
        raise AccountError("private_absolute_file_required")
    path = Path(value).expanduser()
    if not path.is_absolute() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise AccountError("private_absolute_file_required")
    path = path.resolve()
    # Keep user-created secrets out of the distributable source tree.
    if path.is_relative_to(Path(__file__).parent.resolve()):
        raise AccountError("identity_outside_plugin_required")
    if not path.exists() and missing:
        return path
    try:
        stat = path.stat()
        if not path.is_file() or not 0 < stat.st_size <= 16384 or (os.name != "nt" and stat.st_mode & 0o077):
            raise AccountError("private_file_unavailable")
    except OSError:
        raise AccountError("private_file_unavailable") from None
    return path


def configured_identity(raw):
    section = raw.get("qiandengji", {})
    if not isinstance(section, dict) or set(section) - {"identity_file"}:
        raise AccountError("invalid_qiandengji_settings")
    value = section.get("identity_file", "")
    if value:
        private_path(value, missing=True)
    elif value != "":
        raise AccountError("private_absolute_file_required")
    return value


def parse_identity(text):
    try:
        if not isinstance(text, str) or len(text.encode('utf-8')) > 16384:
            raise ValueError()
        data = json.loads(text.lstrip('\ufeff'))
        if not isinstance(data, dict) or data.get("schemaVersion") != 1 or data.get("portal") != PORTAL:
            raise ValueError()
        if not NAME.fullmatch(data.get("username", "")) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", data.get("clientSecret", "")):
            raise ValueError()
        for key in ("clientId", "gameRequestId"):
            if str(uuid.UUID(data[key])) != data[key].lower():
                raise ValueError()
        password = data.get("gamePassword")
        if not isinstance(password, str) or not 6 <= len(password) <= 64 or re.search(r"\s|[\x00-\x1f\x7f]", password):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise AccountError("invalid_private_identity") from None
    return data


def read_identity(value):
    path = private_path(value)
    try:
        return path, parse_identity(path.read_text("utf-8-sig"))
    except (OSError, UnicodeError):
        raise AccountError("invalid_private_identity") from None


def public_result(result):
    """Do not forward API messages, nested data, arbitrary strings or credentials."""
    state = result.get("state") if isinstance(result, dict) else None
    state = state if state in STATES else "unknown"
    username = result.get("username") if isinstance(result, dict) else None
    username = username if isinstance(username, str) and NAME.fullmatch(username) else None
    created = isinstance(result, dict) and result.get("gameAccountCreated") is True
    return {"state": state, "username": username, "game_account_created": created,
            "ready": state == "ready" and created, "game_address": ADDRESS,
            "game_version": VERSION, "game_connection_started": False}


def require_ready_result(result, identity):
    if (not isinstance(result, dict) or result.get("state") != "ready" or result.get("gameAccountCreated") is not True
            or result.get("username") != identity["username"] or result.get("gameAddress") != ADDRESS
            or result.get("gameVersion") != VERSION):
        raise AccountError("account_not_ready_query_status")


async def _invoke(args, *, node="node"):
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA256:
        raise AccountError("official_helper_integrity_failed")
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            node, str(HELPER), *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}))
        out, err = await asyncio.wait_for(process.communicate(), timeout=70)
        if len(out) > 65536 or len(err) > 65536:
            raise AccountError("account_result_unknown_query_status")
        if process.returncode not in {0, 2}:
            raise AccountError("account_result_unknown_query_status")
        value = json.loads(out.decode("utf-8").strip())
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (OSError, UnicodeError, ValueError, asyncio.TimeoutError) as error:
        if process is not None and process.returncode is None:
            process.kill()
            await process.communicate()
        if isinstance(error, AccountError):
            raise
        raise AccountError("account_result_unknown_query_status") from None
    except asyncio.CancelledError:
        if process is not None and process.returncode is None:
            process.kill()
            await process.communicate()
        raise


async def account_action(action, identity_file, *, username="", invite_url_file="", node="node"):
    if action not in {"register", "status", "activate"}:
        raise AccountError("invalid_account_action")
    if action == "register":
        path = private_path(identity_file, missing=True)
        if path.exists():
            raise AccountError("identity_exists_query_status")
        if not isinstance(username, str) or not NAME.fullmatch(username):
            raise AccountError("invalid_agent_name")
        invitation = private_path(invite_url_file)
        try:
            url = urlsplit(invitation.read_text("utf-8-sig").strip())
            params = parse_qs(url.fragment, strict_parsing=True)
            if (url.scheme != "https" or url.netloc != "mc.kangqiang.site" or url.path != "/join" or url.query
                    or set(params) != {"invite"} or len(params["invite"]) != 1
                    or not re.fullmatch(r"qdi_[A-Za-z0-9_-]{43}", params["invite"][0])):
                raise ValueError()
        except (OSError, ValueError):
            raise AccountError("invalid_private_invitation") from None
        args = [action, "--username", username, "--invite-url-file", str(invitation), "--identity-file", str(path)]
    else:
        path, _ = read_identity(identity_file)
        args = [action, "--identity-file", str(path)]
    result = await _invoke(args, node=node)
    _, identity = read_identity(str(path))
    if result.get("username") != identity["username"]:
        raise AccountError("account_response_mismatch_query_status")
    summary = public_result(result)
    summary["ready"] = (summary["ready"] and result.get("gameAddress") == ADDRESS and result.get("gameVersion") == VERSION)
    return summary


def _private_write_same(path, contents):
    if path.exists():
        private_path(str(path))
        if path.read_bytes() != contents:
            raise AccountError("private_material_conflict")
        return
    try:
        with path.open("xb") as handle:
            if os.name != "nt":
                os.fchmod(handle.fileno(), 0o600)
            handle.write(contents)
    except FileExistsError:
        if path.read_bytes() != contents:
            raise AccountError("private_material_conflict") from None


def login_material(identity):
    return {"enabled": True, "accounts": [{"server": ADDRESS, "username": identity["username"],
            "credentialFile": "game-password.private", "credentialFormat": "file", "command": "login"}]}


def prepare_login(source, identity, directory):
    # No alternate password, registration command or controller is introduced.
    _, original = read_identity(str(source))
    if any(original[key] != identity[key] for key in ("username", "clientId", "gameRequestId", "gamePassword")):
        raise AccountError("private_identity_changed")
    directory = Path(directory)
    # SDK data directories can live inside the installed plugin package.
    if directory.resolve().is_relative_to(Path(__file__).parent.resolve()):
        directory = Path(source).resolve().parent
    directory = directory / "qiandengji" / identity["clientId"]
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    private_path(str(directory / "game-password.private"), missing=True)
    secret = (identity["gamePassword"] + "\n").encode("utf-8")
    config = (json.dumps(login_material(identity), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _private_write_same(directory / "game-password.private", secret)
    _private_write_same(directory / "login.json", config)
    return directory / "login.json"


async def preflight(raw, settings, *, data_root=None):
    value = configured_identity(raw)
    if not value:
        return
    _, identity = read_identity(value)
    if (settings.host != "micro.kangqiang.site" or settings.port != 25702 or settings.username != identity["username"]
            or settings.auth != "offline" or settings.version != VERSION):
        raise AccountError("imported_account_connection_mismatch")
    # The password form creates a scoped, managed login file (DPAPI on Windows).
    # It is a valid alternative to the original helper's plaintext layout.
    # Fresh website readiness and exact identity/connection checks still apply.
    managed = False
    if data_root is not None:
        from agent_mc_autonomy.server_login import public_login
        state = public_login(data_root, settings)
        managed = state['managed'] and state['configured']
    login = private_path(settings.login_config_file)
    try:
        config = json.loads(login.read_text("utf-8"))
        if not managed:
            if config != login_material(identity):
                raise ValueError()
            secret = private_path(str(login.parent / "game-password.private"))
            if secret.read_text("utf-8") != identity["gamePassword"] + "\n":
                raise ValueError()
    except (OSError, ValueError):
        raise AccountError("private_login_mismatch") from None
    result = await _invoke(["status", "--identity-file", str(Path(value))], node=settings.node)
    require_ready_result(result, identity)
    _, latest = read_identity(value)
    if any(latest[key] != identity[key] for key in ("username", "clientId", "gameRequestId", "gamePassword")):
        raise AccountError("private_identity_changed")
