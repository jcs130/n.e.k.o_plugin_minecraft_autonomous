"""Official website pairing for the resident mode of the N.E.K.O. adapter."""

# Adapted from jcs130/minecraft-ai-friend resident 0.3.2 (bf913815), MIT.

import asyncio
import importlib
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

from .neko_resident_device import DesktopDevice, DeviceVault

PORTAL = "https://mc.kangqiang.site"
SECRET = {"type": "string", "writeOnly": True}

BODY_KINDS = ("mineflayer", "numen", "maid", "villager")
BODY_STATUSES = ("ready", "switching", "recovery_required", "unavailable")
RECEIPT_PHASES = ("releasing", "acquiring", "completed", "reconciled")
RECEIPT_REASONS = (
    "SOURCE_NOT_READY", "TARGET_NOT_READY", "SOURCE_RELEASE_UNCONFIRMED",
    "TARGET_ACQUIRE_UNCONFIRMED", "SERVICE_RESTART", "ORIGINAL_RECEIPTS_CONFIRMED",
)


def public_body_id(value):
    return value if (
        isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value)
        and not value.startswith(("qdh_", "qdp_", "rot_", "rdt_", "rba_", "rbc_", "qda_"))
    ) else None


def public_generation(value):
    return value if type(value) is int and 1 <= value <= 2**53 - 1 else None


def body_control_view(value):
    """Project display state without private control or pairing data."""
    if not isinstance(value, dict) or value.get("status") not in BODY_STATUSES:
        return None
    kind = value.get("activeKind")
    return {
        "status": value["status"],
        "activeKind": kind if kind in BODY_KINDS else None,
        "generation": public_generation(value.get("generation")),
        "pendingRequestId": public_body_id(value.get("pendingRequestId")),
    }


def body_row(value):
    state = body_control_view(value)
    if not state or not public_body_id(value.get("characterId")):
        raise ValueError("invalid_character")
    name = value.get("name")
    if not isinstance(name, str) or not name.strip() or not name.isprintable() or len(name) > 128:
        raise ValueError("invalid_character_name")
    targets = value.get("targetKinds")
    allowed = [kind for kind in BODY_KINDS if kind != state["activeKind"] and kind in targets] if isinstance(targets, list) else []
    return {**state, "characterId": value["characterId"], "name": name,
            "targetKinds": allowed, "autonomous": value.get("autonomous") is True}


def body_receipt_view(value, character_id, request_id):
    if not isinstance(value, dict) or value.get("characterId") != character_id or value.get("requestId") != request_id:
        raise ValueError("receipt_mismatch")
    status, phase, active, target = (value.get(key) for key in ("status", "phase", "activeKind", "targetKind"))
    generation = public_generation(value.get("generation"))
    if (status not in ("completed", "blocked", "switching", "recovery_required") or phase not in RECEIPT_PHASES
            or not generation or target not in BODY_KINDS or (active is not None and active not in BODY_KINDS)
            or (status == "completed" and (active != target or phase not in ("completed", "reconciled")))):
        raise ValueError("invalid_receipt")
    reason = value.get("reason")
    return {"characterId": character_id, "requestId": request_id, "status": status, "phase": phase,
            "activeKind": active, "targetKind": target, "generation": generation,
            "reason": reason if reason in RECEIPT_REASONS else None}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, payload=None, token=None, *, timeout=8, extra_headers=None):
    headers = {"Content-Type": "application/json", **(extra_headers or {})}
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
    body_view = None
    body_receipt = None
    _website_player_grant = None
    _body_device_pairing = None
    _body_device_character = None
    _body_device_grant = None
    _desktop_client = None
    _desktop_view = None

    def _desktop(self):
        if self._desktop_client is None:
            vault = DeviceVault(self.data_path("desktop-device.lock"), self.portal)
            self._desktop_client = DesktopDevice(self.portal, vault, request_json)
        return self._desktop_client

    async def _refresh_desktop(self):
        device = self._desktop()
        record = await asyncio.to_thread(device.settings)
        if not record.get("refreshToken"):
            self._desktop_view = {"status": "reauthorize" if record.get("character") else "unlinked"}
            return None
        try:
            state = await asyncio.to_thread(device.authorized, "status", {})
            character = state["character"]
            if character["characterId"] != record["character"] or str(UUID(record["character"])) != record["character"]:
                raise ValueError("desktop_character_changed")
            self._desktop_view = {
                "status": "authorized", "character": {key: character.get(key) for key in
                    ("id", "characterId", "name", "bodyId", "bodyKind")}, "canStart": state.get("canStart") is True,
                "controller": state.get("controller"), "controllerName": state.get("controllerName"),
                "pendingRequestId": state.get("pendingRequestId"), "role": record.get("localRole"),
                "activeKind": state.get("activeKind"), "modes": [kind for kind in BODY_KINDS if kind in state.get("modes", [])],
            }
            return state
        except HTTPError as error:
            self._desktop_view = {"status": "reauthorize" if error.code == 401 else "unavailable"}
        except (OSError, TypeError, ValueError, KeyError):
            self._desktop_view = {"status": "unavailable"}
        return None

    @ui.action(id="desktop_device", label="千灯纪设备授权", refresh_context=True)
    @plugin_entry(id="desktop_device", name="千灯纪设备授权", kind="service", timeout=30,
                  input_schema={"type": "object", "properties": {
                      "op": {"type": "string", "enum": ["login", "cross-device", "complete", "refresh", "start", "stop", "verify"]},
                      "localRole": {"type": "string", "maxLength": 128},
                      "mode": {"type": "string", "enum": ["maid", "numen"]}, "uiToken": SECRET},
                      "required": ["op", "uiToken"], "additionalProperties": False})
    async def desktop_device(self, op, uiToken, localRole="", mode="", **_):
        if not self._from_panel(uiToken):
            return Err({"code": "resident_panel_required", "message": "请从千灯纪居民面板操作。"})
        if self.pair_lock.locked() and op == "complete":
            return Ok({"pending": True})
        async with self.pair_lock:
            device = self._desktop()
            try:
                if op == "refresh":
                    await self._refresh_desktop()
                    return Ok({"status": self._desktop_view["status"]})
                if op == "start":
                    return await self._start_desktop_resident(localRole, mode)
                if op == "stop":
                    return await self._stop_desktop_resident()
                if op == "verify":
                    return await self._verify_desktop_play()
                if self._resident_phase != "stopped":
                    return self._resident_pairing_blocked()
                if self._desktop_play_record():
                    return Err({"code": "desktop_request_pending", "message": "请先核对本机原控制请求。"})
                if op in ("login", "cross-device"):
                    url = await device.start(op == "cross-device")
                    return Ok({"opened": await asyncio.to_thread(webbrowser.open, url)})
                if op == "complete":
                    if not await device.complete():
                        return Ok({"pending": True})
                    await self._refresh_desktop()
                    return Ok({"status": self._desktop_view["status"]})
            except HTTPError as error:
                if op == "complete" and error.code in (400, 401, 404):
                    device.close_login()
                if op in ("start", "stop") and self._desktop_play_record():
                    return self._desktop_pending_error()
                return Err({"code": "desktop_portal_unavailable", "message": "官网未确认设备授权，请刷新状态。"})
            except (ImportError, OSError, RuntimeError, TypeError, ValueError, KeyError):
                if op in ("start", "stop") and self._desktop_play_record():
                    return self._desktop_pending_error()
                return Err({"code": "desktop_authorization_unavailable", "message": "暂未完成设备授权，请检查官网状态和系统凭据存储。"})
        return Err({"code": "invalid_desktop_operation"})

    @staticmethod
    def _body_device_provider():
        try:
            return importlib.import_module("agent_mc_autonomy.device_pairing")
        except ModuleNotFoundError:
            return None

    def desktop_body_device_grant(self):
        """In-process handoff for a compatible player worker."""
        grant = self._body_device_grant
        if grant is not None and grant.expires_at > time.time() * 1000:
            return grant
        self._body_device_grant = None
        return None

    @staticmethod
    def _body_device_connection_supported(settings):
        return (settings.host.lower() == "micro.kangqiang.site" and settings.port == 25702
                and settings.body_provider == "mineflayer")

    def _body_device_status(self):
        grant = self.desktop_body_device_grant()
        if grant is not None:
            return {"state": "paired", "characterId": grant.character_id}
        pairing = self._body_device_pairing
        if pairing is None:
            return {"state": "idle"}
        if pairing.expires_at <= time.time() * 1000:
            self._body_device_pairing = self._body_device_character = None
            return {"state": "expired"}
        return {"state": "pending", "pairId": pairing.pair_id, "expiresAt": pairing.expires_at,
                "characterId": self._body_device_character}

    @ui.action(id="pair_body_device", label="配对桌面接力设备")
    @plugin_entry(id="pair_body_device", name="配对桌面接力设备", input_schema={
        "type": "object", "properties": {"op": {"type": "string", "enum": ["start", "open", "check", "cancel"]},
            "characterId": {"type": "string", "maxLength": 128}, "uiToken": SECRET},
        "required": ["op", "uiToken"], "additionalProperties": False})
    async def pair_body_device(self, op, uiToken, characterId="", **_):
        if not self._from_panel(uiToken) or op not in ("start", "open", "check", "cancel"):
            return Err("请从千灯纪居民面板配对设备。")
        provider = self._body_device_provider()
        if provider is None:
            return Err("当前运行时尚未接入设备配对。")
        async with self.pair_lock:
            if self._resident_phase != "stopped":
                return self._resident_pairing_blocked()
            status = self._body_device_status()["state"]
            if op == "cancel":
                self._body_device_pairing = self._body_device_character = None
                return Ok({"state": "paired" if status == "paired" else "idle"})
            if status == "paired":
                return Ok({"state": status})
            if op != "start" and status != "pending":
                return Err("配对已结束，请生成新的配对编号。")
            official_page = self.portal + "/resident-connect.html?flow=bodies"
            try:
                if op == "start":
                    if status == "pending" and characterId != self._body_device_character:
                        return Err("请先结束当前角色的配对。")
                    if not self._body_readable() or (self.body_view or {}).get("available") is not True or not any(
                            row["characterId"] == characterId for row in self.body_view["characters"]):
                        return Err("请在角色身体列表里选择本人角色，再生成配对编号。")
                    if status != "pending":
                        pairing = await provider.begin_device_pairing(self.portal)
                        if not re.fullmatch(r"[A-Za-z0-9_-]{24}", pairing.pair_id) or pairing.approval_url != official_page:
                            raise ValueError("invalid_device_pairing")
                        self._body_device_pairing = pairing
                        self._body_device_character = characterId
                elif op == "open":
                    if not await asyncio.to_thread(webbrowser.open, official_page):
                        return Err("未能打开官网。请进入千灯纪的角色身体管理页。")
                elif op == "check":
                    grant = await provider.redeem_device_pairing(self._body_device_pairing)
                    if grant is not None:
                        expected = self._body_device_character
                        self._body_device_pairing = self._body_device_character = None
                        if grant.character_id != expected:
                            return Err("官网批准的是另一角色。请在官网撤销该设备，再对选定角色配对。")
                        self._body_device_grant = grant
                return Ok({"state": self._body_device_status()["state"]})
            except Exception:
                # The provider handles recovery; its exception may contain private transport data.
                return Err("暂时无法核对设备配对，请在官网检查批准状态后重试。")

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
        self.body_view = self.body_receipt = None

    def _body_readable(self):
        until = self.authorization.get("bodyReadExpiresAt") if self._authorized() else None
        if type(until) in (int, float) and until > time.time() * 1000:
            return True
        self.body_view = self.body_receipt = None
        return False

    @ui.action(id="read_character_body", label="查看身体状态和原回执")
    @plugin_entry(id="read_character_body", name="查看身体状态和原回执", input_schema={
        "type": "object", "properties": {"op": {"type": "string", "enum": ["list", "receipt"]},
            "characterId": {"type": "string"}, "requestId": {"type": "string"}, "uiToken": SECRET},
        "required": ["op", "uiToken"], "additionalProperties": False})
    async def read_character_body(self, op, uiToken, characterId="", requestId="", **_):
        if not self._from_panel(uiToken) or op not in ("list", "receipt"):
            return Err("请从居民面板查看角色身体。")
        async with self.pair_lock:
            if not self._body_readable():
                return Err("本次授权未开放身体查询。可以打开官网查看。")
            url = self.portal + "/api/v1/character-bodies"
            if op == "receipt":
                known = (self.body_view or {}).get("characters", [])
                if not public_body_id(characterId) or not public_body_id(requestId) or not any(
                        row["characterId"] == characterId for row in known):
                    return Err("请选择列表中的角色并填写原请求编号。")
                url += f"/{characterId}/switch/{requestId}"
                self.body_receipt = None
            try:
                data = await asyncio.to_thread(request_json, url, None, self.authorization["onboardingToken"])
                if not self._body_readable():
                    return Err("本次授权已结束，请重新打开官网。")
                if op == "list":
                    available = data["available"]
                    if type(available) is not bool:
                        raise ValueError("invalid_body_availability")
                    rows = [body_row(row) for row in data["characters"]] if available else []
                    self.body_view = {"available": available, "characters": rows}
                    if self.body_receipt and not any(row["characterId"] == self.body_receipt["characterId"] for row in rows):
                        self.body_receipt = None
                else:
                    self.body_receipt = body_receipt_view(data, characterId, requestId)
                return Ok({"updated": True})
            except HTTPError as error:
                if op == "list" and error.code == 404 and self._body_readable():
                    self.body_view = {"available": False, "characters": []}
                    self.body_receipt = None
                    return Ok({"updated": True})
                if op == "list":
                    self.body_view = self.body_receipt = None
                return Err("未能核对身体状态或原回执。可以打开官网查看。")
            except (OSError, ValueError, TypeError, KeyError):
                if op == "list":
                    self.body_view = self.body_receipt = None
                return Err("未能核对身体状态或原回执。可以打开官网查看。")

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
        if self._desktop_view is None and self.data_path("desktop-device.lock").is_file():
            try:
                await self._refresh_desktop()
            except (ImportError, OSError, RuntimeError, TypeError, ValueError):
                self._desktop_view = {"status": "unavailable"}
        device_login = self._desktop_client.login if self._desktop_client is not None else None
        desktop_play = self._desktop_play_record()
        names, current = await asyncio.to_thread(self.local_characters)
        return {"role": role or getattr(self.ctx, "current_lanlan", "") or current,
                "localRoles": names, "authorized": login["authorized"], "catalog": self.catalog or {},
                "bodyReadable": self._body_readable(), "bodyView": self.body_view, "bodyReceipt": self.body_receipt,
                "bodyDeviceAvailable": self._body_device_provider() is not None, "bodyDevice": self._body_device_status(),
                "desktop": self._desktop_view, "desktopPending": device_login is not None,
                "desktopCode": device_login.get("crossCode") if device_login else None,
                "desktopUrl": device_login["url"] if device_login and device_login.get("crossCode") else None,
                "desktopPlay": desktop_play,
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
        "type": "object", "properties": {"page": {"type": "string", "enum": ["authorize", "characters", "bodies"]}, "uiToken": SECRET},
        "required": ["page", "uiToken"], "additionalProperties": False})
    async def open_resident_website(self, page, uiToken, **_):
        if not self._from_panel(uiToken) or page not in ("authorize", "characters", "bodies"):
            return Err("请从千灯纪居民面板打开。")
        url = (self.local_origin() + "/character_card_manager" if page == "characters"
               else self.portal + "/resident-connect.html?flow=" + page)
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
                        pending = await asyncio.to_thread(request_json, api + "browser-start", {"bodyRead": True})
                        if (str(UUID(pending["id"])) != pending["id"]
                                or not re.fullmatch(r"rba_[A-Za-z0-9_-]{43}", pending["secret"])
                                or not re.fullmatch(r"[0-9]{6}", pending["code"])
                                or not pending["expiresAt"] > time.time() * 1000):
                            raise ValueError("invalid_browser_login")
                        self.browser_login = pending
                    url = self.portal + "/resident-connect.html?flow=browser&play=1&bodyRead=1#" + self.browser_login["id"]
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
