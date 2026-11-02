"""User initiated optional onboarding, independent of the native work queue."""

from agent_mc_autonomy.configuration import Settings
from agent_mc_autonomy.mailbox import Mailbox
from agent_mc_autonomy.ownership import session_is_owned, session_lease
from agent_mc_autonomy.recovery import require_no_pending_acknowledgement
from plugin.sdk.plugin import Err, Ok, plugin_entry, ui

from .prepared_runtime import resolve_host_runtime
from .qiandengji_account import (
    AccountError,
    account_action,
    configured_identity,
    prepare_login,
    read_identity,
    start_failure,
)
from .qiandengji_onboarding import (
    account_root,
    prepare_invitation,
    prepare_public_identity,
    selected_identity,
    store_identity,
)


def require_idle(plugin, settings):
    directory = settings.data_root(plugin.data_path()) / "sessions" / settings.identity / "host"
    if session_is_owned(directory) or plugin._worker and plugin._worker.snapshot().get("worker_alive"):
        raise AccountError("account_runtime_active")
    if directory.exists():
        Mailbox(directory).check_uncertain()
        require_no_pending_acknowledgement(directory)


class QiandengjiPanel:
    @ui.action(label='免邀请码加入千灯纪')
    @plugin_entry(id='join_public_account', name='免邀请码加入千灯纪', kind='service', timeout=85,
                  description='本人显式创建或继续原普通Agent体验账号，保存自动登录，不关联猫娘计划账号，不启动游戏。',
                  input_schema={'type': 'object', 'properties': {'username': {'type': 'string', 'maxLength': 16}}})
    async def join_public_account(self, username: str = '', **_):
        try:
            from .neko_account_link import load_link
            raw = await self.config.dump()
            settings = Settings.parse(resolve_host_runtime(raw)[0])
            require_idle(self, settings)
            if settings.runtime_mode == 'external' or configured_identity(raw) or settings.login_config_file:
                raise AccountError('existing_game_role_use_original_connection')
            if settings.username and (settings.data_root(self.data_path()) / 'sessions' / settings.identity / 'host/status.json').exists():
                raise AccountError('existing_game_role_use_original_connection')
            with session_lease(account_root() / 'public-registration-lock'):
                identity_file = prepare_public_identity(username, seed=load_link())
                result = await account_action('join_public', str(identity_file), node=settings.node)
                if result['ready']:
                    return await self.qiandengji_account('import', identity_file=str(identity_file))
                return Ok({**result, 'account_saved': True})
        except (OSError, ValueError, RuntimeError) as error:
            code = str(error) if isinstance(error, AccountError) else 'public_signup_unconfirmed'
            messages = {'reserved_observer_name': 'Eye 是配对观战身份，不能注册为普通 Agent。请先使用本体，再以本人已授权的 Eye 身份观战。',
                        'existing_game_role_use_original_connection': '请继续使用原角色和已保存登录，不要再次创建账号。',
                        'account_runtime_active': '请先停止游玩并等待原动作结算，再准备账号。',
                        'invalid_agent_name': '昵称须以 ag_ 开头，仅含英文字母、数字和下划线，总长不超过 16 位。'}
            return Err({'code': code, 'message': messages.get(code, '账号准备未确认。请保留原昵称和本机身份，继续同一申请；已有账号请使用原登录，不重复建号。')})

    @ui.action(label="千灯纪网站账户接入")
    @plugin_entry(id="qiandengji_account", name="千灯纪网站账户接入", kind="service", timeout=85,
                  description="本人通过界面选身份文件或填写邀请，显式查状态、激活或接入；私有材料不回显，不启动游戏。",
                  input_schema={"type": "object", "properties": {
                      "action": {"enum": ["register", "status", "activate", "import"]},
                      "identity_file": {"type": "string", "maxLength": 4096},
                      "identity_json": {"type": "string", "maxLength": 16384, "writeOnly": True},
                      "username": {"type": "string", "maxLength": 16},
                      "invite_url": {"type": "string", "maxLength": 512, "writeOnly": True},
                      "invite_url_file": {"type": "string", "maxLength": 4096}}, "required": ["action"]})
    async def qiandengji_account(self, action: str, identity_file: str = "", username: str = "", invite_url_file: str = "",
                                identity_json: str = "", invite_url: str = "", **_):
        try:
            if action not in {"register", "status", "activate", "import"}:
                raise AccountError("invalid_account_action")
            raw = await self.config.dump()
            effective, _ = resolve_host_runtime(raw)
            settings = Settings.parse(effective)
            if action != "status":
                require_idle(self, settings)
            if identity_json:
                if action != 'import' or identity_file or invite_url or invite_url_file:
                    raise AccountError('invalid_account_action')
                identity_file = str(store_identity(identity_json))
            if invite_url:
                if action != 'register' or identity_file or invite_url_file or identity_json:
                    raise AccountError('invalid_account_action')
                path, invitation = prepare_invitation(username, invite_url)
                identity_file, invite_url_file = str(path), str(invitation)
                # The official helper saves identity before registration. A retry
                # queries the original request instead of registering another.
                if path.exists():
                    action = 'status'
            if not identity_file:
                path = configured_identity(raw) or selected_identity()
                if not path:
                    raise AccountError('private_file_unavailable')
                identity_file = str(path)
            if action == "register" and username == settings.username:
                history = settings.data_root(self.data_path()) / "sessions" / settings.identity / "host"
                if settings.login_config_file or (history / "status.json").exists():
                    raise AccountError("existing_game_role_use_original_connection")
            result = await account_action("status" if action == "import" else action, identity_file,
                                          username=username, invite_url_file=invite_url_file, node=settings.node)
            if action == "import":
                if not result["ready"]:
                    raise AccountError("account_not_ready_query_status")
                path, identity = read_identity(identity_file)
                connection = {"host": "micro.kangqiang.site", "port": 25702, "username": identity["username"],
                              "auth": "offline", "version": "1.21.1", "connection_type": "custom"}
                desired = Settings.parse({**raw, "server": {**raw.get("server", {}), **connection}})
                require_idle(self, settings)
                require_idle(self, desired)
                if settings.runtime_mode == "external":
                    raise AccountError("import_requires_embedded_mode")
                login = prepare_login(path, identity, self.data_path())
                saved = await self.save_settings({"server": {**connection, "login_config_file": str(login)},
                                                  "qiandengji": {"identity_file": str(path)}})
                if isinstance(saved, Err):
                    return saved
                result["imported"] = True
            return Ok(result)
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            code = str(error) if isinstance(error, AccountError) else "account_operation_not_ready"
            messages = {
                'account_runtime_active': '请先停止游玩并等待动作结束，再接入账号。',
                'invalid_private_invitation': '邀请链接无效。请粘贴千灯纪官网“邀请自己的 Agent”生成的完整链接，不要填网站密码。',
                'invalid_agent_name': 'Agent 昵称须以 ag_ 开头，总长不超过 16 位，只使用英文字母、数字和下划线。',
                'identity_exists_query_status': '本机已有保存的 Agent 身份或创建请求。请查询并接入原账号，不要重复创建。',
                'private_material_conflict': '本机已保存的账号材料与所选文件不同，未覆盖。请使用原身份文件。',
                'import_requires_embedded_mode': '当前为独立身体的观察模式，不能切换其账号。请在原运行入口停止并配置，或使用嵌入式模式。',
                'invalid_account_action': '接入参数不匹配，请选择一种接入方式后重试。',
                'existing_game_role_use_original_connection': '该角色已有游戏记录。请沿用原昵称与游戏登录密码，不要重新创建。',
            }
            detail = start_failure(error)
            return Err({'code': code if code in messages or detail['reason'] != 'account_check_failed' else 'account_operation_not_ready',
                        'message': messages.get(code, detail['message'])})
