# 在 Neko App 安装与更新

## 0.6.114：在插件页准备组件

正常从 App 市场安装插件，打开「配置与控制」，点击「准备游戏组件」。页面显示下载、解压、完整校验和安装阶段，可取消或重试。组件使用当前用户的短缓存，无需管理员权限、开启长路径支持、注册表设置或另写命令。安装和临时文件收尾可能需要数分钟，请等到显示「游戏组件已就绪」。完成后选择服务器和身份、绑定模型，再点击「开始自主游玩」；准备组件本身不会进服或调用模型。

插件更新继续由 App 的市场来源和更新事务负责。游戏组件按当前插件固定的版本和摘要准备，保留账号、模型及独立数据；运行中的身体、自定义运行环境或未结算动作会阻止替换。离线用户可下载同版本完整 ZIP，完整解压后运行「一键安装.cmd」。

## Windows 首次安装

当前版本 **0.6.114** 的同一个官方包支持 **Windows x64 与 Linux x64 / CPython 3.11**。它保留标准 Linux vendor，并通过插件自己的完整校验资源选择 Windows 原生依赖；不替换或重载宿主已经加载的依赖，不修改 Neko 或 SDK。旧市场 0.6.109 包只有 Linux 原生依赖，不要混用旧包的验收记录。

Windows 首次使用可直接在 App 市场安装，再点插件内的「准备游戏组件」。离线使用下载 [0.6.114 完整包](https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous/releases/download/v0.6.114/NEKO-MC-0.6.114-Windows.zip)：完整解压、运行「一键安装.cmd」准备短缓存，再在 Neko App 导入相邻 `.neko-plugin`。单独插件文件不内嵌约 1.02 GB 的完整音画与执行组件，由显式准备按钮获取。最新资源已在 `longPathAware=false` 的进程中实装并全量校验，注册表未修改；既有中文/空格、长路径和移动源目录复用边界保留。官网原默认包仍为 0.6.109，更新官网默认版本是独立部署。

打开本插件，只需填写服务器与玩家身份、绑定 Neko 的 `decision` 模型，然后显式开始。只有要求 `/login` 的服务器才需要展开「服务器登录密码」并保存原账号密码。不会替用户注册或设置新的服务器密码。

## Market 的一键安装

Neko App 先与 Market 配对，然后把安装请求交给本机插件管理器。管理器核对市场登记的下载地址、版本、包 SHA256 和 payload hash，预检冲突，再执行安装事务。市场只有一份登记包时，不能通过网页按钮把另一份 Windows ZIP 当成这份包安装。

官方 `plugin-market-release.yml` 使用 `ubuntu-latest`，发布工作流保持标准模板。自 0.6.111 起保留这份包的 Linux vendor，另在 `assets/python-runtime` 内携带逐成员验证的 Windows CPython 3.11 x64 依赖，导入时按实际平台选择。同一份官方 CI 产物分别验 Windows 冷导入、宿主已加载依赖和真实 Neko 运行，Linux 由官方流程验证。沿用原同包、来源锁与更新事务。

## 更新到底会自动做什么

App 会为有 Market 来源记录的插件检查新版本、显示更新提示。用户点「更新」或「全部更新」后，按安装来源和版本串行预检/下载/校验/替换，保留独立配置与数据，并在失败时尝试回滚。不是无人确认的后台覆盖。

从本地文件导入的包记录为 imported，不会自动变为 Market 来源，也不能保证进入 Market 自动更新链。新文件仍通过插件中心导入覆盖升级，核对插件 ID 与版本后确认。不要在插件内部再加一个绕过宿主来源锁的自动更新器。

插件更新与 MC 运行环境更新分开。旧离线资源绑定不兼容时，在停止游玩后使用「使用已安装的新版运行环境」；它保留账号、模型和数据，只在下一次启动选择已准备的兼容缓存。

## 新配置界面

服务器密码输入只写不读，Windows 下使用当前 Windows 用户的 DPAPI 加密；换机器或 Windows 用户时须重新填写。高级的 `server.login_config_file` 仍支持原私有登录文件。重新填写游戏密码不等于执行游戏改密命令。

MC 行为选项放在折叠的「MC 核心行为」中。留空或「跟随核心」不写入覆盖值；自动战斗、受击反射、旅途、空闲动作、垫脚材料、容器演出可以单独调整，不开放服务器进程、提权、碰撞或库存/未知回执门禁。

DeepSeek 官方 [思考模式](https://api-docs.deepseek.com/guides/thinking_mode/) 支持关闭思考和 low/high/max，`deepseek-flash` 当前由 V4.1-Flash-1017 提供。插件直接模型路线提供预设，并为保守字节计数设置至少262144的窗口预算，以容纳完整原生工具声明；它不是实测 token，也不会直接填满模型的1M上下文。Neko 模型绑定路线的参数由宿主控制，不能把插件显示的预算选择冒充宿主已采用的思考参数。调用时保留工具历史要求的 reasoning 内容，不向解说正文转发。

## 官方来源核对

此前核对的官方源码固定`3f12697fb722d61e37bb9e4c0ead33205b2d5651`：[Market工作流](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/.github/workflows/plugin-market-release.yml)、[App更新控制](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/frontend/plugin-manager/src/stores/pluginUpdates.ts)、[安装确认与事务](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/frontend/plugin-manager/src/composables/usePluginPackageInstaller.ts)。本插件通过自己的平台资源适配现有协议，不要求用户应用宿主补丁或未采纳的发行字段。
