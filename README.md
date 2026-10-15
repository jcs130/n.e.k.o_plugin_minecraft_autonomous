# Minecraft Autonomous · 我的世界自主生存

Minecraft 自主框架的薄适配插件，面向 [N.E.K.O](https://github.com/Project-N-E-K-O/N.E.K.O) 的接入插件。
Neko 提供高层目标、策略、角色演出与语音；独立框架细化规划并驱动原生执行队列。
没有用户新消息时继续推进目标；新反馈可以在检查点插入，或明确替换当前行为。
完整框架已归入 [minecraft-ai-friend/packages/agent-mc-autonomy](https://github.com/jcs130/minecraft-ai-friend/tree/main/packages/agent-mc-autonomy)，不安装、不启动 Neko 也能运行。本插件按固定提交依赖它；不再保存控制器、调度器或上下文策略的副本。
可配置其他人的兼容服务器，不要求在本机开服。
Minecraft 执行插件由 **jcs130** 编写与维护，源码来自你的 `minecraft-ai-friend` 项目。

**0.5.38 发布准备版：默认使用 Mineflayer，主力优化与验收版本为 Java 1.21.1。固定独立框架 0.1.54 和经校验核心 0.5.5；主脑的人格、当前关注和选出的相关记忆进入实际身体规划，解说沿用同一个角色。支持结构化性格档案与自定义提示词，空档案明确回退到主脑投影。生存指南按需参考，角色可按兴趣选择活动；明确用户目标优先。保留原生队列、动作连续衔接、失败退避、原文查询、知识检索、熟食优先和多厂商模型。新增真实死亡的延迟重生、证据复盘及分域记忆，观战支持平滑移动、短轨迹和背包操作回放。千灯纪等扩展按实际校验数据及匹配资源启用。不修改 Neko 主程序或 SDK。长期自主生活与完整场景一致性仍在验收；见 [本次维护说明](docs/gameplay-experience-20261015.md) 和 [发布准备](docs/release-candidate-20261015.md)。**
默认关闭自主游玩，必须显式执行独立 `run` 或内嵌 `start`。普通源码更新不自动开始游戏；Release/Market 仍需单独发布。
YUI 普通 slim 皮肤和原创 YSM 模型默认随插件附带，内嵌运行自动注册。在观战页「人物模型」选择；默认跟随服务器，显式选择只改变 Web 显示。独立运行可将 `viewer.bundled_appearance_catalog_file` 指向安装目录的 `assets/appearances/catalog.json`，无需另下载这些外观素材。
实际结果及失败记录见 [原版服验收](docs/vanilla-live-acceptance-2026-10-13.md)。

| 项目 | 内容 |
| --- | --- |
| Plugin ID | `minecraft_autonomous` |
| SDK 入口 | `plugin.plugins.minecraft_autonomous:MinecraftAutonomousPlugin` |
| 环境 | Python 3.11+；Node 22+；N.E.K.O 为可选前端 |
| 游戏协议 | **Java 1.21.1（767）**，拒绝 `auto` 和其他版本 |
| 自主框架 | `agent-mc-autonomy@0.1.54`，固定来源 `minecraft-ai-friend@1d1119d210820e100e3efff9fc3ed99a2f00b764` |
| 执行核心 | `agent-mc-world@0.5.5`，来源提交 `954f6f96829e9e2766f41b2599f7dab0cefc54fd` |
| 构建 | 固定源码，直接运行核心官方 `build:engine`；无插件专用补丁或第二份编译实现 |
| 许可证 | 本插件 Apache-2.0；独立核心 MIT，归档保留其许可证和来源 |

## 架构与版本选择

动作规划默认使用 Neko 的模型绑定；也可在「模型 API 接入」中单独选择通义千问、DeepSeek、Kimi、智谱、豆包、硅基流动、OpenAI、Claude、Gemini 或兼容服务。厂商预设不代选模型。原生协议、思考内容回传、流式接收和参数校验均在共享 `agent-mc-autonomy`，插件只提供配置与模型入口。模型访问不进入 Minecraft 身体执行核心。

支持 API Key、外部管理的 Bearer 令牌、OpenAI / Google 官方 OAuth 及 Google ADC。OAuth 可选依赖需单独安装，在运行机器执行 `auth-login`，使用系统凭据库保存授权。Claude 支持 API Key 或外部有效 Bearer，不冒称通用 Claude 订阅账号登录。配置、参数、授权命令和厂商限制见 [共享模型接入文档](https://github.com/jcs130/minecraft-ai-friend/blob/main/packages/agent-mc-autonomy/docs/model-providers.md)。读取模型列表不会推理；显式测试模型会消耗一次调用额度。

游戏记忆在核心的 `mc_memory` 中统一实现，可按需搜索摘要、读取原文、保存方法与失败证据。默认不需要模型；`[memory]` 可选择向量模型、Mem0、阿里云百炼、PowerContext 或通用 HTTP 桥接。配置面板提供相同选项，密钥只填写环境变量名。服务异常时回退本地检索，历史记忆始终要求现场复核。

基础外部检索只匹配本机游戏笔记。可选 `learning_enabled` 接入 PowerContext 1.3 的任务证据、Experience/Skill 候选、Dream 整理与限量历史召回，也可通过通用 HTTP 桥接接入其他服务。PowerContext 需要该服务器、账号和角色专用的已有 Scope；候选在记忆服务中人工审核，插件不会自动批准、安装技能或训练权重。换电脑需迁移本地笔记与提交回执。具体地址与接口边界见共享核心的 [游戏记忆文档](https://github.com/jcs130/minecraft-ai-friend/blob/main/packages/agent-mc-world/docs/game-memory.md)。本地检查未连接真实云账号或家庭记忆服务。

```text
N.E.K.O 主脑：人格 / 相关记忆 / 当前意图 / 策略 / 解说与语音表演
  ↕ 有界共享上下文、目标与反馈；原生状态及回执（不需要逐动作点头）
独立框架：目标管理 → 可替换规划模型 → 事件调度与执行账本
  → MCP stdio / agent-mc/v1 → Agent MC World 原生队列
  → 一个 Mineflayer 客户端 → 远程 Java 1.21.1 服务器

可选现代化观战页 ← 同一个 Mineflayer 连接的区块 / 角色 / 背包
```

Neko 主脑、低层规划模型和 Minecraft 执行器是三个职责。Neko 的主对话人格、记忆、语音情绪
由 Neko 自己管理；`decision` 模型槽只是可选的规划模型来源，不等于主脑完整会话。
启用 `host_context.enabled` 后，主脑在已有复盘回合选取相关记忆与当前关注，通过
`minecraft_autonomy_review.context` 交给同一个身体规划器；没有另跑人格或记忆总结模型。
人格保持在请求固定前缀，变化信息只放在末尾。宿主选出的记忆保留原 ID、来源和原文，
实际现场及当前用户意图优先。投影限量、限时，并绑定身体会话和意图版本；不复制整个聊天记录。

可在配置页显式填写 Neko 的本机公共角色接口，例如已配置主服务的 `/api/characters` 完整地址，
用于获取目标角色的有界人格档案节选（默认结构化性格字段或自定义提示词）；默认留空，不探测端口。此接口不是最终主脑请求或运行中反思人格的完整快照。
未配置时由主脑回传当前人格要点，标为 `host_projection`；相关记忆复用主脑已有的 `recall_memory`，
未检索到则传空列表，不编造或扫描私有记忆文件。关闭共享会清除旧投影，游戏继续运行。
控制面板只显示共享状态、人格字节数、记忆条数及哈希，不公开人格或个人记忆正文。
研究对照和正式接口边界见 [Neko/Cortico 上下文核查](docs/research/neko-host-context-port-20261015.md)。
SQLite 只保存目标和跨进程指令投递、去重及回执；正在执行哪一步、待执行动作和抢占规则
以 **原生 `mc_queue` / `mc_do` / task 事件**为准，不再复制一个身体执行器。

2026-10-13 的历史上游核对至主分支 `034bf38`，新增实际照片留存、登录就绪与实时读数等修复；
实验分支 `7983039` 的有限模型试玩宿主仍绑定具体服务器和模型。本次保留已验证的 headless 核心，
结论和可转发给上游的文本见 [上游更新核查](docs/research/upstream-autonomy-2026-10-13.md)。

## 独立运行与 Neko 旁路接入

先按下节安装固定后端，再把 `standalone.example.toml` 复制为忽略提交的 `config.local.toml`。
配置服务器、后端路径、共享 `runtime.data_directory`，以及显式的 `[planner]` 模型端点和模型名。
密钥只填写环境变量名 `api_key_env`，不写进配置。独立模式只需要 Python 依赖，不需要 Neko SDK：

```powershell
python -m pip install .  # 安装包含固定版本自主框架的声明依赖
python standalone.py check --config config.local.toml
# 自行配置 autonomy.enabled=true 后才可显式启动。
python standalone.py run --config config.local.toml --goal '自主生存，合理收集资源并维护安全住所'
```

`check` 只校验，不访问模型或游戏。前台 `run` 的 Ctrl+C 停止自己的运行实例。
`max_decisions=0` 表示持续运行到显式停止或错误；正数适合有限试跑。每轮工具、上下文和超时仍有界。
稳定世界状态不导致空转模型调用，原生队列会自行推进已规划的多步动作，终态与重要事件推动下一次规划。
没有可用规划模型时不能生成任意新计划；`run --queue-only` 仅执行已规划的原生任务和内置反射。

Neko 插件配置选择 `runtime.mode="external"`，服务器/账号和 `runtime.data_directory` 必须与独立进程一致。
此模式无需绑定 `decision`，不会启动第二个游戏客户端，关闭 Neko 也不会停止外部框架。
Neko 可读取 `status` 的原生队列、事实、当前目标和采样时间，用自己的解说、语音与演出通路表达。
本插件将简短的真实观测交给 Neko 主会话，由宿主按自己的角色和语音配置播报；
不另建语音模型循环，也不会把工具结果发到游戏公屏。现场已收到官方线上语音的音频交付、
桌面开始播放和结束播放回执。

在配置页开启 `heartbeat.enabled`，让 **Neko 主脑持续参与自主生存**。框架根据运行状态生成复盘，插件每 10 秒转交待处理请求；
身体、物品、口粮、任务结果或目标有变化时合并唤醒（默认最短 60 秒），
没有新聊天或新变化时默认 180 秒复核。消息带上当下有用事实和本次 review ID，
详细证据含当前目标、队列、最近任务结果与物资状态持续时间；不会反复拼接完整日志。
主脑调用 `minecraft_autonomy_review` 明确选择继续当前工作或安全插入一个阶段目标，
`inspect` 可以补读本轮证据，完整事实仍可分页查询。复盘不要求每轮开口：
主脑照常确认策略，只有本轮 `commentary` 给出新重点时才用角色口吻说1—2句自然反应，
约40个汉字，不念背包清单、坐标、工具名或“先读取现场”等过程。
独立规划器继续掌管细化回合、动作屏障和原生执行，正常长动作不因心跳被取消。

心跳默认关闭，仅作用于已经显式开始的游戏，`heartbeat.target` 指定角色。
停止、过期观测和旧会话不能派单；新用户意图使旧 review 失效。
外部框架在显式停止后重新启动时，Neko 的停止标记会保留。请在控制面板的
「Neko 主脑决策心跳」卡中点击「恢复 Neko 主脑参与」；入口核验同账号的运行租约
和新鲜联机状态，只恢复后续主脑复盘，不启动游戏、不添加任务。只读状态和观战仍可查看。
手动面板目标标记为用户来源；主脑复盘阶段只是建议，历史来源不明的记录保持未知。
需要时可用 `minecraft_autonomy_review(inspect, lineage_offset=0)` 分页查看原始父目标，
平时不把完整修订链反复放进上下文。[Neko 复盘会话能力需求](docs/neko-review-scope-request.md)
说明当前宿主公共 API 的限制，附可转发给上游的文本。
未收到主脑回执最多重试一次同一 ID，再退避五分钟；未完成的主脑阶段目标不重复插入。
配置页显示通知与主脑回执两种状态，不把发送通知等同于作出决策。
启用决策心跳时，自动解说合并到主脑决策中；普通解说间隔与 `presentation.min_interval_seconds`
共用，危急生命变化可绕过一次间隔。同一局面不反复提醒，用户直接聊天仍正常回应。
关闭 Neko 不影响独立框架继续工作。

如果只需要解说，可开启 `presentation.enabled`：每 10 秒只读一次快照，明显生命/饥饿变化、
新物资种类或有实际结果的原生动作才提供解说机会；普通数量/耐久变化和只读任务不触发。
默认至少间隔 90 秒。`presentation.target` 可指定角色，留空使用宿主当前角色。
默认关闭自动解说；“解说当前游戏状态”按钮可手动提交新鲜状态。旧快照不播报，
状态未变不反复提醒，通知受理也不等于播放完成。当前公共 SDK 没有“静默执行工具、禁止该轮语音”
的强制输出开关；策略通过通知及工具返回的表达要求传给主脑，实际说话与播放仍需现场核验。

主脑通过公共 SDK 的 `minecraft_autonomy_status` 工具按需读取紧凑状态、分页事实与指定指令回执；
`minecraft_autonomy_intent` 投递自然语言目标，明确选择 append / insert / replace；
`minecraft_autonomy_stop` 处理用户明确的停止要求。这些工具不再启动另一套规划或语音循环。

| 入口 | 意图与行为 |
| --- | --- |
| `submit_goal(goal,request_id)` | 新的自然语言目标，当前目标及原生动作结束后由独立规划器接续 |
| `feedback(goal,mode="insert",request_id)` | 优先采用新反馈，取消过时推理，按原生安全检查点插入；结束后恢复原目标 |
| `feedback(goal,mode="replace",request_id)` | 明确替换：先调用原生 stop 清空旧动作，保存回执，再按新目标规划 |
| `status` / `task_receipt(request_id)` | 读取最后观察到的状态和原始回执；保留采样时间，不把文件存在等同于进程存活 |
| `submit_steps(steps,request_id,queue)` | 高级接口：投递已规划动作，默认 append；也支持 afterCheckpoint / now |
| `stop` | 显式停止外部实例需由其确认；shutdown 在 external 模式只读取状态 |

每个新目标或反馈生成一个 UUID `request_id`；确认不明时用同一个 ID 查询或重试，不换 ID 重投。
`queued` 只说明指令已投递，`planning` 说明已采用目标，原生 `accepted` 也不等于完成。
规划器提交的 `reported_done` 始终附 `verified=false`、当时事实与原始回执入口，不能冒充独立验收。
在命令行也可操作同一入口：

```powershell
python standalone.py submit-goal --config config.local.toml --request-id 11111111-1111-4111-8111-111111111111 --goal '收集木头并制作工作台'
python standalone.py feedback --config config.local.toml --request-id 22222222-2222-4222-8222-222222222222 --mode replace --goal '别挖了，返回安全住所'
python standalone.py receipt --config config.local.toml --request-id 22222222-2222-4222-8222-222222222222
python standalone.py status --config config.local.toml
```

示例 ID 只演示格式，实际每个新指令生成新 UUID；重复查询同一指令保留原 ID。
完整所有权、反馈与恢复规则见 [架构说明](docs/design.md)。

不依赖 Cortico Core、Persona、provider 或 Memory；公共类型和构建不需要 Cortico checkout。
本次采用的是指定提交内的独立核心，**没有将整个 My Agent World 服务器工程搬进插件**。
该提交的 `@my-agent-world/agent-mc-host` 是另一种原生身体适配器，有模组操作、UUID 和原生账本约束。
**接入 My Agent World / NeoForge 专用模组服时，普通 Mineflayer 1.21.1 不能替代其原生协议适配器。**
原生适配器尚未接入本插件；具体价值、依赖、缺口及可转发提示词见
[本次评估](docs/research/agent-mc-world-04-integration.md)。

## 准备后端

插件导入、状态查询、startup 均不会下载后端、连接游戏或调用模型。
没有假设 GitHub 上存在对应发行包。先从固定源码构建，再显式安装到独立目录：

```powershell
git clone https://github.com/jcs130/minecraft-ai-friend.git ../minecraft-ai-friend
$env:PYTHONPATH = (Resolve-Path ./vendor).Path
$corePin = Get-Content ./vendor/agent_mc_autonomy/core_distribution/source.json -Raw | ConvertFrom-Json
git -C ../minecraft-ai-friend fetch origin $corePin.source_revision
# 这是新克隆的构建源目录；切到固定提交后，显式准备依赖缓存。
git -C ../minecraft-ai-friend checkout --detach $corePin.source_revision
pnpm --dir ../minecraft-ai-friend/packages/agent-mc-world fetch
# 构建需要 pnpm 11.5.0 和 Node.js >=22；destination 必须为空。
python backend/build.py --checkout ../minecraft-ai-friend --destination ../agent-mc-world-neko-build
python backend/install.py --destination ./local/backend --archive "../agent-mc-world-neko-build/$($corePin.archive)"
python backend/check_disconnected.py --directory ./local/backend
```

安装器检查 `agent_mc_autonomy/core_distribution/source.json`（来自固定版本框架依赖） 中的归档 SHA256、版本、源提交和编译文件清单，
同时校验源码、运行文件、公开类型及入口的标准构建回执。
使用固定 npm lockfile 和 `--ignore-scripts`。构建工具链差异导致哈希不符时会拒绝安装，
需要重新核查构建产物，不能直接跳过校验。已准备运行目录不等于已登录游戏。
发布到其他机器时，同样需要显式准备后端；`.neko-plugin` 不夹带 Node、账号或原生 SDK。若已有与固定清单匹配的 `agent-mc-world` 归档，只需执行 install/check 两步，不需要 Git 或 pnpm 构建。准备版的配套归档与校验值见发布准备文档。

## Neko 内嵌运行（可选）

以 `config.example.toml` 为模板，在 N.E.K.O 的插件配置中填写：

- `server.host` / `port`：可用的远程服务器；`version` 固定为 `1.21.1`。
- `username` / `auth`：使用该服务器允许的账号。正版服使用 `microsoft`；首次认证可能需要按私有后端日志完成设备授权。`offline` 只适用于允许该认证方式的服务器。
- `backend.directory`：填写安装后的绝对目录；版本以固定校验清单为准，目录存在不代表安装校验通过。
- `viewer.url`：填写已部署、与当前角色配套的现代可视化页面；在观战面板点击后载入，也可单独打开。不创建第二个游戏账号。
- `autonomy.enabled=true`：允许显式启动；`plugin_runtime.auto_start=false` 保持默认。

选择 `runtime.mode="embedded"` 时，在宿主的模型槽配置中，将插件声明的 **`decision`** 绑定到支持文本和工具调用的模型。
`context_tokens` 应不大于该模型实际上下文额度，输出预留由 `max_output_tokens` 指定。
插件不保存模型密钥，不自行选择其他模型或显卡。公共模型网关只提供推理；
Neko 主对话的完整角色记忆、语音情绪和长期经验不会自动注入这条独立决策循环。

## 模型、快决策与控制台

在 Neko「用户插件 → 管理面板」中选择 **Minecraft Autonomous → 面板**，有两个页面：

- **配置与控制**：编辑服务器、运行方式、模型/感知策略，投递自然语言目标，查看上下文预算与模型检查结果。
- **观战与状态**：生命/饥饿、位置、当前目标、原生动作队列、决策耗时曲线、Token 样本、事实及中间回执。

配置页的「打开观战与状态」可以独立打开同一页面；旧版宿主的「打开界面」通过标准 `static/index.html` 发现它。
当前宿主也支持直接访问 `/ui/plugins/minecraft_autonomous?tab=panel&surface=main`；
观战页位于 `/plugin/minecraft_autonomous/ui/`，使用插件服务的同源地址，无须另开配置服务。

观战页只读取公共 hosted UI context。可见时每 5 秒刷新；切换到其他面板或隐藏页面后暂停读取。
数据超过 30 秒或读取失败时明确标记为待更新，保留最后观测，不把存档快照当成进程存活。
统计每类最多取末尾 128 KiB 中的 20 条完整记录，不是全会话总量，也不会生成额外模型分析。
刷新与保存不启动游戏。手动模型检查才发起推理，图像检查使用合成色块，不代表真实游戏视觉验收。

**接入现代观战画面：** 在「配置与控制」填写 `viewer.url`，点「仅保存观战地址」，
再到「观战与状态」点「载入观战画面」。仅保存此地址允许在嵌入式角色运行期间进行；
修改运行参数仍须先显式停止。URL 只接受 HTTP(S)，不允许账号、密码、查询参数或片段；
页面不会把模型密钥、用户目标或角色状态转发给观战地址。外部服务不允许嵌入时可单独打开。

配置页使用宿主 Hosted TSX SDK，观战页使用官方静态面板声明，不修改 Neko 核心。
可选观战扩展复用共享可视化项目的精确 1.21.1 资源及当前身体连接。配置和验收边界见
[原版观战](docs/vanilla-viewer.md)。没有配置时显示空状态；页面加载成功不代表实际渲染通过。

| 配置 | 行为与回退 |
| --- | --- |
| Neko `decision` 用途槽 | 文本＋工具调用；绑定通过 Neko 模型 API 页面完成。未绑定时保留原生连接、队列与规则反射，暂停自然语言规划，每 60 秒后才允许重试 |
| Neko `vision` 用途槽 | 可与 decision 绑定同一个多模态模型；只有收到新鲜的核心 PNG 才使用。未绑定、能力不符、接口错误或无效输出时退回 decision 的文字事实 |
| `fast.mode="rules"` | 默认规则，无快模型请求；紧急状态和原生待执行工作优先 |
| `fast.mode="host"` | 使用可选 `fast` 聊天模型槽生成结构化选择；2 秒未返回、格式不符或置信不足则按规则处理 |
| `fast.mode="system_one"` | 显式配置远程 Jev 或本地兼容 Decider 的完整端点、模型和密钥环境变量名；不要求每个人本地部署 |

快选择目前只在 survival / inspect / work / wait 中提供**规划关注点**，不接管底层身体控制。
原生反射与 `mc_do` / `mc_queue` 仍掌管实际动作。
普通聊天模型自报置信度不等同于 Jev 的概率校准。专用协议、参数和研究证据见
[模型兼容记录](docs/research/model-routing-and-jev-2026-10-13.md)。

独立模式继续使用自己的 `[planner]` 配置，`image_input=true` 必须显式声明；
外部观察模式的 Neko 模型绑定不会覆盖独立进程。当前 headless 后端仅有背包地图 PNG 等核心图像，
并没有接通现代 3D 观战画面。图像只在 15 秒内、一次请求末尾使用；原文和图像引用留在原始记录中。
模型密钥由 Neko 宿主管理；专用 System One 只接受密钥所在的环境变量名，面板不展示密钥。
本次实际文字/图像/缺省回退与控制台 API 验证见 [兼容与现场记录](docs/research/model-routing-and-jev-2026-10-13.md)。

| 入口 | 行为 |
| --- | --- |
| `status` | 只读查询连接、决策次数、待完成动作、上下文预算、错误及外部观战地址 |
| `start(goal="survive")` | 返回已受理/正在连接；实际进服以服务器在线灯和后续状态为准 |
| `stop` | 停止模型等待，断开该插件拥有的客户端；保留原始账本，重复调用安全 |
| startup / shutdown | startup 被动查询；shutdown 执行 stop；不自动恢复上次目标 |

运行时通过同一 `submit_goal` / `feedback` 入口调整目标；重复 start 不会创建第二个身体。
`max_decisions` 为正数时限定总回合，为 0 时持续运行；每回合最多 `max_tool_rounds` 次模型请求。
长动作期间继续收取事件；普通快照不打断动作，受伤等紧急事件可取消等待中的推理。
动作 accepted、RPC 成功、HTTP 200 都不是任务完成证据。结果未知时停下并保留请求 ID，禁止自动重放。

## 上下文和恢复

固定规则、稳定工具定义在前；完整的工具调用/回执对组成有限历史；最新事实和事件引用位于最后。
工具说明按需读取；常用动作保留参数约束，高级能力通过 `mc_invoke` 路由并由原始后端校验。
`mc_tool_help` 可逐级读取原始参数文档；`mc_original` 可分页读取事实、超长回执的完整原文。
预算包括消息、工具、输出预留和消息框架余量，以 UTF-8 字节作保守估算；不是精确 tokenizer 或缓存命中实测。
旧事实不会逐轮追加；仅采样时间变化不触发新模型请求。模型等待期间的新聊天保留到下一轮。
固定前缀较大时保留有限的错误诊断与最新动作终态；必要时缩短观测并提供完整原文入口，
优先淘汰已被当前观测替代的旧只读回执。模型截断输出不发送游戏动作，记录后有限退避重试，
连续三次失败则结束运行并保留证据。它不重放已经发出的未知动作。

私有数据按服务器与账号隔离，换后端版本不换账本。若出现 `outcome_unknown`，检查该会话下
`host-state.json`、`receipts.jsonl`、后端原始请求与事件记录，确认原请求结果后再处理状态；
不要删除目录、换 action ID 或把 unknown 当成失败后直接重试。此开发版不提供一键清除未知状态。

## 观战与模组服边界

上游打包的 viewer 资源属于 **1.20.6**。本次构建不包含它，不把它当成 1.21.1 渲染器。
内置 viewer/console 端口必须为 0；文本观测与动作可用性仍需真实服务器验收。
现代观战通过可选扩展接入，精确版本资源由共享可视化项目维护；进服后可请求浏览器自动打开一次。
NeoForge 原生注册表/握手、Numen 远程身体、原生服控制租约和千灯纪扩展仍需独立适配。
当前身体 UUID、区块和背包链路通过不等于实体、光照和完整浏览器画面一致性通过。

## 验证和发布

见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [架构说明](docs/design.md)。
单元测试使用真实公共 SDK和替身模型/执行器；独立 stdio 检查拒绝网络和 Cortico 导入。
官方 Verify/Release/Ruff 模板保持原样。推送只触发源码验证，未创建 release tag、未发布 Market。
包结构检查通过不能替代真实游戏验收。

解耦审计、旧约定清理和可转发给源码维护者的提示词见
[独立核心审计](docs/research/standalone-core-audit.md)。

## English / 日本語

Independent Minecraft Java 1.21.1 autonomy with natural-language goals and native queue execution.
N.E.K.O is an optional strategy, narration and voice frontend. Standalone planning uses an explicitly configured
model. Basic vanilla actions, narration playback receipts and same-player viewer data are verified;
sustained survival and full browser rendering remain unverified.

Minecraft Java 1.21.1 の独立自律フレームワークです。N.E.K.O は目標・方針・解説・音声を担当します。
原版での基本動作、解説の再生通知、同一プレイヤーの観戦データを確認済みです。長期生存と完全な描画は未検証です。

## 框架与适配层归属（2026-10-13）

自主控制器、任务邮箱、稳定前缀/动态事实、事件与定期复盘、多模态/快决策端口、工作线程和可选观战装配只在 MC friend 主仓库维护。Neko 仅提供公开 SDK 模型槽、主脑通知与工具回传、配置面板、角色和官方语音绑定。`autonomy/` 与 `worker.py` 只留兼容导入，`standalone.py` 只留固定后端校验入口；新集成直接使用 `agent_mc_autonomy`。

框架生成决策请求，Neko 定时器只转交待处理请求。主脑 inspect 后选择 continue 或 insert；插入仍交给框架原生检查点，用户的新反馈使旧决策失效。没有接入 Neko 时，显式配置的独立规划模型继续游戏。Cortico/其他宿主可以接相同的 Planner、ReviewPort 和 Mailbox，尚未声称已有这些宿主的完成适配或实测。
