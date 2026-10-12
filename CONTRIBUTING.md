# Contributing

当前增量建立插件仓库基础。提交游戏功能前，先确定后端框架、版本及许可证，并补充可验证的接口设计。

## 开发环境

- Python 3.11+；使用独立的 N.E.K.O 开发环境。
- `NEKO_ROOT` 指向包含 `plugin/sdk/plugin` 的 N.E.K.O 源码目录。
- 仅导入公共 `plugin.sdk.plugin` API，不复制或伪造 SDK。
- 运行时依赖写入 `pyproject.toml`，测试依赖放在开发环境中。

在本插件仓库根目录验证：

```powershell
$env:NEKO_ROOT = '/path/to/N.E.K.O'
uv run --project "$env:NEKO_ROOT" python -m pytest tests -q
uvx ruff==0.12.4 check --ignore-noqa --config ruff.toml .
uv run --project "$env:NEKO_ROOT" neko-plugin check --release --market-release .
```

也可使用已配置开发环境的 Python 直接执行 `python -m pytest tests -q`。
本地测试通过 `NEKO_ROOT` 找到真实 SDK；官方 CI 将插件挂载到宿主源码树后验证。

## 提交要求

- 使用小范围提交，更新受影响的测试与说明。
- 测试使用临时存储并禁止网络连接、进程启动和消息发送，不依赖真实游戏。
- 不提交令牌、账号会话、私服配置、模型权重、参考音频和个人存档。
- 配置默认不自动开始游戏。启动、停止、取消及接管语义必须可观察、可测试。
- 不把 HTTP 成功、模型输出或工具调用受理等同于动作完成。
- 不修改官方管理的工作流和 Ruff 模板；模板升级通过官方 CLI 流程执行。
- 发布前检查 `.neko-plugin` 内容；测试、开发文档、运行数据和密钥文件不进入运行包。

## 功能与发布边界

新增后端应提供观测、有限时动作、取消及结果回执。正常长动作期间不因例行决策反复取消。
提示词保持固定前缀，动态事实集中在末尾；原文留存及查询入口不能因压缩上下文丢失。

普通源码推送只触发 Verify。后端未完成现场验收前，不创建发布 tag、不手动触发 Release、
不调用 `neko-plugin publish`，也不将开发基础作为可玩的插件提交 Market。
首次 Market 审核及之后的发布遵循官方文档，不能用本地验证冒充审核通过。
