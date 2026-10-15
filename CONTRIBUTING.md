# Contributing

当前增量在标准仓库上接入独立 Agent MC World；版本和来源见 `agent_mc_autonomy/core_distribution/source.json`（来自固定版本框架依赖）。
执行接口的离线验证与完整自治行为分别验收，接口差异见 `docs/research/agent-mc-world-04-integration.md`。

## 开发环境

- Python 3.11+；使用独立的 N.E.K.O 开发环境。
- `NEKO_ROOT` 指向包含 `plugin/sdk/plugin` 的 N.E.K.O 源码目录。
- 仅导入公共 `plugin.sdk.plugin` API，不复制或伪造 SDK。
- `autonomy/` 与 `standalone.py` 不导入宿主 SDK；Neko 适配器通过同一运行层操作。
- 运行时依赖写入 `pyproject.toml`，测试依赖放在开发环境中。

在本插件仓库根目录验证：

克隆或隔离验证时，插件目录名使用 `minecraft_autonomous`，与插件 ID、入口和正式安装布局一致。
GitHub 仓库名包含点号；直接把该名字作为 Python 包目录运行测试会导致相对导入失败。

```powershell
$env:NEKO_ROOT = '/path/to/N.E.K.O'
uv run --project "$env:NEKO_ROOT" python -m pytest tests -q
node --test tests/observer-data.test.mjs
uvx ruff==0.12.4 check --ignore-noqa --config ruff.toml .
uv run --project "$env:NEKO_ROOT" neko-plugin check --release --market-release .
```

也可使用已配置开发环境的 Python 直接执行 `python -m pytest tests -q`。
先用 `neko-plugin sync .` 安装固定版本的自主框架依赖。游戏逻辑的测试在 MC friend 主仓库运行，本仓库只检验适配层。
本地测试通过 `NEKO_ROOT` 找到真实 SDK；官方 CI 将插件挂载到宿主源码树后验证。
主仓库 `packages/agent-mc-autonomy/tests/standalone_probe.py` 在隔离 Python 进程中禁止宿主导入、网络和游戏进程，
用假模型与假执行器检验自主循环和纯原生队列模式。端到端演出/语音仍须另行实测。
观战页的 Node 测试只检查展示数据与 URL 校验，不请求宿主、游戏或模型。
界面改动还需在实际 Neko 管理器的两个面板验收：配置保存、隐藏后停止读取、
失效快照、窄屏布局，以及以隔离页面验证按需载入/关闭观战窗口。不得把页面加载当成真实游戏画面验收。

## 提交要求

- 多个 agent 协作时，修改前和推送前先 fetch 本仓库 main，检查差异并保留他人的工作。
  验证后及时普通推送主干；遇到并发更新先整合，禁止强推或重置共享分支。
- 开发期间检查有关上游分支，记录 SHA、适用范围和是否采用；源码更新与实际部署分开。
  核心、Neko 前端、可视化和测试服保持项目边界，不跨仓库夹带修改或复制私有运行目录。
- 使用小范围提交，更新受影响的测试与说明。
- 单元测试使用临时存储并禁止网络连接、真实进程启动和消息发送，不依赖真实游戏。
- 单独的 `backend/check_disconnected.py` 检查会显式启动自己拥有的 MCP 子进程，
  使用禁止网络和 Cortico 导入的预加载器；禁用 HTTP/viewer 监听，不执行 connect，不调用模型。
- 不提交令牌、账号会话、私服配置、模型权重、参考音频和个人存档。
- 配置默认不自动开始游戏。启动、停止、取消及接管语义必须可观察、可测试。
- 不把 HTTP 成功、模型输出或工具调用受理等同于动作完成。
- 不修改官方管理的工作流和 Ruff 模板；模板升级通过官方 CLI 流程执行。
- 发布前检查 `.neko-plugin` 内容；测试、开发文档、运行数据和密钥文件不进入运行包。

## 功能与发布边界

新增后端应提供观测、有限时动作、取消及结果回执。正常长动作期间不因例行决策反复取消。
提示词保持固定前缀，动态事实集中在末尾；原文留存及查询入口不能因压缩上下文丢失。

开发者显式安装固定后端后，可以独立验证 MCP 传输：

```powershell
python backend/install.py --destination ./local/backend-045 --archive /path/to/agent-mc-world-0.4.5.tgz
python backend/check_disconnected.py --directory ./local/backend-045
```

安装器校验官方 `build:engine` 归档 SHA256、固定构建凭据和源码/运行文件/类型清单，
并通过 `npm ci --ignore-scripts --omit=dev` 装配依赖，可用 `--offline` 限定已有缓存。
第二条命令核实断开状态、工具发现、记忆读写与重开恢复，以及错误回执，不证明已登录或可自主游玩。

普通源码推送只触发 Verify。后端未完成现场验收前，不创建发布 tag、不手动触发 Release、
不调用 `neko-plugin publish`，也不将开发基础作为可玩的插件提交 Market。
首次 Market 审核及之后的发布遵循官方文档，不能用本地验证冒充审核通过。
