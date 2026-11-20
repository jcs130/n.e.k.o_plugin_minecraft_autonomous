"""Official website pairing for the resident mode of the N.E.K.O. adapter."""

# Adapted from jcs130/minecraft-ai-friend resident 0.3.2 (bf913815), MIT.

import asyncio
import json
import os
import re
import secrets
import tempfile
import time
import webbrowser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID, uuid4

from plugin.sdk.plugin import Err, Ok, plugin_entry, ui

PORTAL = "https://mc.kangqiang.site"
SECRET = {"type": "string", "writeOnly": True}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, payload=None, token=None, *, timeout=8):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout) as response:
        raw = response.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError("resident_reply_too_large")
        return json.loads(raw)


def origin_of(value):
    parsed = urlsplit(value)
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname == "127.0.0.1")):
        raise ValueError("invalid_portal_origin")
    return f"{parsed.scheme}://{parsed.netloc}"


def read_session(session, origin=None):
    endpoint = session["endpoint"]
    actual_origin = origin_of(endpoint)
    route = re.fullmatch(r"/api/v1/resident-turns/([a-z][a-z0-9_-]{1,31})", urlsplit(endpoint).path)
    resident = session["resident"]
    character_id = resident["characterId"]
    if ((origin and actual_origin != origin)
            or not route or resident["id"] != route[1]
            or not isinstance(character_id, str) or str(UUID(character_id)) != character_id
            or resident["bodyKind"] not in ("maid", "numen")
            or not isinstance(resident["name"], str) or not resident["name"].strip()
            or not re.fullmatch(r"rdt_[A-Za-z0-9_-]{43}", session["token"])):
        raise ValueError("invalid_session")
    return session


def write_resident_state(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            tmp = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        tmp.replace(path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


class ResidentConnection:
    authorization = None
    browser_login = None
    catalog = None
    waiting = None
    draft = None
    _website_player_grant = None

    @staticmethod
    def local_origin():
        from config import MAIN_SERVER_PORT
        return f"http://127.0.0.1:{int(MAIN_SERVER_PORT)}"

    def local_characters(self):
        try:
            result = request_json(self.local_origin() + "/api/characters", timeout=2)
            return list(result.get("猫娘", {})), result.get("当前猫娘", "")
        except (OSError, ValueError, TypeError, AttributeError):
            return [], ""

    def _clear_authorization(self):
        self.authorization = self.catalog = self.waiting = self.draft = None

    def _authorized(self):
        if self.authorization and self.authorization["expiresAt"] > time.time() * 1000:
            return True
        self._clear_authorization()
        return False

    def _from_panel(self, token):
        return isinstance(token, str) and token.isascii() and bool(self.panel_token) and secrets.compare_digest(self.panel_token, token)

    def website_player_grant(self):
        grant = self._website_player_grant
        if grant and grant[1] > time.time() * 1000:
            return grant[0]
        self._website_player_grant = None
        return None

    def website_login_state(self):
        code = self.browser_login["code"] if self.browser_login and self.browser_login["expiresAt"] > time.time() * 1000 else None
        return {"browserCode": code, "authorized": self._authorized(), "playerAuthorized": bool(self.website_player_grant()),
                "uiToken": self.panel_token}

    @ui.context(id="resident_connection", title="千灯纪居民")
    async def connection_context(self):
        role, session = self._read_resident_binding()
        resident = (session or {}).get("resident", {})
        login = self.website_login_state()
        names, current = await asyncio.to_thread(self.local_characters)
        return {"role": role or getattr(self.ctx, "current_lanlan", "") or current,
                "localRoles": names, "authorized": login["authorized"], "catalog": self.catalog or {},
                "waiting": self.waiting[0]["name"] if self.waiting else None,
                "resident": resident.get("name", ""), "connected": session is not None,
                "bodyKind": resident.get("bodyKind"), "characterId": resident.get("characterId"),
                "control": self._resident_status(),
                "browserCode": login["browserCode"], "uiToken": self.panel_token}

    def _read_resident_binding(self):
        try:
            binding = json.loads(self.data_path("resident-binding.json").read_bytes())
            role = binding["role"]
            if isinstance(role, str) and role.strip() and role.isprintable() and len(role) <= 128:
                return role, read_session(binding["session"], self.portal)
        except (OSError, ValueError, TypeError, KeyError):
            pass
        return "", None

    def _resident_pairing_blocked(self):
        return Err({"code": "resident_control_active", "message": "请先停止当前居民的桌面控制，再更换授权或角色。"})

    @ui.action(id="open_resident_website", label="打开角色管理或授权页")
    @plugin_entry(id="open_resident_website", name="打开角色管理或授权页", input_schema={
        "type": "object", "properties": {"page": {"type": "string", "enum": ["authorize", "characters"]}, "uiToken": SECRET},
        "required": ["page", "uiToken"], "additionalProperties": False})
    async def open_resident_website(self, page, uiToken, **_):
        if not self._from_panel(uiToken) or page not in ("authorize", "characters"):
            return Err("请从千灯纪居民面板打开。")
        url = self.portal + "/resident-connect.html?flow=authorize" if page == "authorize" else self.local_origin() + "/character_card_manager"
        if not await asyncio.to_thread(webbrowser.open, url):
            return Err("请在浏览器打开 " + url)
        return Ok({"opened": True})

    @ui.action(id="resident_browser_login", label="网页登录并授权")
    @plugin_entry(id="resident_browser_login", name="网页登录并授权", input_schema={
        "type": "object", "properties": {"op": {"type": "string", "enum": ["start", "status"]}, "uiToken": SECRET},
        "required": ["op", "uiToken"], "additionalProperties": False})
    async def resident_browser_login(self, op, uiToken, **_):
        if not self._from_panel(uiToken) or op not in ("start", "status"):
            return Err("请从千灯纪居民面板操作。")
        if self.pair_lock.locked() and op == "status":
            return Ok({"state": "pending"})
        async with self.pair_lock:
            if self._resident_phase != "stopped":
                return self._resident_pairing_blocked()
            if self.browser_login and self.browser_login["expiresAt"] <= time.time() * 1000:
                self.browser_login = None
            try:
                api = self.portal + "/api/v1/resident-onboarding/"
                if op == "start":
                    if not self.browser_login:
                        pending = await asyncio.to_thread(request_json, api + "browser-start", {})
                        if (str(UUID(pending["id"])) != pending["id"]
                                or not re.fullmatch(r"rba_[A-Za-z0-9_-]{43}", pending["secret"])
                                or not re.fullmatch(r"[0-9]{6}", pending["code"])
                                or not pending["expiresAt"] > time.time() * 1000):
                            raise ValueError("invalid_browser_login")
                        self.browser_login = pending
                    url = self.portal + "/resident-connect.html?flow=browser&play=1#" + self.browser_login["id"]
                    if not await asyncio.to_thread(webbrowser.open, url):
                        return Err("请在浏览器打开 " + url)
                    return Ok({"opened": True})
                if not self.browser_login:
                    return Ok({"state": "expired"})
                data = await asyncio.to_thread(request_json, api + "browser-status", {}, self.browser_login["secret"])
                if data["state"] == "authorized":
                    player_until = data.get("playerAuthorizationExpiresAt")
                    player_grant = (self.browser_login["secret"], player_until) if type(player_until) is int else None
                    await self._accept_authorization(data)
                    self._website_player_grant = player_grant
                return Ok({"state": data["state"]})
            except HTTPError as exc:
                if op == "status" and exc.code == 401:
                    self.browser_login = None
                    return Ok({"state": "expired"})
                return Err("无法使用网页登录。请检查官网连接，也可以使用授权码。")
            except (OSError, ValueError, TypeError, KeyError):
                return Err("网页登录暂未完成，请重试。")

    async def _accept_authorization(self, auth):
        if (not re.fullmatch(r"rot_[A-Za-z0-9_-]{43}", auth["onboardingToken"])
                or not auth["expiresAt"] > time.time() * 1000):
            raise ValueError("invalid_authorization")
        self._clear_authorization()
        self._website_player_grant = None
        self.authorization = auth
        try:
            await self._list()
        except (OSError, ValueError, TypeError, KeyError):
            self._clear_authorization()
            raise
        self.browser_login = None

    @ui.action(id="pair_resident", label="连接居民身体", refresh_context=True)
    @plugin_entry(id="pair_resident", name="连接居民身体", input_schema={
        "type": "object", "properties": {"code": {**SECRET, "maxLength": 20}, "uiToken": SECRET,
                                        "localRole": {"type": "string", "maxLength": 128}},
        "required": ["code", "uiToken"], "additionalProperties": False})
    async def pair_resident(self, code, uiToken, localRole="", **_):
        if not self._from_panel(uiToken):
            return Err("请在千灯纪居民面板输入官网连接码。")
        if not isinstance(code, str) or not re.fullmatch(r"[2-9A-HJ-NP-Z]{4}(?:-[2-9A-HJ-NP-Z]{4}){2}", code.strip().upper()):
            return Err("请粘贴官网显示的三组四位连接码。")
        async with self.pair_lock:
            if self._resident_phase != "stopped":
                return self._resident_pairing_blocked()
            try:
                payload = {"code": code.strip().upper()}
                try:
                    auth = await asyncio.to_thread(request_json, self.portal + "/api/v1/resident-onboarding/pair", payload)
                except HTTPError as exc:
                    if exc.code not in (403, 404):
                        raise
                    role = await self._resolve_role(localRole)
                    if not role:
                        return Err("请先选择本机角色，再提交旧版居民连接码。")
                    grant = await asyncio.to_thread(request_json, self.portal + "/api/v1/resident-turns/pair", payload)
                    result = await self._bind(role, grant)
                    self._website_player_grant = None
                    return result
                await self._accept_authorization(auth)
            except (OSError, ValueError, TypeError, KeyError):
                return Err("未能完成配对。请检查网络并在官网重新生成连接码。")
        return Ok({"authorized": True})

    async def _resolve_role(self, candidate):
        names, current = await asyncio.to_thread(self.local_characters)
        saved, _ = self._read_resident_binding()
        role = candidate or getattr(self.ctx, "current_lanlan", "") or saved or current
        if not isinstance(role, str):
            return None
        role = role.strip()
        return role if role and role.isprintable() and len(role) <= 128 and (not names or role in names) else None

    async def _bind(self, role, grant):
        session = read_session(grant, self.portal)
        await asyncio.to_thread(write_resident_state, self.data_path("resident-binding.json"),
                                {"role": role, "session": session})
        self._clear_authorization()
        self.browser_login = None
        self._resident_health = "idle"
        return Ok({"role": role, "resident": session.get("resident", {}).get("name", ""), "connected": True,
                   "controlling": False})

    async def _onboarding_request(self, op, payload):
        return await asyncio.to_thread(request_json, self.portal + "/api/v1/resident-onboarding/" + op, payload, self.authorization["onboardingToken"])

    async def _list(self):
        data = await self._onboarding_request("list", {})
        self.catalog = {"availableBodies": data["availableBodies"], "residents": [
            {key: row[key] for key in ("id", "characterId", "name", "bodyKind", "state")} for row in data["residents"]]}

    @ui.action(id="manage_residents", label="管理游戏角色")
    @plugin_entry(id="manage_residents", name="管理游戏角色", input_schema={
        "type": "object", "properties": {"op": {"type": "string", "enum": ["list", "create", "connect"]},
            "uiToken": SECRET, "id": {"type": "string"}, "characterId": {"type": "string"}, "localRole": {"type": "string"},
            "bodyKind": {"type": "string", "enum": ["maid", "numen"]}, "name": {"type": "string", "maxLength": 24},
            "persona": {"type": "string", "maxLength": 1000}}, "required": ["op", "uiToken"], "additionalProperties": False})
    async def manage_residents(self, op, uiToken, id="", characterId="", localRole="", bodyKind="", name="", persona="", **_):
        if not self._from_panel(uiToken):
            return Err("请从千灯纪居民面板操作。")
        async with self.pair_lock:
            if self._resident_phase != "stopped":
                return self._resident_pairing_blocked()
            if not self._authorized():
                return Err("请重新登录官网授权。")
            try:
                if op == "list":
                    await self._list()
                    if not self.waiting:
                        return Ok({"updated": True})
                    target, role = self.waiting
                    id, characterId = target["id"], target["characterId"]
                else:
                    role = await self._resolve_role(localRole)
                    if not role:
                        return Err("请选择本机 N.E.K.O. 中接收游戏消息的角色。")
                    if op == "create":
                        profile = {"name": name.strip(), "persona": persona.strip(), "bodyKind": bodyKind}
                        if not self.draft or self.draft[0] != profile:
                            self.draft = profile, str(uuid4())
                        created = await self._onboarding_request("create", {**profile, "requestId": self.draft[1]})
                        self.waiting = created["resident"], role
                        id, characterId = self.waiting[0]["id"], self.waiting[0]["characterId"]
                        await self._list()
                    elif op != "connect":
                        return Err("未知角色操作。")
                selected = next((row for row in self.catalog["residents"] if row["id"] == id and row["characterId"] == characterId), None)
                if not selected:
                    return Err("请刷新角色列表后重新选择。")
                if selected["state"] != "available":
                    self.waiting = selected, role
                    return Ok({"state": "preparing"})
                grant = await self._onboarding_request("connect", {"id": id, "characterId": characterId})
                if grant["resident"]["characterId"] != characterId or grant["resident"]["id"] != id:
                    return Err({"code": "resident_identity_changed", "message": "官网返回的居民身份已变化，请重新授权并选择原角色。"})
                return await self._bind(role, grant)
            except HTTPError as exc:
                if exc.code == 401:
                    self._clear_authorization()
                    return Err("授权已过期，请重新登录官网。")
                return Err("官网暂未完成操作。请刷新角色列表后重试。")
            except (OSError, ValueError, TypeError, KeyError):
                return Err("未能完成角色操作。请检查连接后重试。")
