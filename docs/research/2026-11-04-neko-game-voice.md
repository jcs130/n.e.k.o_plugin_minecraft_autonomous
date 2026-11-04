# N.E.K.O. 在 Minecraft 中说话：模型、音色与附近语音

核验日期：2026-11-04。本次仅核对源码与官方文档，没有调用模型、TTS 或游戏，没有修改宿主/SDK、配置密钥、启动服务或进行真人听音测试。

核对基线：本机 N.E.K.O. `ffdcc7414c9cfb181807998b02f3a8520bfecb95`；本次 fetch 得到的官方 `origin/main` 为 `cf5a9d363c19bace06c5bf7c766ede273764f552`，仅比较，没有切换或安装；适配插件 `d2604ad55b5f9d87cb0da1e857fbebd22d753f33`；独立框架 `a7bc299a74413a2d29215d148d75427b9b1e5034`，其中游戏核心为 `preview.11`。下文宿主链接固定到已核对的官方提交。

## 直接回答

**不必为了玩 Minecraft 或说话换成 Omni，也不是把 N.E.K.O. 的“辅助 API Key”填上就能完成接入。** 游戏决策使用插件模型绑定；本机声音使用角色已有语音配置；让附近玩家听见还需要把音频送入游戏语音通道。这三件事分别配置、分别验证。[官方插件模型合同](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/docs/design/plugin-model-slots.md#L3-L29)、[官方语音路径](https://project-neko.online/zh-CN/architecture/tts-pipeline)、[附近语音核心](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice-lane.ts#L37-L50)。

| 需求 | 当前实际路径 | 是否需要另配 TTS / Omni |
| --- | --- | --- |
| 决定怎么玩、调用游戏工具 | Plugin API 模型槽绑定 `decision`；需要文本和工具调用 | 不需要语音模型 |
| 桌面上的 N.E.K.O. 用角色声音解说 | 插件提交台词到宿主 `/api/game/minecraft_autonomous/speak` | 复用宿主已经可用的角色 TTS，无需在插件重填语音密钥 |
| 附近玩家从游戏角色位置听见 | 已认证游戏连接上的附近语音传输 | 可上传已有 WAV，也可选择服务器现有 TTS；当前适配尚未串好 N.E.K.O. 原声 |

上表对应[插件用途声明](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/plugin.toml#L19-L32)、[本机语音请求](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/neko_speech.py#L145-L190)与[服务器两种发声入口](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/integrations/proximity-voice/README.md#L11-L42)。

## API Key 应该配在哪里

N.E.K.O. 的 Core 负责主对话/实时路径，Assist 为摘要、情感、视觉、Agent 等角色提供服务。插件模型配置则独立于 Main/Agent：官方模型网关按插件声明的用途解析已保存的槽，并不自动使用主 API 或辅助 API 的密钥，也不自动注入主脑人设、历史和工具。[Core/Assist 职责](https://project-neko.online/zh-CN/config/api-providers)、[插件模型隔离与请求合同](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/docs/design/plugin-model-slots.md#L134-L158)。

普通用户的操作是：在 N.E.K.O. 的 **Plugin API / 插件 API** 页面创建或选择一个模型槽，然后在 Minecraft Autonomous 插件详情把它绑定到 `decision`；模型需实际支持文本和工具调用。有图像能力时可另外绑定 `vision`，`fast` 是可选项。可以显式配置自己已有服务的端点、模型与凭据，但“辅助 API 已填好”本身不代表这个插件绑定已就绪。独立运行规划器则使用它自己的显式模型配置。[官方配置流程](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/docs/design/plugin-model-slots.md#L11-L29)、[插件现行用户说明](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/docs/model-and-voice.md)。

`ctx.models.get_client()` 虽然返回 OpenAI 形状的客户端，官方插件网关只实现 Chat Completions；不能据此假定 `client.audio.speech.create()` 或 Realtime/Omni 音频也可通过同一个槽调用。[SDK 执行边界](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/docs/design/plugin-model-slots.md#L186-L230)。

## 本机原声为什么不要求 Omni

N.E.K.O. 同时支持实时提供方的原生音频和外部 TTS。文本会话、部分自定义/克隆音色走外部 TTS；实时原生音色可走另一条路径。因此，“文字决策模型产出台词 → 现有 TTS 合成”已经足够，Omni 只是可选语音路线，不是游戏传音的必要条件。[官方 TTS 管线](https://project-neko.online/zh-CN/architecture/tts-pipeline)。

本插件已有本机解说：台词来自现有规划响应的显式口播字段，再通过 `neko_speech.py` 提交给宿主；宿主 `mirror_assistant_speech` 会按需启动项目 TTS，把纯台词送入已有队列。这不是另开一个 Omni 对话来决定游戏动作。插件保存 `speech_id`、合成/投递状态，并明确保留 `playback_verified: false`。[口播来源](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/docs/model-and-voice.md)、[插件投递与回执](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/neko_speech.py#L145-L190)、[宿主合成入口](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_logic/core/turn.py#L3342-L3364)。

实际使用时，先确保当前角色在 N.E.K.O. 普通界面能够正常发声，再启用插件的“用当前猫娘声音解说游戏”。这只说明本机解说的配置入口；是否已真实播放仍需观察，不能把它当作附近玩家已经听见。[现行配置说明](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/blob/d2604ad55b5f9d87cb0da1e857fbebd22d753f33/docs/model-and-voice.md)。

## 服务器已有可选 TTS，但高层插件尚未接上

千灯纪服务器接入源码支持两条路径：上传外部 PCM16 WAV，或提交文字让服务器现有 TTS 合成。原生客户端已有 `say(text, {requestId, voice})`；服务器要求明确选择音色，缺少选择会报 `VOICE_NOT_SELECTED`。内部媒体服务和凭据留在服务器侧，玩家/Agent 通过自己的已认证游戏连接发请求，不需要取得服务器 TTS Key。[原生客户端](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice.mjs#L58-L70)、[服务器验证与合成分支](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/integrations/proximity-voice/src/dev/god/godvoice/PaperVoicePlugin.java#L169-L205)、[身份归属协议](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/integrations/proximity-voice/src/dev/god/godvoice/PaperVoicePlugin.java#L282-L296)。

服务器文档给出的玩家流程是先 `/voice voices` 查看，再 `/voice voice <已有音色ID>` 选择，随后 `/voice say <最多200字符>` 单独发声。`/voice auto on` 是另一个明确选择：给本人的普通聊天自动配音；默认关闭。上传同一句音频时应保持自动配音关闭，避免重复合成。以上是现有服务器接口说明，本研究没有执行这些命令。[服务器使用说明](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/integrations/proximity-voice/README.md#L11-L38)。

**当前 `mc_voice speak` 仍不是这个服务器 `say` 分支。** `ProximityVoiceLane` 要求显式 `audioProducerUrl`，向其 `POST /api/voice-artifacts` 取得完整音频，再上传；当前配置没有“服务器 TTS”选择项。因此可以开发一个默认关闭的服务器音色选项，复用已有 `say` 和同请求回执，但不能宣称现在只切一个开关就已实现。该方案无需每位用户自建 TTS 或更换 Omni，代价是使用服务器所选音色及服务器推理资源，不保证与 N.E.K.O. 桌面原声相同。[当前高层分支](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice-lane.ts#L138-L215)。

游戏语音默认关闭。`mc_voice upload` 在 `game-only` 模式可以直接使用已有 WAV，不要求音频生产服务；文件必须是 PCM16 WAV，单/双声道、8–96 kHz、0.1–30 秒、最多 4 MiB。`live-and-game` 还调用生产服务的 `/broadcast` 和 `/api/actions`，指该服务的播出队列，不能自动等同于 N.E.K.O. 桌面播放。[默认值](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/config.ts#L25)、[WAV 校验](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice.mjs#L7-L18)、[播出合同](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice-lane.ts#L220-L250)。

## 保留 N.E.K.O. 同一次合成，缺的是什么

当前通用游戏 `/speak` 返回的是 `speech_id`、`audio_queued`、`audio_completed` 等状态，没有 WAV、音频句柄或下载地址。`wait_for_audio_completion` 等待的是宿主管线投递结果，不证明真人耳听；缓存命中路径甚至明确说明完成不可观察。单纯改用 Omni 不会把这些状态变成游戏可上传的音频。[宿主响应](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_logic/core/turn.py#L3419-L3445)、[普通合成响应](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_logic/core/turn.py#L3533-L3559)、[投递完成处理](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_logic/core/tts_runtime.py#L2592-L2618)。

不能另开角色 WebSocket 当作被动音频订阅：新连接会更新角色会话标识并赋值 `mgr.websocket`，可能改变桌面输出目标。现有音频消息也使用 JSON 头加随后的二进制 PCM，并非一个现成 WAV 产物接口。[连接归属](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_routers/websocket_router.py#L692-L723)、[官方音频帧合同](https://project-neko.online/zh-CN/architecture/tts-pipeline)。

有一个值得复用的官方先例：`watch-together` 的内部实现可以把角色 TTS 缓存封装成 WAV，再提供临时 token 下载。但 `/api/watch-together/live` 要求当前有效观看会话并产生该场景的台词；其专用 `/live-audio/{token}` 不能导出任意 Minecraft `/speak` 的话语。它证明宿主已有相关实现材料，不代表通用插件合同已经存在；`voice_preview` 同样使用固定试听文本，不是本次游戏台词。[观看会话门禁](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_routers/watch_together_router.py#L77-L104)、[角色音频封装](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_logic/watch_together/live.py#L275-L305)、[专用 WAV 下载](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_routers/watch_together_router.py#L165-L174)、[固定试听文本](https://github.com/Project-N-E-K-O/N.E.K.O/blob/cf5a9d363c19bace06c5bf7c766ede273764f552/main_routers/characters_router/voice_preview.py#L574-L575)。

以下是**建议的最小公开合同，尚未实现或获官方承诺**：

1. 宿主对明确请求的游戏台词提供音频产物能力，继续拥有角色选择、音色、提供方和凭据；对同一次合成进行保留/分发，保持桌面原连接，不靠插件导入宿主内部对象或再次合成来取音频。
2. 一个稳定的 utterance UUID 关联插件、角色、会话、宿主 `speech_id` 和游戏 `requestId`；返回格式、声道、采样率、长度、SHA256、完整性、到期时间及受限的临时音频句柄。状态查询只查原请求，不重新合成；换角色/世界、停止、中断及过期有明确结果。
3. 产物只包含本次已授权的口播音频，不导出密钥、其他对话或思考字段。产物读取受插件/会话授权约束，缓存有时限与大小上限，不把任意 HTTP 音频地址当成可信输入。
4. 适配器把完整产物封装/校验为核心支持的 PCM16 WAV，走原已认证游戏连接上传；保留同一请求与哈希，超时查原回执，未知结果不换 ID 重播。若适配 `/api/voice-artifacts`，该地址是产物桥，不能直接填 N.E.K.O. `/speak` 地址或模型 API 地址。
5. 分别记录合成完成、桌面投递、游戏服务器发送及真人听见；任何一项都不冒充其他项。是否还向直播播出单独选择，不能把普通桌面解说全部自动公开给附近玩家。

上述建议依据现有宿主缓存/观看场景实现与核心上传协议推导；没有在本次研究中修改宿主。若暂时不做宿主合同，可先补接服务器 TTS；插件自带可选 TTS 则是第三种方案，需要独立显式配置端点/音色/必要凭据或本机资源，且不能保证与 N.E.K.O. 原声一致。若桌面继续原路合成，同一句还可能重复消耗 TTS。应把它标为独立语音选项，不能静默读取宿主密钥。[现有产物桥协议](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice-lane.ts#L194-L250)。

## 实际听见仍需单独验收

附近真人要在 Java 客户端安装匹配游戏版本的 Simple Voice Chat；仅服务器装插件，或仅在桌面听见 N.E.K.O.，都不能证明游戏客户端能收听。语音还使用独立 UDP 网络路径。[SVC 官方安装要求](https://dev.modrepo.de/minecraft/voicechat/wiki/installation)、[SVC 官方网络配置](https://dev.modrepo.de/minecraft/voicechat/wiki/server_config)。

仓库的 2026-10-29 记录称服务器组件已部署，并记录距离、音频包、跨维度取消和原请求去重等验证；同一记录明确说明真人麦克风/耳听尚未验收。本研究没有刷新在线部署证据，因此只能确认源码与历史记录，不能称今天附近玩家已经听见。[部署记录与证据边界](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/docs/PROXIMITY_VOICE.md#L3-L22)。

“听玩家说话”也无需强制 Omni：已有服务器 ASR 将附近语音转成文本事件，原生客户端保留真实 `speakerUuid` 和 `utteranceId`，供框架区分说话者与去重。它与输出音频是两个方向；未来验收应分别检查真人入站、N.E.K.O. 出站、近远距离、跨维度、停止和未知回执不重播。[入站设计](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/paper/docs/PROXIMITY_VOICE.md#L41-L55)、[入站身份字段](https://github.com/jcs130/minecraft-ai-friend/blob/a7bc299a74413a2d29215d148d75427b9b1e5034/packages/agent-mc-world/core/proximity-voice.mjs#L28-L36)。
