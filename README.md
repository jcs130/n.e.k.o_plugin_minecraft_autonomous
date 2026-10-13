# Minecraft Autonomous · 我的世界自主生存

面向 [N.E.K.O](https://github.com/Project-N-E-K-O/N.E.K.O) 的 Minecraft 自主游玩插件。
Neko 提供模型接口与用户目标，插件负责事件调度，独立执行核心负责观察世界、操作和回执。
可配置其他人的兼容服务器，不要求在本机开服。
Minecraft 执行插件由 **jcs130** 编写与维护，源码来自你的 `minecraft-ai-friend` 项目。

**0.2.0 开发版：已接入自主控制流程并完成离线验证，真实进服、长期生存及观战绑定尚未验收。**
默认关闭自主游玩，必须显式 `start`。本次开发没有启动旧 Neko、模型或游戏，没有发布 Release/Market。

| 项目 | 内容 |
| --- | --- |
| Plugin ID | `minecraft_autonomous` |
| SDK 入口 | `plugin.plugins.minecraft_autonomous:MinecraftAutonomousPlugin` |
| 环境 | Python 3.11+；Node 22+；支持公共插件模型网关的 N.E.K.O |
| 游戏协议 | **Java 1.21.1（767）**，拒绝 `auto` 和其他版本 |
| 执行核心 | `agent-mc-world@0.4.0`，来源提交 `7889ce261a2309d94400b739c6198468d8271d83` |
| 构建 | 固定源码 + 本仓库的解耦补丁，派生的 `neko-headless` |
| 许可证 | 本插件 Apache-2.0；独立核心 MIT，归档保留其许可证和来源 |

## 架构与版本选择

```text
用户目标 / N.E.K.O 插件入口
  → 公共模型绑定 decision（推理）
  → Python 控制器（事件、上下文预算、停止、动作账本）
  → MCP stdio / agent-mc/v1（回合、屏障、回执）
  → 独立 Agent MC World 核心 → 一个 Mineflayer 客户端 → 远程 Java 1.21.1 服务器

外部现代化可视化页面 ← 自己的数据/画面来源（需另行核验与该角色的绑定）
```

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

## 配置和使用

以 `config.example.toml` 为模板，在 N.E.K.O 的插件配置中填写：

- `server.host` / `port`：可用的远程服务器；`version` 固定为 `1.21.1`。
- `username` / `auth`：使用该服务器允许的账号。正版服使用 `microsoft`；首次认证可能需要按私有后端日志完成设备授权。`offline` 只适用于允许该认证方式的服务器。
- `backend.directory`：安装后的绝对目录；留空则使用插件缓存内的 `agent-mc-world-0.4.0-headless`。
- `viewer.url`：可填现有现代化可视化页面。这里只返回入口，不会接管页面、额外开观战账号或谎称已绑定本角色。
- `autonomy.enabled=true`：允许显式启动；`plugin_runtime.auto_start=false` 保持默认。

在宿主的模型槽配置中，将插件声明的 **`decision`** 绑定到支持文本和工具调用的模型。
`context_tokens` 应不大于该模型实际上下文额度，输出预留由 `max_output_tokens` 指定。
插件不保存模型密钥，不自行选择其他模型或显卡。公共模型网关只提供推理；
Neko 主对话的完整角色记忆、语音情绪和长期经验不会自动注入这条独立决策循环。

| 入口 | 行为 |
| --- | --- |
| `status` | 只读查询连接、决策次数、待完成动作、上下文预算、错误及外部观战地址 |
| `start(goal="survive")` | 返回已受理/正在连接；实际进服以服务器在线灯和后续状态为准 |
| `stop` | 停止模型等待，断开该插件拥有的客户端；保留原始账本，重复调用安全 |
| startup / shutdown | startup 被动查询；shutdown 执行 stop；不自动恢复上次目标 |

更换目标需先 `stop` 再 `start`；重复 start 不会创建第二个身体。
每次启动最多 `max_decisions` 个决策回合，每回合最多 `max_tool_rounds` 次模型请求，达到上限即停止。
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

Development integration of an independent Minecraft Java 1.21.1 execution core with N.E.K.O-owned decisions.
Explicit start, bounded context and receipt-based execution are implemented and tested offline. Live gameplay,
native My Agent World integration and external viewer/body binding remain unverified. No automatic startup.

N.E.K.O が判断し、独立した実行コアが Minecraft Java 1.21.1 を操作する開発版です。
明示的な起動・停止とオフライン検証を実装しています。実サーバー、自律生存、専用MOD対応と観戦の紐付けは未検証です。
