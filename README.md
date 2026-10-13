# Minecraft Autonomous · 我的世界自主生存

Minecraft 自主框架，以及面向 [N.E.K.O](https://github.com/Project-N-E-K-O/N.E.K.O) 的接入插件。
Neko 提供高层目标、策略、角色演出与语音；独立框架细化规划并驱动原生执行队列。
没有用户新消息时继续推进目标；新反馈可以在检查点插入，或明确替换当前行为。
框架有独立入口，不安装、不启动 Neko 也能运行。
可配置其他人的兼容服务器，不要求在本机开服。
Minecraft 执行插件由 **jcs130** 编写与维护，源码来自你的 `minecraft-ai-friend` 项目。

**0.3.0 开发版：独立运行、自然语言目标、反馈插入和原生队列接入已做离线验证；真实进服、长期生存、Neko 演出链路及观战绑定尚未验收。**
默认关闭自主游玩，必须显式执行独立 `run` 或内嵌 `start`。本次开发没有启动旧 Neko、模型或游戏，没有发布 Release/Market。

| 项目 | 内容 |
| --- | --- |
| Plugin ID | `minecraft_autonomous` |
| SDK 入口 | `plugin.plugins.minecraft_autonomous:MinecraftAutonomousPlugin` |
| 环境 | Python 3.11+；Node 22+；N.E.K.O 为可选前端 |
| 游戏协议 | **Java 1.21.1（767）**，拒绝 `auto` 和其他版本 |
| 执行核心 | `agent-mc-world@0.4.0`，来源提交 `7889ce261a2309d94400b739c6198468d8271d83` |
| 构建 | 固定源码 + 本仓库的解耦补丁，派生的 `neko-headless` |
| 许可证 | 本插件 Apache-2.0；独立核心 MIT，归档保留其许可证和来源 |

## 架构与版本选择

```text
N.E.K.O 主脑：目标 / 新反馈 / 解说 / 语音 / 表演
  ↕ 自然语言目标与反馈；原生状态及回执（不需要逐动作点头）
独立框架：目标管理 → 可替换规划模型 → 事件调度与执行账本
  → MCP stdio / agent-mc/v1 → Agent MC World 原生队列
  → 一个 Mineflayer 客户端 → 远程 Java 1.21.1 服务器

外部现代化可视化页面 ← 自己的数据/画面来源（需另行核验与该角色的绑定）
```

Neko 主脑、低层规划模型和 Minecraft 执行器是三个职责。Neko 的主对话人格、记忆、语音情绪
由 Neko 自己管理；`decision` 模型槽只是可选的规划模型来源，不等于主脑完整会话。
SQLite 只保存目标和跨进程指令投递、去重及回执；正在执行哪一步、待执行动作和抢占规则
以 **原生 `mc_queue` / `mc_do` / task 事件**为准，不再复制一个身体执行器。

最新上游已核对：主分支 `7c0bdc5` 增加空间短诊断；实验分支 `7983039` 增加有限模型试玩宿主，
但仍绑定具体服务器和模型，且核心包相对当前 pin 没变。本次保留已验证核心，
结论和可转发给上游的文本见 [上游更新核查](docs/research/upstream-autonomy-2026-10-13.md)。

## 独立运行与 Neko 旁路接入

先按下节安装固定后端，再把 `standalone.example.toml` 复制为忽略提交的 `config.local.toml`。
配置服务器、后端路径、共享 `runtime.data_directory`，以及显式的 `[planner]` 模型端点和模型名。
密钥只填写环境变量名 `api_key_env`，不写进配置。独立模式只需要 Python 依赖，不需要 Neko SDK：

```powershell
python -m pip install 'mcp==2.1.1' 'httpx>=0.27,<1'
python standalone.py check --config config.local.toml
# 自行配置 autonomy.enabled=true 后才可显式启动；本次开发没有执行此行。
python standalone.py run --config config.local.toml --goal '自主生存，合理收集资源并维护安全住所'
```

`check` 只校验，不访问模型或游戏。前台 `run` 的 Ctrl+C 停止自己的运行实例。
`max_decisions=0` 表示持续运行到显式停止或错误；正数适合有限试跑。每轮工具、上下文和超时仍有界。
稳定世界状态不导致空转模型调用，原生队列会自行推进已规划的多步动作，终态与重要事件推动下一次规划。
没有可用规划模型时不能生成任意新计划；`run --queue-only` 仅执行已规划的原生任务和内置反射。

Neko 插件配置选择 `runtime.mode="external"`，服务器/账号和 `runtime.data_directory` 必须与独立进程一致。
此模式无需绑定 `decision`，不会启动第二个游戏客户端，关闭 Neko 也不会停止外部框架。
Neko 可读取 `status` 的原生队列、事实、当前目标和采样时间，用自己的解说、语音与演出通路表达。
本插件不合成语音，也不会把解说或工具结果发到游戏公屏；端到端演出效果尚待实测。

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
git -C ../minecraft-ai-friend fetch origin 7889ce261a2309d94400b739c6198468d8271d83
# 构建需要 pnpm 11.5.0；destination 必须为空。
python backend/build.py --checkout ../minecraft-ai-friend --destination ../agent-mc-world-neko-build
python backend/install.py --destination ./local/backend-04 --archive ../agent-mc-world-neko-build/agent-mc-world-0.4.0.tgz
python backend/check_disconnected.py --directory ./local/backend-04
```

安装器检查 `backend/source.json` 中的归档 SHA256、版本、源提交和编译文件清单，
以及解耦补丁摘要；没有应用补丁的旧构建会被拒绝。
使用固定 npm lockfile 和 `--ignore-scripts`。构建工具链差异导致哈希不符时会拒绝安装，
需要重新核查构建产物，不能直接跳过校验。已准备运行目录不等于已登录游戏。
发布到其他机器时，同样需要显式准备后端；`.neko-plugin` 不夹带 Node、账号或原生 SDK。

## Neko 内嵌运行（可选）

以 `config.example.toml` 为模板，在 N.E.K.O 的插件配置中填写：

- `server.host` / `port`：可用的远程服务器；`version` 固定为 `1.21.1`。
- `username` / `auth`：使用该服务器允许的账号。正版服使用 `microsoft`；首次认证可能需要按私有后端日志完成设备授权。`offline` 只适用于允许该认证方式的服务器。
- `backend.directory`：安装后的绝对目录；留空则使用插件缓存内的 `agent-mc-world-0.4.0-headless`。
- `viewer.url`：可填现有现代化可视化页面。这里只返回入口，不会接管页面、额外开观战账号或谎称已绑定本角色。
- `autonomy.enabled=true`：允许显式启动；`plugin_runtime.auto_start=false` 保持默认。

选择 `runtime.mode="embedded"` 时，在宿主的模型槽配置中，将插件声明的 **`decision`** 绑定到支持文本和工具调用的模型。
`context_tokens` 应不大于该模型实际上下文额度，输出预留由 `max_output_tokens` 指定。
插件不保存模型密钥，不自行选择其他模型或显卡。公共模型网关只提供推理；
Neko 主对话的完整角色记忆、语音情绪和长期经验不会自动注入这条独立决策循环。

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

私有数据按服务器与账号隔离，换后端版本不换账本。若出现 `outcome_unknown`，检查该会话下
`host-state.json`、`receipts.jsonl`、后端原始请求与事件记录，确认原请求结果后再处理状态；
不要删除目录、换 action ID 或把 unknown 当成失败后直接重试。此开发版不提供一键清除未知状态。

## 观战与模组服边界

上游打包的 viewer 资源属于 **1.20.6**。本次构建不包含它，不把它当成 1.21.1 渲染器。
内置 viewer/console 端口必须为 0；文本观测与动作可用性仍需真实服务器验收。
图像模型输入、NeoForge 原生注册表/握手、Numen 远程身体、原生服控制租约以及桌面语音不在本次通用接入范围内。
外部页面能打开，也不能证明画面属于当前 Mineflayer 身体。

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
model. Offline tests cover feedback, stop and receipts; live gameplay, performance and viewer binding are unverified.

Minecraft Java 1.21.1 の独立自律フレームワークです。N.E.K.O は目標・方針・解説・音声を担当します。
明示起動とオフライン検証を実装しています。実サーバー、長期生存、演出と観戦の紐付けは未検証です。
