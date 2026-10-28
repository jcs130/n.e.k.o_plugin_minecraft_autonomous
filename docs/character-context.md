# 游戏人格与记忆的绑定

`host_context.enabled=true` 且显式配置本机公开的 `/api/characters` 地址时，插件独立同步角色卡。无需开启 `heartbeat` 或 `presentation`，不会为同步调用模型。优先使用已配置的 heartbeat/presentation target；未指定时使用公开 API 的当前角色。

计时服务每 10 秒核对配置与已有身体，每 120 秒更新一次公开人格。它要求身份匹配、持有现有账号租约、30 秒内的已连接快照；网络返回后再次核对配置、停止状态、进程和运行会话。它不连接游戏、不启动自主行动。手动入口 `sync_character_context` 返回绑定元数据，不返回人格正文。

角色卡优先使用显式 `system_prompt`；否则只选取公开人格字段，包括昵称、日常称呼、自称、口癖、口头禅、说话风格及性格。身份与说话习惯排在长性格描述之前，最多 2400 UTF-8 字节。音色、模型、凭据及 `_reserved` 不进入游戏人格。

同步调用核心公开 `HostContextPort.publish_static`，只刷新人格期限；不延长已选记忆、当前意图或近期语言的期限。相同人格刷新不把时间戳插入模型前缀。宿主明确提供的有效人格投影仍优先。

可选的 `host_context.memory_api_url` 必须显式指向本机记忆服务的 origin。它仅供 `load_character_identity_memory` 按需调用：通过该角色的只读 `get_persona` 选择最多 6 条身份记忆，保留原始 ID 与来源，忽略已抑制记录和内部元数据；不读取近期聊天正文，不调用模型。计时同步不调用这个接口，也不为所选记忆续期。已有明确的宿主记忆/意图投影优先；此入口不能替代按话题检索游戏或直播经历。

人格接入不能视作记忆召回：`status.host_context.memory_selection=not_provided` 表示宿主尚未选择个人记忆，不能解释成没有历史。Neko 的个人近期/人格/长期记忆按角色保存；MC 的笔记、人物关系和经验由核心 `mc_memory` 按服务器、账号与 Agent 隔离。游戏原始账本也不等价于已经提炼的长期笔记。宿主可通过既有 review context 提交有来源的选中记忆，不能整库复制、伪造召回或把别人的经历移入本角色。

验收需分别核对：静态人格可用、下一次真实决策 `status.context.host_context.persona=true`、原账号/运行会话保持，以及具体记忆的可检索来源。仅有角色文件、HTTP 成功或旧日志不能证明当前模型已经使用。

运行层 0.2.117 统一了规划器的协议权限、渐进帮助与错误修正：`mc_protocol` 只暴露 task/facts/archive/archive_runs，回合与 barrier 仍由宿主协调。普通技能帮助继续按真实 schema 限量查询；这不是人格提示词或旧经历的权限。旧版现役可用原生 insert 反馈纠正当前决策；永久修复需加载相应运行层，不把源码提交视为现役已经升级。
