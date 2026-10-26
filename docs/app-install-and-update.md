# 在 Neko App 安装与更新

## Windows 首次安装

当前已发布的市场 0.6.109 默认包是 **Linux x64 / CPython 3.11**，不是 Windows 包。市场页面中另有 Windows 完整包入口。请勿把“已导入文件”当成其内 Linux 扩展能在 Windows 上运行。

Windows 用户目前使用官网 [Windows 完整包](https://mc.kangqiang.site/downloads/neko)：完整解压、运行「一键安装.cmd」准备短缓存，再在 Neko App 的插件中心导入其中的 Windows `.neko-plugin`。不需要管理员权限或修改系统长路径注册表。原解压目录的中文/空格/长路径和缓存解析分别验收；源码目录或单独插件文件不等于完整运行环境。

打开本插件，只需填写服务器与玩家身份、绑定 Neko 的 `decision` 模型，然后显式开始。只有要求 `/login` 的服务器才需要展开「服务器登录密码」并保存原账号密码。不会替用户注册或设置新的服务器密码。

## Market 的一键安装

Neko App 先与 Market 配对，然后把安装请求交给本机插件管理器。管理器核对市场登记的下载地址、版本、包 SHA256 和 payload hash，预检冲突，再执行安装事务。市场只有一份登记包时，不能通过网页按钮把另一份 Windows ZIP 当成这份包安装。

本次核查的官方 `plugin-market-release.yml` 固定 `ubuntu-latest`，没有平台输入。官方 CLI 还检查插件的发布工作流必须保持标准模板。要让市场默认交付 Windows 二进制，需要官方可信构建/发行支持 Windows 目标；替换附件、手写或改写官方证据会破坏来源校验，不作为解决方案。

## 更新到底会自动做什么

App 会为有 Market 来源记录的插件检查新版本、显示更新提示。用户点「更新」或「全部更新」后，按安装来源和版本串行预检/下载/校验/替换，保留独立配置与数据，并在失败时尝试回滚。不是无人确认的后台覆盖。

从本地 Windows 文件导入的包记录为 imported，不会自动变成 Linux Market 包，也不能保证进入 Market 自动更新链。新 Windows 文件仍通过插件中心导入覆盖升级，核对插件 ID 与版本后确认。不要在插件内部再加一个绕过宿主来源锁的自动更新器。

插件更新与 MC 运行环境更新分开。旧离线资源绑定不兼容时，在停止游玩后使用「使用已安装的新版运行环境」；它保留账号、模型和数据，只在下一次启动选择已准备的兼容缓存。

## 新配置界面

服务器密码输入只写不读，Windows 下使用当前 Windows 用户的 DPAPI 加密；换机器或 Windows 用户时须重新填写。高级的 `server.login_config_file` 仍支持原私有登录文件。重新填写游戏密码不等于执行游戏改密命令。

MC 行为选项放在折叠的「MC 核心行为」中。留空或「跟随核心」不写入覆盖值；自动战斗、受击反射、旅途、空闲动作、垫脚材料、容器演出可以单独调整，不开放服务器进程、提权、碰撞或库存/未知回执门禁。

DeepSeek 官方 [思考模式](https://api-docs.deepseek.com/guides/thinking_mode/) 支持关闭思考和 low/high/max，`deepseek-flash` 当前由 V4.1-Flash-1017 提供。插件直接模型路线提供预设，并为保守字节计数设置至少262144的窗口预算，以容纳完整原生工具声明；它不是实测 token，也不会直接填满模型的1M上下文。Neko 模型绑定路线的参数由宿主控制，不能把插件显示的预算选择冒充宿主已采用的思考参数。调用时保留工具历史要求的 reasoning 内容，不向解说正文转发。

## 官方来源核对

截至2026-10-26，官方最新源码固定`3f12697fb722d61e37bb9e4c0ead33205b2d5651`：[Market工作流](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/.github/workflows/plugin-market-release.yml)、[App更新控制](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/frontend/plugin-manager/src/stores/pluginUpdates.ts)、[安装确认与事务](https://github.com/Project-N-E-K-O/N.E.K.O/blob/3f12697fb722d61e37bb9e4c0ead33205b2d5651/frontend/plugin-manager/src/composables/usePluginPackageInstaller.ts)。当前没有已生效的Windows市场目标配置；不应把未应用的上游提案字段写进用户安装步骤。
