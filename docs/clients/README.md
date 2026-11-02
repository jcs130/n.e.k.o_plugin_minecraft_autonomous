# 和猫娘一起玩，或使用本人 Eye 观战

这些是可选的启动器导入清单，不是 Neko 运行依赖。主插件仍使用自己的 Node 原生执行器和浏览器 3D 观战，无需安装 Minecraft 服务端或启动第二个游戏角色。

在插件「观战与状态 → 一起玩 / Eye 观战客户端」下载 `.mrpack`，使用支持 Modrinth 导入的启动器并选择 Java 21。清单只含原作者 CDN 链接、大小和 SHA1/SHA512；不会把 YSM 等原作者模组重新打包上传，也不带完整 Minecraft、账户缓存、`servers.dat`、私人配置或世界。原始模组三份合计 88,092,975 字节已下载并逐项校验。客户端下载和插件更新分别进行。

| 选择 | 当前内容 | 验收边界 |
| --- | --- | --- |
| 最新 NeoForge 清单 | Minecraft 1.21.1 / NeoForge 21.1.265 / 女仆 1.5.3 / YSM 2.6.5 / RPG-HUD 3.13 | 官方版本和原模组摘要已核；本轮未启动完整客户端，真实协商、入服及渲染尚未验收 |
| 配套基线清单 | 相同模组，NeoForge 21.1.252 | 服务器公开兼容记录采用此基线；新导入 profile 仍需本人核对实际显示 |

## 真人客户端

使用自己的普通角色登录 `micro.kangqiang.site:25702`。已有角色沿用原游戏密码；Neko 自动账号入口创建的是普通 Agent 体验角色，不创建管理员、Eye 或与猫娘计划账户的关联。网站登录密码与游戏登录材料分别管理。

## Eye 观战与 RPG-HUD

必须使用本人本体对应、服务端已认可的 Eye 身份。本体先完成真实认证并进入世界，然后按原配对使用 `<本体名>_eye` 或 `<本体名>eye`；已有显式别名优先。长旧名字不能为安装而改名，应由服主按原规则登记别名。本插件不代建 Eye、不拷贝共享密码、不修改服务端授权。新默认普通角色名最多 12 字符，为 `_eye` 留出长度，已保存角色名保持。

收到原生登录成功后，还要确认真实旁观模式及实际附身到对应本体。Eye 连接出现注册提示时，不自行发送 `/register`。本体退出、配对撤销、世界或相机不匹配时，转发应停止。

标准 NeoForge Eye 可以接收服务器授权的原版标题、动作栏、消息、效果、BossBar、声音及原版状态转发。本包已加入真正的 **RPG-HUD 3.13 NeoForge 1.21.1**，并在 `config/RPG-HUD` 预置原作者的 `default` 样式；无需手改代码即可启用 RPG 界面。

RPG-HUD 从客户端原版生命、饥饿和经验字段绘制状态，Eye 对应转发能为其提供输入；生命上限、吸收等属性不能只凭健康包推断。原作者的旁观快捷栏仍回到原版 SpectatorGui，**不声称目标九格快捷栏或完整容器已显示**。这与服务器专用 `mcviewer:state` / `corti:viewer_state` 技能、魔力面板是不同接口；后者的现有 NativeObserver/SpectatorPlus 客户端为 Fabric 实现，本包没有混装。YSM 外观又是独立通道。新 NeoForge profile 尚未启动实服验证这些画面。网页 3D 观战继续保留。

## 官方来源

- [NeoForge Maven](https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml)
- [YSM 2.6.5 NeoForge](https://modrinth.com/mod/yes-steve-model/version/2.6.5-neoforge%2Bmc1.21.1)，原项目保留权利；由启动器从原作者下载。
- [Touhou Little Maid 1.5.3](https://modrinth.com/mod/touhou-little-maid/version/tXG1TkGx)，代码与模型等资源分别按原许可。
- [RPG-HUD 3.13 NeoForge](https://modrinth.com/mod/rpg-hud/version/rColiNyN)，GPL-3.0-or-later；原作者配置和旁观绘制范围以 [固定源码](https://github.com/Raelzaryn/RPG-Hud/tree/693e20760e5e0a606cfc73a539d22ad83326ec15) 为准。
- [Eye 原配对规则](https://github.com/jcs130/minecraft-ai-friend/blob/main/paper/docs/AGENT_EYES.md)

没有登录令牌、密码、认证平台参数或模型 Key 进入这些文件。安装清单可公开转发；不要转发自己的启动器账户目录或私有身份文件。
