"""Explicit Neko-account linking via the website; no host token/file access."""

import asyncio
import contextvars
import time

import httpx
from agent_mc_autonomy.configuration import Settings
from agent_mc_autonomy.ownership import session_lease
from agent_mc_autonomy.server_login import public_login
from plugin.sdk.plugin import Err, Ok, TransportError, plugin_entry, ui

from .neko_account_link import advance_link, ensure_link, load_link, public_link, save_link
from .prepared_runtime import resolve_host_runtime
from .qiandengji_account import AccountError, configured_identity
from .qiandengji_onboarding import account_root, selected_identity
from .qiandengji_panel import require_idle

POLL_SECONDS = 3
MAX_WAIT_SECONDS = 540

MESSAGES = {
    'checking': '正在核对千灯纪官方授权入口。',
    'authorization_required': '请打开官网，用猫娘计划账号登录并允许本次角色准备；插件会自动继续。',
    'approved': '已获本人授权，正在准备游戏账号和自动登录。',
    'ready': '游戏角色已确认，正在私有保存自动登录。',
    'pending': '服务器正在处理原建号请求，请等待；不会重复建号。',
    'unknown': '原请求结果尚未确认，保留身份并查询，不会重复提交。',
    'configured': '账号和自动登录已准备好。选好模型与游戏组件后，点击开始自主游玩。',
    'provider_not_configured': '千灯纪尚未启用猫娘计划登录，需站点完成官方 OAuth 应用登记。原账号与设置保留。',
    'failed': '游戏账号未准备成功，请在官网核对原请求；不会更换名字或重复建号。',
    'paused': '接入查询已暂停；原身份与请求保留，可继续原申请。',
    'expired': '本次授权已过期。尚未提交建号时可重新授权，继续使用同一身份；已提交的请求仍只查询。',
    'neko_link_busy': '另一个接入操作正在处理同一身份，请稍后继续原申请。',
    'neko_link_identity_conflict': '本机已有接入申请，请沿用原角色名和身份。',
    'neko_link_private_material_unavailable': '本机接入资料不可读，请保留原文件，未生成替代身份。',
    'neko_link_response_mismatch': '官方回执与原角色不匹配，未保存连接或启动游戏。',
    'neko_link_result_unconfirmed': '官方接入结果尚未确认。请继续原申请，不要另建角色。',
    'neko_link_configuration_unconfirmed': '账号已准备，但连接保存结果尚未确认。请刷新核对；不会重复保存或自动进服。',
    'original_identity_selected': '本机已有原账号，请使用下方已保存身份接入；可在官网登录原千灯纪账号后关联猫娘计划。',
    'invalid_agent_name': '昵称请留空自动生成，或填写 ag_ 开头、总长不超过16位的英文字母、数字与下划线。',
    'account_runtime_active': '请先停止游玩并等待原动作结算，再关联账号。',
}


class NekoAccountPanel:
    def neko_account_state(self):
        current = getattr(self, '_neko_link_state', None)
        if current is None:
            try:
                current = public_link(load_link())
            except (OSError, ValueError):
                current = {'phase': 'neko_link_private_material_unavailable'}
        task = getattr(self, '_neko_link_task', None)
        phase = current.get('phase', 'idle')
        return {**current, 'active': task is not None and not task.done(), 'message': MESSAGES.get(phase, '')}

    def _link_idle(self, raw):
        effective, _ = resolve_host_runtime(raw)
        settings = Settings.parse(effective)
        if settings.runtime_mode == 'external':
            raise AccountError('account_runtime_active')
        require_idle(self, settings)
        if configured_identity(raw) or selected_identity():
            raise AccountError('original_identity_selected')
        value = load_link()
        if settings.login_config_file and (not value or settings.username != value['username']):
            raise AccountError('original_identity_selected')
        return settings

    @ui.action(label='关联猫娘计划账号')
    @plugin_entry(id='connect_neko_account', name='用猫娘计划账号接入千灯纪', kind='service',
                  description='本人显式发起官网授权；后台只查询同一申请，成功后私有保存游戏自动登录。不读取宿主令牌、不自动进服。',
                  input_schema={'type': 'object', 'properties': {'username': {'type': 'string', 'maxLength': 16}, 'renew': {'type': 'boolean'}}})
    async def connect_neko_account(self, username: str = '', renew: bool = False, **_):
        try:
            raw = await self.config.dump()
            self._link_idle(raw)
            with self._control_lock:
                task = getattr(self, '_neko_link_task', None)
                if task is not None and not task.done():
                    return Ok(self.neko_account_state())
            with self._control_lock, session_lease(account_root() / 'neko-plugin-link-lock'):
                task = getattr(self, '_neko_link_task', None)
                if task is not None and not task.done():
                    return Ok(self.neko_account_state())
                value = ensure_link(username)
                if value['phase'] == 'configured':
                    current = Settings.parse(resolve_host_runtime(raw)[0])
                    if (current.host, current.port, current.username) == ('micro.kangqiang.site', 25702, value['username']) and public_login(current.data_root(self.data_path()), current)['configured']:
                        return Ok(self.neko_account_state())
                    # A confirmed older save is distinct from a lost reply. This
                    # explicit reconnect may save a new resource selection.
                    value['phase'], value['configuration_sent'] = 'ready', False
                    save_link(value)
                self._neko_link_state = {**public_link(value), 'phase': 'checking'}
                self._neko_link_cancel = asyncio.Event()
                self._neko_link_task = asyncio.create_task(self._run_neko_link(value, renew=renew), context=contextvars.Context())
            return Ok(self.neko_account_state())
        except (OSError, ValueError, RuntimeError) as error:
            code = str(error) if isinstance(error, AccountError) else 'neko_link_busy' if isinstance(error, RuntimeError) else 'account_runtime_active'
            return Err({'code': code, 'message': MESSAGES.get(code, '接入尚未开始，请核对原账号和运行状态。')})

    async def _run_neko_link(self, value, *, renew=False):
        try:
            with session_lease(account_root() / 'neko-plugin-link-lock'):
                latest = load_link()
                if latest is None or latest['clientId'] != value['clientId']:
                    raise AccountError('neko_link_identity_conflict')
                # Another app instance may have advanced the same identity after
                # admission. Always reacquire the durable flags under the lease.
                value = latest
                async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                    until = time.monotonic() + MAX_WAIT_SECONDS
                    while not self._neko_link_cancel.is_set() and time.monotonic() < until:
                        state = await advance_link(client, value, renew=renew)
                        renew = False
                        self._neko_link_state = state
                        if state['phase'] == 'ready':
                            raw = await self.config.dump()
                            settings = self._link_idle(raw)
                            connection = {'host': 'micro.kangqiang.site', 'port': 25702, 'username': value['username'],
                                          'auth': 'offline', 'version': '1.21.1', 'connection_type': 'custom'}
                            effective, _ = resolve_host_runtime(raw)
                            require_idle(self, Settings.parse({**effective, 'server': {**effective.get('server', {}), **connection}}))
                            configured = (all(raw.get('server', {}).get(k) == v for k, v in connection.items())
                                          and public_login(settings.data_root(self.data_path()), settings)['configured'])
                            if not configured:
                                if value['configuration_sent']:
                                    raise AccountError('neko_link_configuration_unconfirmed')
                                value['configuration_sent'] = True
                                save_link(value)
                                result = await self.configure_server_login(True, password=value['gamePassword'], connection=connection)
                                if isinstance(result, Err):
                                    raise AccountError('neko_link_configuration_unconfirmed')
                            value['phase'] = 'configured'
                            save_link(value)
                            self._neko_link_state = public_link(value)
                            return
                        if state['phase'] in {'provider_not_configured', 'failed', 'expired'}:
                            return
                        try:
                            await asyncio.wait_for(self._neko_link_cancel.wait(), timeout=POLL_SECONDS)
                        except asyncio.TimeoutError:
                            pass
            self._neko_link_state = {**public_link(value), 'phase': 'paused'}
        except asyncio.CancelledError:
            self._neko_link_state = {**public_link(value), 'phase': 'paused'}
            raise
        except (OSError, ValueError, RuntimeError, TransportError) as error:
            code = str(error) if isinstance(error, AccountError) else 'neko_link_result_unconfirmed'
            self._neko_link_state = {**public_link(value), 'phase': code if code in MESSAGES else 'unknown'}

    async def _close_neko_link(self):
        task = getattr(self, '_neko_link_task', None)
        if task is not None and not task.done():
            self._neko_link_cancel.set()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._neko_link_state = {**public_link(load_link()), 'phase': 'paused'}

    @plugin_entry(id='pause_neko_account_link', name='暂停猫娘计划接入查询', kind='service',
                  description='停止本机授权状态查询，保留原身份和请求；不撤销官网授权、不清空已提交的游戏账号请求。')
    async def pause_neko_account_link(self, **_):
        await self._close_neko_link()
        return Ok(self.neko_account_state())
