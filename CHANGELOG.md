# Changelog

## 0.6.35 — Development candidate

- 固定自主框架 0.2.30 和 MC 核心 0.5.7-rc.34：满背包时允许用安全的普通工具交互全部 16 色原版床，避免强制腾空主手而拒绝睡眠；无安全工具时仍拒绝，不丢物、不自动认定入睡。
- 核心同时带上当前主干的可见告示与体素地标感知；第三方依赖版本和观战资源保持。沿用 0.6.34 的历史退役修复及显式缓存余量。
- 类型、独立归档、安装和离线 MCP 检查分别留证；实际睡眠、持续生存及公开发布仍需现场条件与独立验收。

## 0.6.34 — Development candidate

- 固定自主框架 0.2.29：真正退役已被实际上下文窗口淘汰的完整历史交换，避免每轮重新装入再裁剪。原始日志、查询入口和最新身体回执保留。
- 框架新增显式 `autonomy.context_history_headroom_tokens`，默认 0；启用后只在真实溢出时批量退役旧历史，为后续请求保留缓存连续性。上下文容量、模型、人设及主程序不变。
- 观战、MC 核心和原生队列版本保持；离线缓存回放和实服等待时长分别验收，不能以新会话短请求代替长时生存验收。

## 0.6.33 — Development candidate

- 固定自主框架 0.2.28 和共享观战 1cbd5574：技能列表改为少量预览、按需展开；修复盾牌图标和 YUI 双手持物被动作采样过期隐藏的问题。
- 原版附魔物品接入校验过的原始纹理、图集坐标、滚动和混合规则，覆盖图标与已支持的手持模型；图标共用有界时钟，手持光效不增加独立绘制遍数。合入主干 YSM 弩朝向修复。
- MC 核心保持 0.5.7-rc.32，主脑/SDK、人格、模型和上下文不变；专用模组图集、穿戴盔甲光效和 Java 像素一致性未包含在此验收中。

## 0.6.32 — Development candidate

- 固定自主框架 0.2.27、MC 核心 0.5.7-rc.32：修复 1.21.1 混合木板无法合成箱子等物品的误判。核心按校验过的官方数据支持全部 65 类带标签合成配方，旧版保持独立。
- 合成仍需服务端实际产出与入包核验；人格、模型、上下文上限和薄适配边界保持。此候选不代表持续生存或战斗撤退已通过发布验收。

## 0.6.31 — Development candidate

- 固定自主框架 0.2.26 和通用 MC 核心 0.5.7-rc.31：优先沿现有通路导航，补齐背包分批确认、副手装备及脚格坐标修复。
- 核心归档与 npm 依赖按实际构建重新锁定；观战资源及其校验保持独立。模型、人格、近期消息与上下文设置沿用用户配置。源码测试、实际部署和持续生存分别验收。

## 0.6.30 — Development candidate

- 固定自主框架 0.2.25：为兼容的 Chat 模型增加显式 `planner.reasoning_history="current_turn"` 选项，避免后续轮次反复重放已完成轮次的内部推理。默认仍完整保留，其他原生协议不能启用此选项。
- 当前工具调用链的推理、正文、工具结果、人格和记忆保持，原始推理回执仍留档；上下文上限不变。此选项的输入节省需与现场延迟及生存效果分别验收。

## 0.6.29 — Development candidate

- 固定自主框架 0.2.24：已完成查询/试算的确切结果沿用有界五分钟恢复窗口，避免 60 秒以上的模型推理返回时答案已过期，又重复读取同一现场。
- `mc_scout` 与 `mc_do` 的只读组合共用同一防重键，换入口不再重排相同试算；普通试算原文和查询入口保留，空回执不算已有答案，真实身体动作、变化后的现场与用户停止边界保持。

## 0.6.28 — Development candidate

- 固定自主框架 0.2.23：相同箱子的同一取物操作两次实测失败且背包不变时，保留按步骤的短期恢复证据；走路、重新开箱、改解说或后续任务不再掩盖该失败。
- 仅在当前连接、账号/世界、死亡代次和测量一致时短期拒绝重复批次；换容器、物品/数量、取得新材料或前置采集仍可正常执行。原始回执、128K 配置和身体/观战依赖保持。

## 0.6.27 — Development candidate

- 固定自主框架 0.2.22：完整当前目标放到动态末尾，阶段提案变化不再改动历史之前的缓存前缀，保留用户目标优先级和原文。
- 增加固定头部、工具目录与首条历史组的摘要指纹，区分目标变化、工具变化和真实窗口淘汰；不记录私有提示词。保留 0.6.26 的确切证据复用、128K 配置及身体/观战依赖。

## 0.6.26 — Development candidate

- 固定自主框架 0.2.21：完整上下文只保存一次确切终态证据，动态尾部在源仍包含时引用；淘汰后恢复原文，避免失效引用。
- 工具回执仅消除原生包装器中与主文本完全相同的长副本；人格、记忆、聊天、当前事实和原始日志完整保留，128K 配置不变。
- 新增无私有内容的证据复用计数；身体、观战、Neko 主程序/SDK 及模型固定配置保持，实际性能与长期生存分别验收。

## 0.6.25 — Development candidate

- 复盘模型等待时间服从原始复盘机会的剩余有效期，修复插件固定 25 秒提前取消已配置 180 秒本地模型请求的问题；有界纠正共享同一个截止时间，不续期。
- 失败回执只记录超时、连接、HTTP、网关或无效响应类别与等待预算，不记录凭据、完整异常或思考；未知结果不重投，Neko 主程序、SDK 和游戏执行器不随此改动重启。

## 0.6.24 — Development candidate

- 主脑结构化复盘收到明确的阶段拒绝时，把原始工具错误交回同一次对话，最多纠正一次；避免无可修订阶段却反复 revise，直到超时退避和语音静默。
- 纠正前后重新检查停止、当前账号、原生连接和用户意图；传输超时、未知结果及已受理事务不重试。只转交工具事务，思考和工具前文字仍不进入语音。
- 固定自主框架 0.2.20；游戏执行器、Neko 主程序/SDK 和本地模型保持独立。

## 0.6.23 — Development candidate

- 固定自主框架 0.2.20：成功回执也按独立测量检查效果，避免“背包已有目标物品、没有新合成”反复提交同一计划。
- 两次相同计划且现场没有变化时返回已有证据；物品消耗、位置变化或未知测量仍允许正常工作，由 Agent 选择后续行为。
- 保留 128K 配置能力、原生身体与观战依赖；不把重复拦截、离线测试或任务完成当作持续生存验收。

## 0.6.22 — Development candidate

- 固定自主框架 0.2.19：完整历史按所选模型的 token 计数保留，修复字节上界提前挤掉缓存前缀的问题；计数不可用时保留保守回退。
- 兼容 Chat 服务可显式设置 `reasoning_budget_tokens`，限制思考长度并给最终工具参数预留输出空间。默认不发送，不改变宿主或其他用户的模型配置。
- 原生身体与观战固定依赖保持；实际延迟和自主生存继续分别验收，不把离线动作提议当作现场完成。

## 0.6.21 — Development candidate

- 固定自主框架 0.2.18：观察和试算流量不再优先挤掉身体动作回执；完整上下文按整条记录裁剪旧观察，保留窗口能容纳的人格记忆、当前意图和动作结果。
- 原始回执仍可查询，省略数量明确记录；任务受理或完成不自动视为目标成功。保留已有恢复窗口与身体动作入口修复，核心和观战依赖不变。

## 0.6.20 — Development candidate

- 固定自主框架 0.2.17：重复只读观察不会隐藏 mc_do 身体动作入口；恢复窗口覆盖慢推理与调度，避免前一个查询在其他查询让位前重新开放。
- 相同读请求仍复用原始回执，新事实、连接变化和在途任务继续放行。保留 0.6.19 的完整上下文恢复提示与混合试算去重，核心和观战依赖不变。

## 0.6.19 — Development candidate

- 固定自主框架 0.2.16：重复背包/队列查询共同进入有界恢复窗口；混合体素与路线试算复用真实原始回执；完整上下文补齐行动恢复提示。
- 新事实、连接变化或超时恢复查询，正常在途任务仍能读取状态。行为选择保留给 Agent；不写死路线、配方或生活目标。核心与观战依赖不变，长期生存仍需现场验收。

## 0.6.18 — Development candidate

- 固定框架 0.2.15 与核心 0.5.7-rc.20.env.1 最小回补：死亡或重生等待期间不再重复启动环境自救；死亡撤销其持有的逃生控制和水下历史，避免把重生误报成自救成功。
- 保持既有依赖、观战资源、人格和模型路由；不修改 Neko 主程序或 SDK。源码与包校验不代表长期生存验收通过，模型接口账户错误仍需单独解决。

## 0.6.17 — Development candidate

- 固定框架 0.2.14：死亡复盘的读取/保存契约要求完整记录 ID；缺参时明确提示修正，当前上下文提供确切读取参数，避免把缺参误报为历史记录不存在而丢失总结。
- 保持核心 rc.20、观战及宿主接口，未改 Neko 主程序/SDK。复盘内容仍是待验证的经验，不代表连续生存已通过验收。

## 0.6.16 — Development candidate

- 固定框架 0.2.13 与共享观战 ef251a6c：断线后清理旧观战服务全部 HTTP 连接，避免未进入画面流的浏览器连接阻塞重连、留下空白画面。
- 浏览器构建固定源码工作目录，消除宿主工作目录引起的产物哈希变化及 Three.js 依赖误报。核心保持 rc.20，Neko 主程序、SDK、模型及游戏策略不变。

## 0.6.15 — Development candidate

- 固定框架 0.2.12 与核心 0.5.7-rc.20：合成窗口被关闭或替换时，仍有效的原生任务以受阻终态结束，不再永久占据执行槽；真实取消、未知点击和禁止重放保持原语义。
- 同步上游导航安全检查点、水下观察与私聊归属修复。Neko 主程序和 SDK 无改动；源码、打包检查和现场连续游玩分别验收。

## 0.6.14 — Development candidate

- 自动复盘默认通过官方模型 SDK 接收结构化高层判断，复用当前角色的公开人格、已选记忆和近期消息；不再用普通聊天回复承载内部复盘。
- 只有明确的 `spoken_text` 进入现有角色语音出口，自由文本与思考字段不会被自动念出；不新增解说模型循环，保留普通用户聊天和旧通知模式。
- 补充停止、替换目标、迟到回复、模型不可用与思考标签的回归；Neko 主程序、SDK、模型服务和游戏核心不随此修复改动或重启。

## 0.6.13 — Development candidate

- 固定框架 0.2.11：Windows 状态读取短时占用时，在 250 毫秒上限内重试同一原子快照；永久权限错误仍保留首次诊断并安全停止，不重放游戏动作。
- 保留完整上下文模式、已提供近期原文与显式在线模型配置。

## 0.6.12 — Development candidate

- 固定独立框架 0.2.10，配置面板增加完整上下文模式：关闭额外的消息/历史/工具结果裁剪，保留实际窗口预算与省略诊断。
- 模型窗口可显式填写服务支持的容量；独立规划器的模型切换不改变 Neko 主程序、SDK 或角色语音。
- 保持核心 rc.14 与观战 8e72a554 固定版本；源码与离线验证通过不等于长期生存验收或公开发布。

## 0.6.11 — Development candidate

- Recognize actual Java 1.21.1 registered incoming private-chat templates in
  native events, retained message history and viewer labels. Keep public quotes
  and conflicting sender identities separate.
- Retain the native event references actually included in each decision receipt,
  without copying private message text into diagnostic metadata.
- Pin the checked independent core/runtime repair; Neko main/SDK are unchanged.

## 0.6.10 — Development candidate

- Preserve localized private-message identity in the independent Minecraft core.
- Prioritize important native events and acknowledge only those actually shown
  to the planner; retain omitted events and native original-query handles.
- Repair real engine-child decision attribution and cadence-aware player
  interpolation, including original YSM display heading.
- Pin checked core/viewer/autonomy inputs. Neko main and SDK are unchanged;
  live private reception and sustained survival require separate evidence.

## 0.6.9 — Development candidate

- Keep asynchronously mounted terrain maps above the decision panel without
  moving stable canvases every frame.
- Carry actual planner/operator attribution through the independent runtime,
  MCP and core into viewer events; anonymous decisions remain unknown.
- Pin the matching core and viewer source builds. Neko main/SDK are unchanged.
  Gameplay acceptance remains separate from source and package checks.

## 0.6.8 — Development candidate

- Consume native observed-effect evidence in the independent autonomy framework.
  Accepted actions and build previews no longer erase read history; real changes
  can reset it. Repeated identical ineffective work receives a bounded recovery
  response and the failed skill's native help instead of another body dispatch.
- Preserve original receipts and unknown-delivery fences. Core/viewer pins and
  Neko main/SDK remain unchanged; live survival still requires separate acceptance.

## 0.6.7 — Development candidate

- Use original compass frames from observed own-player state and original inactive crossbow GUI textures.

- Prevent late server status replies from doubling the refresh interval and
  expiring health/mana. Bundle the original backpack profile texture and render
  its exact 1.21.1 head/hat model rather than a generic item label.
- Pin the shared core repair that applies explicit server action denials to the
  exact native block and preserves the original error for replanning.
- Consume the shared SNBT text fix and original untrimmed armor icons, plus an
  independently checked optional server item catalog.
- Bundle Qiandengji's original custom item icons/models/textures. Keep its own
  connection attestation through death and opt into bounded read-only status
  refresh. Ordinary servers gain no custom protocol, queries or resource rules.
- Validate every bundled extension resource before selecting the pack. Neko
  main/SDK and model processes remain outside the plugin's lifecycle.

## 0.6.2 — Release preparation

### Fixed
- Keep a planning-voice timer's own bounded HTTP/audio task alive until completion. The official host creates a separate event loop per timer callback, so returning immediately previously cancelled an enqueued line before submission. Waiting happens in that voice timer, independently of the MC controller and main brain; stop/expiry/unknown-output protections remain intact.
- Add a regression reproducing return-before-delivery, retaining the tool-only narration support and the existing official TTS/persona/model-slot boundaries.

## 0.6.1 — Release preparation

### Fixed
- Pin framework 0.2.1: models that return only tool calls can include the same-decision line in an optional host-only `mc_do._spoken_text` field. It is removed before the original native argument validation and dispatch; assistant-content narration remains supported. No extra generation or Minecraft chat message is introduced.
- Retain 0.6.0's public model-slot, character-persona and existing-voice integration. Candidate artifacts remain separate from public Release and Market approval.

## 0.6.0 — Release preparation

### Added
- Forward optional natural commentary from the existing MC planning response through Neko's public character and game-speech APIs. Ordinary speech no longer requires a completed main-brain review or an extra narration model call; voice synthesis runs independently of body work.
- Follow the selected user's current cat when the role is blank. Share only public persona fields; retain the cat's existing TTS configuration without reading voice IDs or supplier credentials.
- Add panel controls for same-decision speech, explicit local host address and pacing, plus installation guidance distinguishing Core, Assist and the official Plugin API model bindings.

### Safety and verification
- Pin the host-neutral framework's bounded, once-claimed speech outbox. Stop, actor/world/runtime changes, new intent, death and expiry invalidate old lines; unknown delivery is never replayed.
- This is a release candidate preparation. Public Release publication, Market approval, clean-machine installation and long-term gameplay remain separate acceptance steps.

## 0.5.65 — Internal candidate

- Pin autonomy 0.1.89: a review proven never offered or inspected receives fresh evidence and a new ID after expiration. Offline time no longer creates a false host-acknowledgement failure and five-minute silence. Actual, rejected and unknown deliveries retain their existing bounds; no action or old acknowledgement is replayed.
- Retain 0.5.64's original YSM UV, terrain preparation, optional-context-read and native reconnect continuity repairs. Source checks, actual playback/action receipts and long-term survival remain separate.

## 0.5.64 — Internal candidate

### Fixed
- Pin autonomy 0.1.88 / shared viewer 3553c60d: yield terrain preparation through browser tasks so throttled painting does not hold up a complete terrain commit. Keep the prior recovery-budget, exact YSM UV and bounded column-cache fixes.
- An intermittent denied optional status read no longer aborts the strategic review timer; unavailable recent conversation material stays unavailable, without altering ownership or replaying work.

- Keep the owned runtime alive through native connecting/retrying phases, suspend model/action work on unavailable facts and require fresh queue/body state after recovery. Explicit stop and stopped/unknown states retain their fences.

## 0.5.63 — Internal candidate

### Fixed
- Keep the review ID and required death reflection visible in short host notification previews; avoid repeating the full standing goal there.
- Pin framework 0.1.86: preserve individually bounded live facts and put short recovery completion requirements first. Missing reflections return the same bound contract without acknowledging or dispatching anything.
- Retain viewer 43e23250, including the original YSM crown/chin UV conversion fix and bounded terrain caches. Source validation is separate from actual deployment and gameplay acceptance.

## 0.5.62 — Internal candidate

### Fixed
- A missing public SDK model gateway no longer crashes explicit direct planning or the model-check entry; unavailable host planning stays explicit.
- Pin framework 0.1.85: unique tool names, provider-compatible tuple projection with original native validation, bounded safe HTTP rejection diagnostics and queue-preserving backoff.
- Pin viewer 43e23250: bounded received/decoded terrain caches recover normally beyond 512 columns and preserve updates, block entities and unload semantics.
- Refresh visible control panels periodically without polling hidden panels or overwriting an advanced edit. Exclude author backup files from packages.
- Clarify exact offline pairing, Windows TOML paths, inherited API-key environments and official metadata rebuild/import. Keep source validation distinct from recipient and gameplay acceptance.

## 0.5.53 — Internal candidate

- Pin reviewed canonical autonomy 0.1.77 at `ed94de1277ff0bf61182733374ec8ac8db7e8413` (final recovery fix2), retaining exact checked core .39 / `3ee62ca2` and packaged viewer c799.
- Consume bounded private first-error diagnostics and the pending operator-acknowledgement startup fence. Recovery remains an explicit offline operator CLI action; the adapter adds no recovery tool, automatic acknowledgement or replay. Accepted-only old native work remains unknown.
- Preserve recent-context filtering, profile leases, speech admission, native queue ownership and disabled automatic startup. Source/package checks do not cure the original PermissionError or establish live recovery. See `docs/integration-0.5.53-20261017.md` for provenance and deployment order.

## 0.5.52 — Internal candidate

- Refresh bounded public same-character conversation context and independently fresh configured persona through the existing observer, including when no review is pending. Canonical autonomy reads the private file at every body model round; historical language is never a new command or verified world fact.
- Suppress exact explicit-output repeats within 300 seconds for positively bound ordinary automatic opportunities. Keep same-opportunity receipts, urgent/manual/unknown paths and independent action dispatch. Accepted or unknown output never proves playback.
- Pin reviewed autonomy 0.1.76 at `bb538c7bc1e1b4bc33e8b38aceaf27079a6ab0df`, including exact checked core .39 / `3ee62ca2`. Default external viewer c799 remains separate. Source/package checks do not establish live acceptance.

## 0.5.51 — Internal candidate

- Pin reachable canonical `6178073c38e671771a90cf507e492fe3b23841a0` / autonomy0.1.73 with exact corec9ac/.32 and shared viewerc799 source/build receipts. Preserve the bundled speaking skill, original YUI assets and reviewed GUI producer/abort/stow contracts.
- Default public context settings to65536, document optional131072 on supporting services and preserve explicit other valid values. Current service capacity remains an independent configuration constraint.
- Source-only incoming core.33 method capabilities are separate from the frozen.32 distribution. Offline candidate checks do not establish deployment, full scene/voice coverage or survival.

## 0.5.50 — Internal candidate

- Pin reviewed autonomy 0.1.71 at `6cbff24070a2ff4ee224e6d5bf94e82cebe4a914`, with frozen engine-only core .24 from exact `2723d39f8129a6d2f87a773832289888dda1d51c` and unchanged viewer `567d95e6`.
- Consume optional viewer-state persistence isolation: failed writes preserve the complete prior snapshot; normal publication recovers using current state, and obsolete/disposed attachments cannot publish. Preserve reviewed short-final, death, ownership and no-replay behavior.
- Retain disabled startup/gameplay defaults, original bundled YUI assets, saved appearance choices and external configuration. Later incoming core source .25 is preserved in canonical history but excluded from this frozen core artifact; its delivery remains required follow-up. Exact hashes distinguish concurrent .24 source labels.
- Offline checks do not establish natural ACK, playback, busy-file live continuity, all animations or sustained survival. No release tag or Market publication.

## 0.5.49 — Internal candidate

- Pin reviewed autonomy 0.1.70 at `ec20aef983cdd25fe6e124adf7a95ad2040bca15`, retaining immutable engine-only core .13 and shared viewer `567d95e6`.
- Inspect exposes the evidence-bound minimal final completion contract. Finish the same-brain tool transaction before optional narration; preserve authored reasons, goals, death lesson/deferral, public character context and optional speech-before-dispatch without audio waits or replay.
- Keep startup/gameplay disabled by default. Offline package/SDK checks do not establish natural provider final ACK, playback, complete scene fidelity or sustained survival. No release tag or Market publication.

## 0.5.48 — Internal candidate

- Pin reviewed autonomy 0.1.69 at `2b0db6308c93a5b155e17abe0ed5d4708424fe20` and immutable engine-only core 0.5.7-dev.20261016.13. Consume reviewed fresh-connection/current-death recovery and strategic applicability repairs without copying gameplay policy into the adapter.
- Default Neko embedded Web appearance to original bundled YUI YSM; preserve explicit defaults and saved browser choices, including server-follow. Expose Web-only choice/status and canonical `/3dview/` links. Shared viewer `567d95e6` carries validated defaults and opaque server/account scopes; ambiguous old preferences require one-time reselection, not guessed migration.
- Require evidence for legacy episode-only lessons while retaining compact evidence references and honest deferral. Log only categorical review entry/completion/exception diagnostics with plugin `call_id`, validated review/command IDs and evidence-reference presence. Preserve original results, exceptions, acknowledgement and speech/action dispatch semantics.
- Retain public speech-ID/audio flags with playback unverified. Full entity rendering, natural host speech/final-ACK compliance, swimming and sustained survival remain acceptance work. New upstream core .21 is separately scheduled for final integration; this candidate deliberately keeps the reviewed .13 artifact. No release tag or Market publication.

## 0.5.47 — Internal candidate

- Use autonomy 0.1.67 compact inspection and bounded original evidence pages. Final decisions use a short same-brain contract with optional natural speech and validated compact death references; ordinary Neko finals require a fresh inspection.
- Bind the configured public character during inspection independently of strategic acknowledgement. Preserve fresh explicit persona, current intent and selected memory; static identity never represents memory recall or revives expired intent.
- Retain validated public speech ID/audio queue/completion metadata alongside the text hash. Queued output is not playback. Core .9 remains pinned and live model/speech acceptance is still separate.

## 0.5.46 — Internal candidate

- Pin autonomy 0.1.66 at `fd205ba5f3cb8957a70a3709fa42c0beef6c2fd4` with unchanged checked core 0.5.7-dev.20261016.9 inputs. Pending death decisions require an inspected evidence-based lesson or explicit justified deferral before acknowledgement, speech or goal delivery; missing reflection can be corrected on the same heartbeat.
- Expose lesson/deferral requirements through the public SDK schema and tool help. Freshly inspect and complete legacy acknowledged pending reflections without replaying their original goal or speech. Historical lessons remain hypotheses with improvement unverified.
- Normal-drain the independent body to 0.1.66 as well: its transactional history writer preserves concurrent host reflection/completion fields. Reloading only the adapter leaves the old 0.1.65 producer's stale-write race. Startup/autonomy remain disabled by default; package checks do not prove live recovery or playback.

## 0.5.45 — Internal candidate

- Pin reviewed autonomy 0.1.64 at `784047e72a67d616e8847c3032b3b79c4d0d672e` so installation provides the heartbeat idle-presence and final-review speech/death-reflection APIs already used by this adapter.
- Keep its checked core 0.5.7-dev.20261016.6 pin and refresh matching installation metadata. This candidate is not deployed or released; startup/autonomy remain disabled by default.

## 0.5.44 — Internal candidate

- Pin autonomy 0.1.61 and core 0.5.7-dev.20261016.2. New operation evidence sums duplicate inventory stacks, preserves unknown inventory and leaves historical records unchanged.
- Preserve the canonical memory read preference through full dashboard draft saves, so typed field feedback reaches the panel.
- Explain local installation metadata in Chinese and distinguish external executor resources from local configuration; actual scene and role binding remain to be verified in the viewer.
- Refresh exact committed source and archive pins. Default startup/autonomy remain disabled; no public release or Market submission.

## 0.5.43 — Internal candidate

- Pin autonomy 0.1.60 and reviewed core 0.5.7-dev.20261016.1; expose bounded installation metadata without repeated full runtime hashes. Explicit starts still verify the pinned runtime.
- Return safe field-specific configuration guidance, retain rejected drafts, and explain local addresses and Microsoft human authorization. Public-server shortcuts preserve the user account and authentication choice.
- Document exact locally staged core/viewer/optional sound assets and reproducible setup. No public artifact URLs, clean-machine guarantee, release or Market submission are claimed.
- Exclude development/private artifacts while retaining only Certifi's public CA PEM bundle, so packaged direct-model clients can construct their TLS context.

## 0.5.29 — Unreleased

- Consume checked autonomy 0.1.46/core 0.5.2, preserving current main's Java 1.21.1 build/registry/login defaults and the existing knowledge, food and queue fixes.
- Synchronize shared viewer main `4b59ce79`: the native entry now uses the common toolbar, display settings, chat history and photo entry. Actual capture provider and night vision gaps stay explicit.
- Default to ordinary Mineflayer data. Optional server visuals follow validated received capabilities/state and exact resources; hostname/chat/profile guesses cannot enable Qiandengji abilities or mana. Loss/reset removes stale panels.
- Add public-SDK-only host boundary regressions. No Neko main program/SDK source patch, second game account, extra model loop or host restart is introduced.

## 0.5.28 — Unreleased

- Make vanilla Java 1.21.1 the primary optimization/acceptance target; consume autonomy 0.1.45 and checked core 0.5.1 from pinned main commits.
- Expose the core's bounded `mc_knowledge` search/get for versioned food, cooking, regeneration and full registered item/block/crafting references. Retrieval defaults to local reference data; historical memory and explicitly configured vector providers remain separate. No extra model request or duplicated gameplay policy in this adapter.
- Prefer an available cooked counterpart during routine eating, keep emergency food usable, and include baseline hunger/saturation, cooking gains and harmful-food warnings in current ration facts. Ominous bottles are not rations. Explicit eat requests are not silently rewritten.

- Live follow-up: infer read-only search/get when action is omitted and expose verified cooking/charcoal recipes through recipe-filtered search.

## 0.5.27 — Unreleased

- Consume autonomy 0.1.43 and checked core 0.4.7. Every named craft step is checked for a known recipe before accepting a batch, so a later nonexistent recipe cannot consume materials in earlier steps or interrupt existing work.
- Preserve deferred material checks, explicit custom grids, tagged recipes, smithing and unknown recipe-reader states. This is a specific admission fix, not a claim that autonomous planning or sustained survival is fully reliable.

## 0.5.26 — Unreleased

- Consume autonomy 0.1.42: reuse an attached internal viewer after runtime handover, with a bounded reconnect grace before opening a new page. This prevents repeated automatic opens from exhausting the four read-only stream connections.
- Keep the checked 0.4.6 body, synchronized food-reserve facts and private source/build evidence. This change does not claim complete visualization or sustained survival.

## 0.5.23 — Unreleased

- Consume autonomy 0.1.39 and checked core 0.4.4: keep concise native action parameter meanings, return a legal bounded voxel retry, and expose repeated read-only activity to the optional planner. Game decisions and body execution remain in the independent framework.
- Preserve the deployed fall safeguards, explicit stops and unknown-dispatch protection. Offline validation does not establish sustained survival.

## 0.5.22 — Unreleased

- Consume autonomy 0.1.38 and the hash-checked independent 0.4.3 body: reject damaging dry navigation drops, brake predicted cliff falls with real physics, and remove the lower-goal deep-fall exemption. The thin adapter owns no movement policy.
- Preserve source/build/deployment evidence separately; this does not claim sustained survival or publish a Market release.

## 0.5.20 — Unreleased

- Consume autonomy 0.1.36 so manually inserted native tasks appear in the same public timeline as planner tasks. Queue entries reuse their public skill summary, and each rejection keeps one sanitized diagnostic row.

## 0.5.19 — Unreleased

- Consume autonomy 0.1.35: expose bounded public native queue and actual action/terminal history to the configured shared viewer. Full arguments, private planner context and raw errors remain local.
- Keep inventory, crafting, trading, survival, terrain and operation rendering in mc-visual-console; the plugin remains a thin host adapter. The independently pinned native 0.4.0 body is unchanged.

## 0.5.18 — Unreleased

- Consume autonomy 0.1.34: inject bounded public goal, tool/skill and real receipt state into the explicitly configured native viewer. Private planner context and configuration stay out of the viewer projection.
- Use the shared viewer's same-body path/trail/input and observed hand-motion integration. Rendering remains in `mc-visual-console`; no duplicate renderer or body queue is added to the plugin.
- Pass the shared Mineflayer window projection for original inventory/crafting layouts, actual cursor stacks, slot-click playback and received furnace progress.
- Preserve the separately verified native backend pin and service ownership; unrelated concurrent native-core source updates are not silently deployed.

## 0.5.17 — Unreleased

- Consume autonomy 0.1.32: a newly queued observation ends the planning turn even while feedback awaits its first body plan. Wait for the actual native result before deciding again, without consuming feedback queue policy or interrupting unrelated native work.

## 0.5.16 — Unreleased

- Consume autonomy 0.1.31: keep a rejected body plan across intervening failed observations, cached retries and corrected reads. A read error cannot overwrite the action error that still needs correction.
- Allow explicit `tool_choice=required` for compatible Chat/Responses planners, so supported providers can prevent text-only plans without forcing a particular Minecraft action. Defaults remain unchanged.
- Preserve concurrent upstream source while keeping the separately verified Mineflayer core pin. The optional new Java client body is not enabled by this deployment.

## 0.5.15 — Unreleased

- Consume autonomy 0.1.29: queued observations retain rejected body-plan evidence, including after history eviction, and rejected batches explain that earlier steps did not run.
- Clarify the Neko transport: autonomous heartbeat strategy uses the existing review/inspect/revise port; the separate intent tool relays new user goals and must not replay stale stages or entity IDs. This wording does not guarantee model compliance.
- Pin the checked independent core with distinct live-chicken search receipts, preserving food item labels and native retry guards.

## 0.5.14 — Unreleased

- Put the current speaking policy and 30-character highlight limit directly at the front of the small notification preview. Tool-result-only instructions were insufficient when the main brain spoke without inspecting; same-review retries explicitly request tool confirmation without repeating narration.

## 0.5.13 — Unreleased

- Consume autonomy 0.1.28 for fresh commentary signals, preserving full facts for strategic decisions while ignoring inventory counts, durability and read-only task churn.
- Share ordinary commentary timing with strategic heartbeats; allow a new critical-health/death warning without repeating the same warning. Ask for one natural highlight in 1–2 short sentences instead of inventory/inspection readouts.
- Keep official host voice and normal user conversation. Speaking opportunities, strategic acknowledgement, native completion and actual playback remain separate; the public SDK does not enforce silent tool-only output.

## 0.5.8 — Unreleased

- Consume autonomy 0.1.22, preserving complete native action/scout parameter structure while omitting repeated manuals and retaining coordinate/angle units.
- Preserve existing model, game, queue and explicit stop policies. Schema/context verification remains separate from real survival acceptance.

## 0.5.7 — Unreleased

- Consume autonomy 0.1.21 for explicit goal provenance, paged original parent goals and complete rejected-call history.
- Mark manual panel goals as user-sourced while preserving legacy UUID retries and unknown model-intent provenance. Show a bounded current-user-goal cue and expose framework lineage inspection through the existing review tool.
- Document the installed Neko SDK's separate review-history limitation and a forwardable upstream capability request; do not impersonate the legacy plugin or modify host SDK internals.

## 0.5.6 — Unreleased

- Consume shared autonomy 0.1.20, preserving native scalar parameter constraints in compact model tools while keeping full manuals progressive.
- Add an explicit control-panel action to resume Neko participation after an external runtime restart. Require its account lease and fresh connected evidence; preserve stop on stale state, configuration changes or concurrent stop.
- Show the separate host stop flag. Resume does not start a game, dispatch a task, reset review history or invoke a model; the existing framework review transport continues normally afterward.
- Offline checks and deployment do not establish sustained survival, food acquisition or voice playback. No Release or Market publication.

## 0.5.2 — Unreleased

- Consume shared agent-mc-autonomy 0.1.16 for native Chat/Responses, Claude and Gemini model APIs; add explicit domestic provider presets, streaming and protocol-specific parameters.
- Add optional official OpenAI/Google OAuth, OS credential storage and refresh in the shared framework. Default Neko model binding is unchanged; no host account files are reused.
- Add direct model settings, explicit catalog/tool checks and pre-start validation to the hosted panel. Provider implementation stays out of the Neko adapter and Minecraft body.
- Offline protocol, authentication and hosted-form checks do not prove cloud account access or live gameplay. No release/Market publication or running agent reload.

## 0.5.1 — Unreleased

- Consume the canonical shared core through agent-mc-autonomy 0.1.15: inventory recovery, generic tactics and scoped game memory, with no plugin-specific core patch/compiler.
- Expose local keyword, optional embedding and external Mem0/Bailian/PowerContext/HTTP memory configuration in the existing settings panel. Provider logic, evidence and revisions remain in agent-mc-world.
- Default to local retrieval; forward only the configured memory key environment variable. External failures preserve local notes and report degraded retrieval. No game, model or service starts during checks.
- Pin the archive and build/type receipts, preserve old world identities and permission channels, and validate the disconnected Python-to-MCP channel. Source checks do not establish live gameplay or cloud connectivity.

## 0.5.0 — Unreleased

- Move the complete autonomous runtime and strategic review lifecycle into minecraft-ai-friend/packages/agent-mc-autonomy. Consume one pinned dependency; remove gameplay/viewer assembly copies from the Neko adapter.

- Add opt-in main-character strategic heartbeats with useful fresh facts, material/terminal changes, periodic review and a public inspect/continue/safe-insert decision tool. Preserve independent execution and official host speech.
- Persist review IDs and acknowledgements, bound retries, suppress duplicate in-flight goals and fence stale reviews against new user intent in the same mailbox transaction. Expose heartbeat settings/results in the existing Neko panel.
- Declare separate Neko configuration/control and observation panels through public UI APIs, with a legacy static UI entry.
- Add real bounded runtime statistics, health/food/position observations, native queue, latency chart and decision/receipt details. Stale reads and failed runs remain visible.
- Embed a configured modern viewer only after an explicit click, with separate-window and unload controls. No viewer deployment, second account or player-binding claim is implied.
- Allow validated viewer-only settings to change without stopping an embedded worker; keep runtime changes blocked while it is active.
- Pause observation reads when the page or its Neko panel is hidden. Render observations as text and reject unsafe viewer URLs.
- Add optional exact-version viewer assembly over the current player's native connection; request one browser open after joining. Keep full browser rendering separate from identity/data validation.
- Forward fresh, deduplicated game changes through the public Neko notification API, with an explicit narration action and configurable role/rate limit. Verified official online voice delivery and desktop playback receipts.
- Bound failure diagnostics and spatial previews while preserving original evidence, completed scout results and the latest synchronous inventory receipt.
- Restrict action/scout queue policies consistently. Reject invalid replacement locally with a correctable receipt instead of disconnecting the body.
- Verify the actual Neko manager tabs, public assets/context, viewer-only save, responsive layout and isolated viewer loading. Sustained vanilla survival and complete scene parity remain unverified.

## 0.4.0 — Unreleased

- Add public Neko `decision`, optional `vision` and `fast` model routing without reading provider credentials.
- Fall back to text on unavailable/invalid vision responses; keep native observation/queues alive when decision is unbound.
- Consume one fresh core PNG at the request tail with a separate image budget; standalone vision capability is explicit.
- Add optional bounded System One (remote Jev/local compatible Decider) or Neko-slot focus selection, with rules as the default and failure fallback. Native physical control stays in the core.
- Add a Hosted TSX panel for validated settings, natural-language goals and bounded real observations, decision/receipt samples, usage and latency.
- Add explicit text/tool and synthetic-image model diagnostics through the same SDK adapter; no game commands are dispatched.
- Keep short numeric/coordinate descriptions, prioritize survival facts under pressure and load script/artifact schemas on demand; one image still fits the default context budget.
- Reject empty provider successes before dispatch and record them for bounded recovery.
- Verify real public-gateway text/tool calls, missing-vision text fallback, bound-vision recognition and hosted settings/context APIs. Browser visual acceptance and paid Jev inference remain unverified.

## 0.3.0 — Development snapshot

### Added

- Independent runtime and explicit HTTP planner configuration, without a N.E.K.O installation.
- Natural-language goals and feedback: insert at native checkpoints and resume, or explicitly replace current work.
- Shared observations and deduplicated command receipts for Neko to guide and narrate an external runtime.
- Continuous event-driven planning with `max_decisions=0`, and planner-free execution of already planned native tasks.
- Public Neko LLM tools for compact state/fact pages, natural-language intents and explicit stop.
- Private rejected-inference diagnostics and bounded recovery before any game action is dispatched.

### Changed

- Neko is optional in external mode; closing it does not stop the independently launched runtime.
- Newly planned actions preserve native queued work by default. Unknown delivery still blocks automatic replay.
- Embedded mode still supports the public `decision` slot. This slot supplies planning inference, not Neko's full main conversation.
- Keep the latest tool receipt when a large fixed prefix previously evicted all error feedback.
- Advertise native scouting directly and reject standing-goal completion reports without disconnecting the body.

### Acceptance

- Development build only. Vanilla 1.21.1 login, collection, crafting and Neko intent delivery were observed; see the dated live-acceptance report.
- Long-running survival, automatic game narration and viewer binding remain unverified. Planner-reported goal success stays explicitly unverified.
