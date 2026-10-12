# Minecraft Autonomous · 我的世界自主生存

面向 [N.E.K.O](https://github.com/Project-N-E-K-O/N.E.K.O) 的 Minecraft 自主游玩插件。
目标是让角色自己观察世界、制定目标、执行动作并根据结果调整，在用户没有逐步指挥时也能推进生存任务。
用户可以改变目标、接管和停止；陪聊与解说是可选能力。

**当前状态：仓库基础已建立，游戏后端尚未接入，不能实际自主游玩。**
`0.1.0` 是开发中的初始版本，尚未发布 Release 或提交 Market 审核。

| 项目 | 内容 |
| --- | --- |
| Plugin ID | `minecraft_autonomous` |
| 仓库 | `jcs130/n.e.k.o_plugin_minecraft_autonomous` |
| SDK 入口 | `plugin.plugins.minecraft_autonomous:MinecraftAutonomousPlugin` |
| Python | 3.11+ |
| 许可证 | Apache-2.0 |

## 产品目标

- 自行感知位置、生命、饥饿、库存、附近风险和任务变化。
- 自行规划采集、制作、探索、建造和生存行为，通过执行反馈判断进展。
- 长动作期间少打断，遇到新的重要事件再决策。
- 支持明确的停止、人工接管及恢复边界。
- 只把有用的当前事实放入决策上下文；原始证据保留查询入口。
- 固定规则和工具定义保持稳定，动态状态集中放在请求末尾，减少重复拼接。

以上为待实现的产品目标。候选后端与迁移对照版本为 `agent-mc-world@0.3.0-next.2`，
已有固定来源、显式安装器、配置和 MCP 传输基础；禁止网络的离线工具发现已验证，
尚未接入插件入口或完成自主循环。
独立入口不需要 Cortico npm 运行依赖，但上游构建与部分接口仍有耦合；
接入前必须完成[解耦验收](docs/research/fork-improvements-and-decoupling-boundary.md)。
架构与后续验收边界见 [设计说明](docs/design.md)，
以及 [Cortico / N.E.K.O 对照研究](docs/research/neko-integration-architecture.md)。

## 当前可用入口

| 入口 | 当前行为 |
| --- | --- |
| `status` | 返回 `backend_ready=false`、`game_connected=false`、`autonomy_running=false` |
| `start(goal="survive")` | 返回 `Err`，错误码为 `backend_not_integrated` |
| `stop` | 返回当前停止状态，可以重复调用 |
| startup / shutdown | 初始化时只报告状态，退出时保持停止 |

插件生命周期和以上入口不会启动进程、连接游戏、调用模型或发送聊天。
独立的开发安装与离线桥接检查需显式执行，不能由导入或 startup 自动触发。
入口成功返回状态并不代表已经连上游戏或实现自主生存。

## 配置

`config.example.toml` 提供可移植的默认配置：

```toml
[plugin_runtime]
enabled = true
auto_start = false

[autonomy]
enabled = false
```

`autonomy.enabled` 为后端接入预留；当前即使改成 `true`，启动请求仍会返回后端未接入。
本仓库不包含账号、服务器地址、模型配置、音色缓存或用户私有数据。

## 开发与验证

先准备 N.E.K.O 源码和它的 Python 3.11 开发环境。
`NEKO_ROOT` 指向宿主源码目录；验证只读取 SDK，不要求启动宿主或 Minecraft。

在本插件仓库根目录执行，例如 PowerShell：

```powershell
$env:NEKO_ROOT = '/path/to/N.E.K.O'
uv run --project "$env:NEKO_ROOT" python -m pytest tests -q
uvx ruff==0.12.4 check --ignore-noqa --config ruff.toml .
uv run --project "$env:NEKO_ROOT" neko-plugin check --release --market-release .
```

未处于 Git tag 的本地 Market 结构检查会提示无法比对 tag；这不会发布插件。
VS Code 任务直接使用 `NEKO_ROOT`，修改环境变量后重新打开编辑器。
任务中的环境变量用法见 [VS Code 官方文档](https://code.visualstudio.com/docs/reference/variables-reference#_environment-variables)。

运行时依赖在 `pyproject.toml` 声明，由官方 CLI 同步到 `vendor/` 后打包。
MCP 传输依赖官方 Python `mcp==2.1.1`；独立 Node.js 22+ 执行后端需要另外显式安装。
`vendor/`、Node 依赖、构建结果和运行数据均不提交。
详细开发流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 后续发布

仓库保留官方 CLI 生成的 Verify / Release 工作流，推送源码会运行验证。
Release 工作流仅在 `v*` tag 或手动触发时执行，不会因为普通源码推送发布。

接入后端并完成实际游戏验收后，再按[官方插件贡献流程](https://project-neko.online/zh-CN/plugins/cli)
提交首次审核。审核通过后，使用官方 `neko-plugin publish` 流程发布插件包及 Market 验证材料。
当前不应把这个基础版本提交成已能自主游玩的插件。

## English / 日本語

An autonomous Minecraft player plugin for N.E.K.O. This repository currently contains
the official plugin scaffold, readiness entries, offline tests and Market workflows.
The game backend is not integrated; autonomous gameplay is not available yet.

N.E.K.O 向けの自律型 Minecraft プレイヤープラグインです。現在は公式構成、状態確認、
オフラインテストと公開用ワークフローのみです。ゲームバックエンドは未接続で、自律プレイはまだできません。
