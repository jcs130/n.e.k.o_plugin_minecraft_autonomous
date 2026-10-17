import {
  Page, Card, Stack, Grid, Inline, Text, StatCard, StatusBadge, DataTable,
  Field, Input, Select, Switch, Textarea, Button, ActionButton, RefreshButton,
  Alert, Accordion, JsonView, FileDownload, useState,
} from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"
import { installationGuidance } from "./installation-guidance.js"
import { applyConnectionPreset } from "./connection-presets.js"

export default function Panel(props: PluginSurfaceProps<any>) {
  const { state, actions } = props
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<any>(null)
  const [parametersText, setParametersText] = useState("{}")
  const [routineParameters, setRoutineParameters] = useState("{}")
  const [complexParameters, setComplexParameters] = useState("{}")
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState("append")
  const [requestId, setRequestId] = useState("")
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState("")
  const [failure, setFailure] = useState(false)
  const [fieldError, setFieldError] = useState<any>(null)
  const [modelCheck, setModelCheck] = useState<any>(null)
  const [viewerDraft, setViewerDraft] = useState<string | null>(null)
  const [connectionDraft, setConnectionDraft] = useState<any>(null)
  const [hostModel, setHostModel] = useState<boolean | null>(null)
  const [appearanceDraft, setAppearanceDraft] = useState<string | null>(null)
  const [extensionDraft, setExtensionDraft] = useState<string | null>(null)
  const [characterDraft, setCharacterDraft] = useState<string | null>(null)
  const settings = state.settings || {}
  const runtime = state.runtime || {}
  const audit = state.audit || {}
  const external = settings.runtime?.mode === "external"
  const connection = connectionDraft ?? settings.server ?? {host:"",port:25565,username:"",auth:"offline",version:"1.21.1",connection_type:"local"}
  const setConnection = (key:string,value:any) => setConnectionDraft({...connection,[key]:value,
    ...(key==="host"?{connection_type:["","127.0.0.1","localhost","::1"].includes(value)?"local":"custom"}:{})})
  const usingHostModel = hostModel ?? settings.planner?.route !== "direct"
  const installation = installationGuidance(state.installation, external, state.viewer_url)
  const action = (id: string) => actions.find(a => a.entry_id === id || a.id === id)
  const call = async (id: string, args: any) => {
    setBusy(true); setNotice(""); setFailure(false); setFieldError(null)
    try {
      const transportId = id === "save_settings" ? "save_settings_hosted" : id
      const reply = await props.api.call(action(transportId)?.id || transportId, args, { userInitiated: true })
      const result = reply?.result ?? reply
      if (result?.is_error || result?.error || result?.success === false) {
        const detail = result?.error || result
        if (id === "save_settings") setFieldError({field:detail.field || "", message:detail.message || "配置不合法，请检查设置。"})
        throw new Error(detail.message || "请求未成功，请检查回执。")
      }
      if (id === "check_model" || id === "check_direct_model") setModelCheck(result)
      setNotice("请求已受理，请核对更新后的状态和回执。")
      await props.api.refresh()
      return true
    } catch (error: any) {
      setFailure(true); setNotice(error?.message || "请求未确认，重试将沿用同一个请求 ID。")
      return false
    } finally { setBusy(false) }
  }
  const change = (section: string, key: string, value: any) => {
    const next = { ...draft, [section]: { ...draft[section], [key]: value,
      ...(section === "memory" && ((key === "mode" && value !== "remote") || (key === "provider" && !["powercontext","http"].includes(value))) ? {learning_enabled:false} : {}),
    } }
    if (value !== draft[section]?.[key] && ((section === "backend" && ["node","directory"].includes(key)) ||
        (section === "viewer" && ["renderer_directory","catalog_file","bundled_appearance_catalog_file"].includes(key)))) {
      next.runtime = {...draft.runtime, bundle_root:"", bundle_manifest_sha256:""}
    }
    setDraft(next)
  }
  const field = (section: string, key: string, label: string, type = "text") =>
    <Field label={label}><Stack gap={4}><Input type={type} value={draft?.[section]?.[key] ?? ""} placeholder={section === "server" && key === "host" ? "本机填写 127.0.0.1；远程填写域名或 IP" : ""} onChange={v => change(section, key, type === "number" ? Number(v) : v)} />{fieldError?.field === `${section}.${key}` && <Text>{fieldError.message}</Text>}</Stack></Field>
  const authField = (key: string, label: string) => <Field label={label}><Input value={draft?.planner?.auth?.[key] || ""}
    onChange={v=>change("planner","auth",{...draft.planner.auth,[key]:v})} /></Field>
  const saveDraft = async () => {
    try {
      const parameters = JSON.parse(parametersText)
      const routine = JSON.parse(routineParameters), complex = JSON.parse(complexParameters)
      if ([parameters,routine,complex].some(value=>!value || Array.isArray(value) || typeof value !== "object")) throw new Error()
      if (await call("save_settings",{settings:{...draft,planner:{...draft.planner,parameters},decision_policy:{...draft.decision_policy,routine_parameters:routine,complex_parameters:complex}}})) setEditing(false)
    } catch { setFailure(true); setNotice("模型参数须为有效的 JSON 对象，请检查格式。") }
  }

  return <Page title="Minecraft 自主游玩" subtitle="Java 1.21.1 · 原生任务队列 · Neko 高层目标与演出">
    <Stack gap={18}>
      {state.error && <Alert tone="danger" message="配置或观测暂不可用。请先检查插件配置。" />}
      {runtime.phase === "failed" && <Alert tone="danger" message="框架最近记录为运行失败；下方保留最后观测，刷新页面不会自动恢复游玩。" />}
      <Inline justify="space-between">
        <Inline><StatusBadge label={runtime.phase || "未启动"} tone={runtime.game_connected ? "success" : "default"} />
          <Text>{external ? "独立运行 · Neko 观察与投递" : "Neko 嵌入式运行"}</Text></Inline>
        <RefreshButton label="刷新观测" />
      </Inline>
      <Text>观测时间：{runtime.updated_at || "尚无样本"}。保存的快照不等于当前进程存活；刷新只读取状态，不触发模型或游戏动作。</Text>
      <Grid cols={4} gap={12}>
        <StatCard label="本次运行决策轮次" value={runtime.decisions ?? "—"} />
        <StatCard label="待结算原生动作" value={(runtime.pending || []).length} />
        <StatCard label="最近样本失败回执" value={audit.sample_failed_receipts ?? "—"} />
        <StatCard label="最近样本 Token" value={audit.usage_recorded ? audit.sample_tokens : "未记录"} />
      </Grid>
      {notice && <Alert tone={failure ? "danger" : "info"} message={notice} />}
      <Card title="连接与启动"><Stack gap={12}>
        <Text>填写服务器和账号后即可从这里启动。标准 Minecraft 默认使用通用接口；已安装的扩展资料仅在匹配当前服务器数据后生效。</Text>
        <Inline>
          <Button disabled={busy||runtime.game_connected} onClick={()=>setConnectionDraft({...connection,host:"127.0.0.1",port:25565,version:"1.21.1",connection_type:"local"})}>本机原版</Button>
          <Button disabled={busy||runtime.game_connected} onClick={()=>setConnectionDraft(applyConnectionPreset({server:connection},"qiandeng").server)}>千灯纪公网</Button>
        </Inline>
        <Grid cols={2}>
          <Field label="服务器地址"><Input disabled={busy||runtime.game_connected} value={connection.host||""} placeholder="域名或 IP；本机填 127.0.0.1" onChange={v=>setConnection("host",v)} /></Field>
          <Field label="端口"><Input disabled={busy||runtime.game_connected} type="number" value={connection.port??25565} onChange={v=>setConnection("port",Number(v))} /></Field>
          <Field label={connection.auth==="microsoft"?"Microsoft 账户标识":"玩家昵称"}><Input disabled={busy||runtime.game_connected} value={connection.username||""} onChange={v=>setConnection("username",v)} /></Field>
          <Field label="登录方式"><Select value={connection.auth||"offline"} options={[{value:"offline",label:"离线昵称"},{value:"microsoft",label:"Microsoft 正版账号"}]} onChange={v=>{if(!runtime.game_connected)setConnection("auth",v)}} /></Field>
        </Grid>
        <Text>Minecraft Java 1.21.1。正版账号首次启动后，在下方账户入口完成官方授权。</Text>
        <Grid cols={2}>
          <Field label="Web 角色外观"><Select value={appearanceDraft??settings.viewer?.default_appearance??"bundled:yui-ysm"} options={[{value:"bundled:yui-ysm",label:"自带 YUI YSM"},{value:"bundled:yui-slim",label:"自带 YUI 皮肤"},{value:"server",label:"跟随服务器"}]} onChange={setAppearanceDraft} /></Field>
          <Field label="扩展资料"><Select value={extensionDraft??settings.extension_pack?.mode??"auto"} options={[{value:"auto",label:"自动识别已安装扩展"},{value:"none",label:"仅使用标准 Minecraft"},{value:"custom",label:"保留自定义扩展配置"}]} onChange={setExtensionDraft} /></Field>
          <Field label="参与游戏的 Neko 角色"><Input value={characterDraft??settings.heartbeat?.target??""} placeholder="留空跟随当前 Neko 角色" onChange={setCharacterDraft} /></Field>
        </Grid>
        <Switch label="规划使用 Neko 中绑定的 decision 模型" checked={usingHostModel} onChange={setHostModel} />
        {!usingHostModel&&<Text>保留已配置的独立规划模型；可在高级设置中修改。</Text>}
        <Inline>
          <Button tone="primary" disabled={busy||runtime.game_connected||!connection.host||!connection.username} onClick={async()=>{
            if(await call("quick_start",{connection,goal,use_neko_model:usingHostModel,
              appearance:appearanceDraft??settings.viewer?.default_appearance??"bundled:yui-ysm",
              extension_mode:extensionDraft??settings.extension_pack?.mode??"auto",
              character:characterDraft??settings.heartbeat?.target??""}))setConnectionDraft(null)
          }}>{runtime.game_connected?"正在自主游玩":"保存并一键启动"}</Button>
          <Button disabled={busy||runtime.game_connected||!connectionDraft} onClick={async()=>{
            if(await call("save_settings",{settings:{server:connection}}))setConnectionDraft(null)
          }}>仅保存连接</Button>
          <ActionButton action={action("panel_stop")} />
          {state.viewer_url&&<FileDownload href={state.viewer_url} label="打开 3D 观战" openExternal tone="primary" />}
          {state.operator?.available&&<FileDownload href={state.operator.url} label="账户授权" openExternal />}
        </Inline>
        <Text>启动会启用本次自主游玩和 Neko 主脑参与；不会开启开机自启。正在运行时请先停止并等待动作结束，再切换连接。</Text>
        <Inline><StatusBadge label={runtime.viewer?.available?"观战已连接":"观战待连接"} tone={runtime.viewer?.available?"success":"default"} />
          <StatusBadge label={runtime.viewer?.server_extension?.active?"服务器扩展已识别":"标准 Mineflayer"} tone={runtime.viewer?.server_extension?.active?"success":"default"} />
          <StatusBadge label={state.heartbeat?.enabled&&!state.heartbeat?.explicit_stop?"主脑参与已开启":"主脑参与未开启"} /></Inline>
        {state.server_pack?.mode==="auto"&&!state.server_pack?.available&&<Text>可选扩展资料尚未安装或校验未通过，标准 Minecraft 可照常使用。</Text>}
        {runtime.planner_error&&<Alert tone="warning" message={`规划暂未恢复：${runtime.planner_error}。下方运行详情保留错误和重试状态。`} />}
      </Stack></Card>
      <Card title="观战与状态"><Stack gap={10}>
        <Text>在上方「观战与状态」页查看生命、饥饿、原生任务队列、决策耗时与中间结果，也可独立打开。</Text>
        <FileDownload href={`${props.host?.origin || ""}/plugin/minecraft_autonomous/ui/`} label="打开观战与状态" tone="primary" openExternal />
        <Field label="现代可视化页面地址"><Input value={viewerDraft ?? state.viewer_url ?? ""} placeholder="http://你的观战主机:端口/3dview/" onChange={v=>setViewerDraft(v)} /></Field>
        <Button disabled={busy || viewerDraft === null} onClick={async()=>{
          const url = viewerDraft ?? ""
          if(await call("save_settings",{settings:{viewer:{url}}})) {
            if(draft)setDraft({...draft,viewer:{...draft.viewer,url}})
            setViewerDraft(null)
          }
        }}>仅保存观战地址</Button>
        <Text>使用与当前角色配套的 HTTP(S) 页面。游戏连接成功后默认自动打开一次；重连不重复弹窗，可在设置中关闭。</Text>
        {!state.viewer_url && <Alert tone="info" message="尚未取得可用的观战地址；可配置同角色渲染器与版本资源目录，运行数据仍可查看。" />}
        {runtime.viewer && <Accordion title="资源版本与画面接入状态"><JsonView data={{pack:runtime.viewer.pack,version:runtime.viewer.minecraftVersion,reason:runtime.viewer.reason,window:runtime.viewer_window,content:runtime.viewer.content}} /></Accordion>}
        {state.viewer_url && !state.viewer_body_binding_verified && <Alert tone="warning" message="已保存页面地址；画面与当前 1.21.1 角色的绑定尚未核验。" />}
      </Stack></Card>
      <Card title="当前工作与用户反馈"><Stack gap={12}>
        <ActionButton action={action("review_game")} />
        <ActionButton action={action("present_status")} />
        <Text>当前目标：{runtime.current_goal?.goal || runtime.standing_goal || "尚无目标"}</Text>
        <DataTable data={runtime.pending || []} columns={[{key:"id",label:"原生任务"},{key:"phase",label:"执行状态"}]} emptyText="没有待结算动作" />
        <Textarea value={goal} placeholder="例如：先收集食物，然后在安全地点建立庇护所。" onChange={v => { setGoal(v); setRequestId("") }} />
        <Select value={mode} options={[{value:"append",label:"排队接续"},{value:"insert",label:"安全检查点插入，之后恢复"},{value:"replace",label:"停止旧动作并改变目标"}]} onChange={v => { setMode(v); setRequestId("") }} />
        <Inline>
          <Button tone="primary" disabled={busy || !goal.trim()} onClick={async () => {
            const id = requestId || crypto.randomUUID(); setRequestId(id)
            const ok = await call("panel_intent", {goal, mode, request_id:id})
            if (ok) { setGoal(""); setRequestId("") }
          }}>投递目标</Button>
          {!external && <Button disabled={busy || !goal.trim()} onClick={async () => { await call("panel_start", {goal}) }}>按此目标开始</Button>}
          <ActionButton action={action("panel_stop")} />
        </Inline>
        {requestId && <Text>请求 ID：{requestId}。确认不明时保持相同内容重试。</Text>}
        <Text>受理、原生动作完成、规划器报告和实际目标达成是不同状态。主脑决定阶段目标，独立框架继续规划和执行；正常工作无需重新派发。</Text>
      </Stack></Card>
      <Accordion title="解说与主脑状态"><Stack gap={10}>
        <StatusBadge label={state.heartbeat?.explicit_stop ? "已停止" : state.heartbeat?.enabled ? "已启用" : "未启用"} tone={state.heartbeat?.enabled && !state.heartbeat?.explicit_stop ? "success" : "default"} />
        {external && state.heartbeat?.explicit_stop && <Stack gap={8}>
          <Text>独立框架重新启动后，需要显式恢复 Neko 反馈。下次正常心跳按原配置继续；此操作不启动游戏、不追加任务。</Text>
          <ActionButton action={action("resume_observation")} />
        </Stack>}
        <Text>没有新聊天也会根据新鲜的身体、口粮、物品、任务结果和当前目标复盘。主脑选择继续或插入阶段目标；正常长动作继续执行。</Text>
        <Text>解说只抓一个新重点，说1—2句自然反应。普通背包数量、工具耐久和读取现场不逐条播报；新危险、明显恢复或重要进展可开口。下方解说间隔也作用于决策心跳，突发危险可及时提醒。直接聊天正常回应。</Text>
        <Text>变化合并后限频唤醒；定期复核带上实际进展。等待主脑回执时不重复派单，用户新反馈优先。通知受理不等于主脑决策或语音播放完成。</Text>
        <JsonView data={state.heartbeat || {enabled:false}} />
        <Text>同一个主脑的人格、当前关注和相关记忆可共享给身体规划器；以下仅显示投影元数据，不展示私人正文。</Text>
        <JsonView data={runtime.host_context || {available:false}} />
      </Stack></Accordion>
      <Accordion title="模型与感知详情"><Stack gap={10}>
        <Text>{external ? "当前由独立运行配置决定模型；本插件设置不覆盖外部进程。" : settings.planner?.route === "direct" ? "动作规划使用下方配置的模型服务。Neko 继续负责目标、人格和解说。" : "在 Neko 的模型 API 页面配置模型，并在本插件模型绑定中选择用途。凭据由宿主保管。"}</Text>
        <DataTable data={[
          {slot:"decision",purpose:"动作规划",fallback:"未配置时保留原生队列与规则反射，自然语言规划暂停"},
          {slot:"vision",purpose:"文字＋真实核心 PNG 图像，可与 decision 绑定同一个多模态模型",fallback:"未配置、不支持或失败时使用 decision 的文字事实"},
          {slot:"fast",purpose:"可选聊天模型快速选择",fallback:"未配置或无效时使用规则；在设置中选择 Neko 模型槽后启用"},
        ]} columns={[{key:"slot",label:"用途槽"},{key:"purpose",label:"用途"},{key:"fallback",label:"回退"}]} />
        <Text>System One 模式可接官方 Jev 或兼容的本地 Decider，使用专用 /v1/systemone 接口。默认规则模式不调用快模型。快速选择只提供规划关注点，原生反射与任务队列继续掌管动作。</Text>
        <Grid cols={2}><JsonView data={runtime.model_status || {route:"尚无模型调用记录"}} /><JsonView data={runtime.fast_focus || {configured_mode:settings.fast?.mode || "rules"}} /></Grid>
        <Text>下面的手动检查会调用 Neko 已绑定模型；图像检查使用合成色块，不代表真实游戏画面验收。外部运行的模型不受此检查影响。</Text>
        <Inline><Button disabled={busy} onClick={async()=>{await call("check_model",{mode:"text"})}}>检查文字与工具调用</Button>
          <Button disabled={busy} onClick={async()=>{await call("check_model",{mode:"vision"})}}>检查图像与回退</Button></Inline>
        {!external && settings.planner?.route === "direct" && <Inline>
          <Button disabled={busy} onClick={async()=>{await call("check_direct_model",{catalog:true})}}>读取直连服务的模型列表</Button>
          <Button disabled={busy} onClick={async()=>{await call("check_direct_model",{catalog:false})}}>测试直连模型（使用一次额度）</Button>
        </Inline>}
        {modelCheck && <JsonView data={modelCheck} />}
        <Text>此 headless 后端可读取背包地图图像；现代 3D 画面还需匹配的观战适配。没有真实图像时按文字运行。</Text>
        <Accordion title="上下文预算与最近图像"><JsonView data={{context:runtime.context,perception:runtime.perception}} /></Accordion>
      </Stack></Accordion>
      <Accordion title="账户与皮肤详情"><Stack gap={10}>
        <Text>当前认证：{settings.server?.auth === "microsoft" ? "Microsoft 授权账号" : "离线昵称"}。离线昵称不能登录要求正版验证的服务器。Microsoft 授权后的实际角色名以本机账户页为准。</Text>
        {state.operator?.available ? <FileDownload href={state.operator.url} label="打开本机账户页：授权、状态与取消" openExternal /> : <Alert tone="info" message={state.operator?.guidance || "账户接口暂不可用。启用本机账户端口并显式启动匹配的执行器；Java 客户端请使用自身登录入口。"} />}
        <Text>入口属于运行机器的 127.0.0.1，只能在该机器浏览器打开。执行器更换后请刷新入口。开启页面不自动连接；授权码、实际账号与过期状态仅在独立的本机页面显示，不进入观战流。</Text>
        <Text>Web 默认外观：{settings.viewer?.default_appearance === "server" ? "跟随服务器" : settings.viewer?.default_appearance === "bundled:yui-ysm" ? "随包原始 YUI YSM" : settings.viewer?.default_appearance === "bundled:yui-slim" ? "随包 YUI slim" : "已配置的其他 Web 模型"}。画面中已保存的明确选择优先；未安装匹配资源时不可用。</Text>
        <Text>外观选择按服务器和账号隔离，同一账号重连、重生与刷新后保留。旧观战页记录没有服务器来源，升级后请在「人物模型」重新选择一次（也可选跟随服务器）；旧条目保留，不跨服猜测迁移。</Text>
        <Text>这些选择只影响网页显示，不会修改服务器角色皮肤、Microsoft 全局皮肤或其他玩家看到的外观。服务器皮肤取决于服务器与已授权账号；本插件没有通用的服务器皮肤修改接口。</Text>
      </Stack></Accordion>
      <Accordion title="安装与资源详情"><Stack gap={8}>
        <Text>{installation.preparedRuntime}</Text>
        <Text>后端目录：{state.installation?.backend_directory || "暂不可用"}</Text>
        <Text>要求核心：{state.installation?.required_core_version || "暂不可用"}；本地后端：{installation.backend}</Text>
        <Text>本地渲染资源：{installation.localResources}</Text>
        <Text>{installation.externalView}</Text>
        <Text>仅检查配置目录中的有限元数据；版本匹配不等于后端完整性校验、游戏连接或真实画面验证。实际启动仍执行完整后端校验。</Text>
      </Stack></Accordion>
      <Accordion title="高级设置"><Stack gap={12}>
        <Text>保存不会启动或重启游戏。嵌入式运行参数须先显式停止再修改，观战地址可在上方单独保存。外部模式下，这些设置只改变 Neko 观察入口；独立运行的模型与策略请同步到 standalone 配置。</Text>
        {!editing && <Button onClick={() => { setDraft(JSON.parse(JSON.stringify(settings))); setParametersText(JSON.stringify(settings.planner?.parameters || {},null,2)); setRoutineParameters(JSON.stringify(settings.decision_policy?.routine_parameters || {},null,2));setComplexParameters(JSON.stringify(settings.decision_policy?.complex_parameters || {},null,2));setEditing(true) }}>编辑设置</Button>}
        {editing && draft && <Stack gap={12}>
          <Field label="连接类型"><Stack gap={4}><Select value={draft.server.connection_type || "local"} options={[{value:"local",label:"原版 / 本地服务器（默认）"},{value:"custom",label:"自定义 / 公共服务器"}]} onChange={v=>setDraft({...draft,server:{...draft.server,connection_type:v,...(v === "local" ? {host:"127.0.0.1",port:25565} : {})}})} />{fieldError?.field === "server.connection_type" && <Text>{fieldError.message}</Text>}</Stack></Field>
          {draft.server.connection_type === "custom" && <Button onClick={()=>setDraft(applyConnectionPreset(draft,"qiandeng"))}>填入千灯纪预设（仅草稿）</Button>}
          <Text>千灯纪可选预设：micro.kangqiang.site:25702 · Java 1.21.1。保留你填写的账号和认证方式；空账号仍需填写。只填入草稿，请核对后保存，再显式开始；不会自动连接或授予服务器权限。</Text>
          <Text>开始前必须填写服务器地址和账户。本机服务器通常为 127.0.0.1:25565；远程地址请选择自定义连接。填写与保存均不自动连接。</Text>
          {draft.server.auth === "microsoft" && !draft.operator?.port && <Alert tone="info" message="Microsoft 账户：可先设置 1024–65535 的空闲本机账户端口，保存后显式启动，再在运行机器打开授权页；保持 0 时请由本人查看私有原生设备授权日志。不要把授权码或令牌填到观战页面。" />}
          <Grid cols={2}>
            {field("server","host","服务器地址")}{field("server","port","端口","number")}
            {field("server","username",draft.server.auth === "microsoft" ? "Microsoft 账户标识（原生授权缓存按此隔离）" : "离线玩家昵称（1–16 位字母、数字或下划线）")}
            <Field label="认证方式"><Select value={draft.server.auth} options={[{value:"offline",label:"离线昵称"},{value:"microsoft",label:"Microsoft 正版账号授权"}]} onChange={v=>change("server","auth",v)} /></Field>
            <Field label="请求 Java 版本"><Select value={draft.server.version} options={["1.21.1"]} onChange={v=>change("server","version",v)} /></Field>
            {field("operator","port","本机账户端口（0 关闭；启用后下次显式启动生效）","number")}
            <Field label="运行方式"><Select value={draft.runtime.mode} options={[{value:"embedded",label:"Neko 嵌入式"},{value:"external",label:"独立运行观察入口"}]} onChange={v=>change("runtime","mode",v)} /></Field>
            {field("runtime","data_directory","共享数据目录")}{field("backend","directory","已验证后端目录")}{field("viewer","url","外部观战地址")}
            {field("viewer","renderer_directory","共享渲染器目录（可选）")}{field("viewer","catalog_file","版本资源目录 JSON（可选）")}{field("viewer","listen_port","本机观战端口","number")}
            {field("viewer","bundled_appearance_catalog_file","随包 Web 外观目录（YUI slim / YSM，可选）")}
            <Field label="Web 默认人物模型（只影响观战，下次显式启动生效）"><Select value={draft.viewer.default_appearance ?? "bundled:yui-ysm"} options={[{value:"bundled:yui-ysm",label:"原始 YUI YSM（Neko 默认）"},{value:"bundled:yui-slim",label:"YUI slim 皮肤"},{value:"server",label:"跟随服务器"},...(![undefined,"bundled:yui-ysm","bundled:yui-slim","server"].includes(draft.viewer.default_appearance) ? [{value:draft.viewer.default_appearance,label:"已保存的其他 Web 模型"}] : [])]} onChange={v=>change("viewer","default_appearance",v)} /></Field>
          </Grid>
          <Switch checked={draft.autonomy.enabled} label="允许显式启动自主游玩" onChange={v=>change("autonomy","enabled",v)} />
          <Switch checked={draft.viewer.auto_open !== false} label="进入游戏后自动打开观战界面" onChange={v=>change("viewer","auto_open",v)} />
          <Switch checked={draft.heartbeat?.enabled === true} label="让 Neko 主脑持续参与自主生存决策" onChange={v=>change("heartbeat","enabled",v)} />
          {field("heartbeat","target","主脑角色（留空跟随当前角色）")}
          {field("heartbeat","min_interval_seconds","变化唤醒最小间隔（秒）","number")}
          {field("heartbeat","review_interval_seconds","无新变化时复核间隔（秒）","number")}
          <Switch checked={draft.host_context?.enabled !== false} label="共享主脑人格、当前关注和相关记忆" onChange={v=>change("host_context","enabled",v)} />
          {field("host_context","character_api_url","角色档案接口（可选，仅显式本机 /api/characters 地址）")}
          <Text>启用决策心跳后，自动解说合并到主脑决策中。此设置不启动游戏；关闭只停止主脑自动复盘，独立框架继续运行。</Text>
          <Switch checked={draft.presentation?.enabled === true} label="让 Neko 解说重要游戏变化" onChange={v=>change("presentation","enabled",v)} />
          {field("presentation","target","解说角色（留空跟随 Neko 当前角色）")}
          {field("presentation","min_interval_seconds","普通解说最小间隔（秒，含决策心跳）","number")}
          <Switch checked={draft.perception.enabled} label="接收核心真实图像（无图像或模型时文字回退）" onChange={v=>change("perception","enabled",v)} />
          <Accordion title="模型 API 接入"><Stack gap={10}>
            <Field label="动作规划使用的模型"><Select value={draft.planner?.route || "host"} options={[{value:"host",label:"使用 Neko 模型绑定（默认）"},{value:"direct",label:"单独配置模型服务"}]} onChange={v=>change("planner","route",v)} /></Field>
            {draft.planner?.route === "direct" && <Stack gap={10}>
              <Field label="模型厂商"><Select value={draft.planner.provider} options={[
                {value:"openai-compatible",label:"自建 / 其他兼容服务"},{value:"qwen",label:"阿里云百炼 / 通义千问"},
                {value:"deepseek",label:"DeepSeek"},{value:"kimi",label:"Kimi / 月之暗面"},{value:"glm",label:"智谱 GLM"},
                {value:"doubao",label:"火山方舟 / 豆包"},{value:"siliconflow",label:"硅基流动"},
                {value:"openai",label:"OpenAI"},{value:"anthropic",label:"Anthropic Claude"},{value:"google",label:"Google Gemini"}
              ]} onChange={v=>{setDraft({...draft,planner:{...draft.planner,provider:v,protocol:"",base_url:"",api_key_env:"",parameters:{},auth:{...draft.planner.auth,mode:"api_key"}}});setParametersText("{}")}} /></Field>
              <Grid cols={2}>
                {field("planner","model","模型 ID（按服务商账户填写）")}{field("planner","base_url","API 根地址（预设可留空；自建必填）")}
                <Field label="接口协议"><Select value={draft.planner.protocol || ""} options={[{value:"",label:"厂商默认"},{value:"chat",label:"OpenAI Chat 兼容"},{value:"responses",label:"OpenAI Responses"},{value:"anthropic",label:"Claude Messages"},{value:"gemini",label:"Google Gemini"}]} onChange={v=>change("planner","protocol",v)} /></Field>
                <Field label="认证方式"><Select value={draft.planner.auth?.mode || "api_key"} options={[
                  {value:"api_key",label:"API Key"},{value:"bearer",label:"外部管理的 Bearer / OAuth 令牌"},
                  {value:"oauth",label:"OpenAI / Google 官方 OAuth"},{value:"google_adc",label:"Google 应用默认凭据（ADC）"},{value:"none",label:"无认证（自建服务）"}
                ]} onChange={v=>change("planner","auth",{...draft.planner.auth,mode:v})} /></Field>
                {field("planner","api_key_env","密钥或令牌的环境变量名（不填密钥）")}
                {authField("quota_project","Google 配额项目（按账户要求填写）")}
              </Grid>
              {!external && <Button disabled={busy} onClick={async()=>{
                try { await call("check_direct_model",{catalog:true,planner:{...draft.planner,parameters:JSON.parse(parametersText)}}) }
                catch { setFailure(true);setNotice("请先修正模型参数 JSON。") }
              }}>读取此服务的模型列表（不调用模型）</Button>}
              {draft.planner.auth?.mode === "oauth" && <Stack gap={8}>
                {authField("credential_id","本机授权记录名称")}{authField("client_id","Google OAuth Client ID；OpenAI 初次注册可留空")}
                {authField("client_secret_env","Google Client Secret 环境变量名")}
                <Text>先在运行机器安装共享框架的 auth 可选组件，再以相同配置执行 auth-login。登录在该机器的浏览器完成，令牌保存到系统凭据库。OpenAI OAuth 需启用流式 Responses；Google 需配置自己的 OAuth 项目。这里不会读取其他应用的登录。</Text>
              </Stack>}
              <Switch checked={draft.planner.stream} label="流式接收（完整校验后执行工具）" onChange={v=>change("planner","stream",v)} />
              <Switch checked={draft.planner.image_input} label="所选模型支持图像输入" onChange={v=>change("planner","image_input",v)} />
              <Field label="Chat 接口的输出长度字段"><Select value={draft.planner.output_parameter} options={["max_tokens","max_completion_tokens"]} onChange={v=>change("planner","output_parameter",v)} /></Field>
              <Field label="模型参数（JSON，按所选协议填写）"><Textarea value={parametersText} onChange={setParametersText} /></Field>
              <Text>采样参数可省略，保留模型默认值。Chat 支持 temperature、top_p、reasoning_effort 和厂商 thinking / enable_thinking；Responses 使用 reasoning、text；Claude 使用 thinking、output_config；Gemini 使用 thinkingConfig、topP、topK。输出上限和超时在“调用预算”设置。参数支持取决于具体模型，服务拒绝时会显示失败。</Text>
              <Grid cols={2}>{field("planner","organization","OpenAI Organization（可选）")}{field("planner","project","OpenAI Project（可选）")}
                {field("planner","anthropic_beta","Claude Beta 标头（可选）")}</Grid>
              <Text>百炼可使用自己的业务空间和地域地址。国产厂商预设不会代选模型、切换区域或偷偷回退到另一家服务。</Text>
            </Stack>}
          </Stack></Accordion>
          <Field label="快决策方式"><Select value={draft.fast.mode} options={[{value:"rules",label:"规则（默认）"},{value:"host",label:"Neko fast 模型槽"},{value:"system_one",label:"System One：远程 Jev / 本地 Decider"}]} onChange={v=>change("fast","mode",v)} /></Field>
          {draft.fast.mode === "system_one" && <Grid cols={2}>
            {field("fast","endpoint","完整 System One 端点")}{field("fast","model","模型名")}
            {field("fast","api_key_env","API Key 所在环境变量名（不填密钥）")}
            {field("fast","min_confidence","最低置信度 0–1","number")}
          </Grid>}
          <Accordion title="游戏记忆"><Stack gap={10}>
            <Text>记录游戏中的地点、方法与经验，按服务器和角色隔离。默认本地保存，不需要模型；开启外部检索后会发送游戏笔记和查询，服务不可用时回退本地搜索。</Text>
            <Field label="检索方式"><Select value={draft.memory?.mode || "local"} options={[{value:"local",label:"本地关键词（默认）"},{value:"vector",label:"本地记忆 + 向量模型"},{value:"remote",label:"外挂记忆服务"}]} onChange={v=>change("memory","mode",v)} /></Field>
            {(draft.memory?.mode || "local") !== "local" && <Grid cols={2}>
              {field("memory","endpoint",draft.memory?.mode === "vector" ? "完整 embeddings 地址" : "记忆服务根地址")}
              {field("memory","api_key_env","密钥所在环境变量名称")}
              {field("memory","timeout_ms","等待上限（毫秒）","number")}
              {draft.memory?.mode === "vector" && field("memory","model","向量模型名")}
            </Grid>}
            {draft.memory?.mode === "remote" && <Stack gap={8}>
              <Field label="服务类型"><Select value={draft.memory.provider} options={[{value:"mem0-platform",label:"Mem0 云端"},{value:"mem0-oss",label:"Mem0 自建"},{value:"bailian",label:"阿里云百炼"},{value:"powercontext",label:"PowerContext"},{value:"http",label:"通用 HTTP 桥接"}]} onChange={v=>change("memory","provider",v)} /></Field>
              {draft.memory.provider === "bailian" && <Grid cols={2}>{field("memory","library_id","记忆库 ID（可选）")}{field("memory","project_id","项目 ID")}</Grid>}
              {draft.memory.provider === "powercontext" && <Grid cols={2}>
                {field("memory","scope_id","已有的 Scope ID")}
                <Field label="PowerContext 检索方式"><Select value={draft.memory.search_mode} options={[{value:"text",label:"全文搜索"},{value:"vector",label:"向量搜索"},{value:"hybrid",label:"混合搜索"}]} onChange={v=>change("memory","search_mode",v)} /></Field>
              </Grid>}
              {["powercontext","http"].includes(draft.memory.provider) && <Stack gap={6}>
                <Field label="服务端经验整理"><Switch checked={draft.memory.learning_enabled === true} onChange={v=>change("memory","learning_enabled",v)} /></Field>
                <Text>使用该角色游戏专用的记忆范围。开启后可以提交任务证据、整理待审核经验并按需召回；候选需在记忆服务中人工审核，生成技能不会自动安装。</Text>
              </Stack>}
            </Stack>}
            <Text>基础检索只增强本机游戏笔记；经验整理可召回专用范围内的历史经验。换电脑时要迁移本地笔记与提交回执；历史库存和地点仍须现场复核。</Text>
          </Stack></Accordion>
          <Accordion title="自适应规划深度（可选）"><Stack gap={10}>
            <Switch label="按新任务、失败和死亡证据选择规划预算" checked={draft.decision_policy?.enabled === true} onChange={v=>change("decision_policy","enabled",v)} />
            <Text>默认关闭并保持原模型配置。原生反射与队列持续执行动作；需要规划时才调用现有模型。常规回合用较短预算，新意图、风险、失败恢复和新死亡复盘用复杂预算，均不得超过总输出预算。</Text>
            {draft.decision_policy?.enabled && <Stack gap={10}>
              <Grid cols={2}>{field("decision_policy","routine_output_tokens","常规回合输出预算","number")}{field("decision_policy","complex_output_tokens","复杂回合输出预算","number")}</Grid>
              <Field label="常规回合参数（所选协议支持的 JSON）"><Textarea value={routineParameters} onChange={setRoutineParameters} /></Field>
              <Field label="复杂回合参数（所选协议支持的 JSON）"><Textarea value={complexParameters} onChange={setComplexParameters} /></Field>
              <Text>参数仅用于明确配置的直连模型，不改变模型或端点。Neko 模型槽沿用主程序配置，SDK 未提供的推理参数会明确回退，只调整本次输出预算；不会额外调用一个模型分析深度。</Text>
            </Stack>}
            {runtime.model_status?.decision_profile && <JsonView data={runtime.model_status.decision_profile} />}
          </Stack></Accordion>
          <Accordion title="调用预算"><Stack gap={10}><Text>上下文默认 65536（64K）；服务实际支持时可设为 131072（128K）。保留已设置的其他有效值；32K 服务应使用 32768，此设置不会扩大模型服务容量。</Text><Grid cols={2}>
            {field("autonomy","context_tokens","上下文窗口","number")}{field("autonomy","max_output_tokens","输出预算","number")}
            {field("autonomy","min_decision_seconds","最小决策间隔（秒）","number")}{field("autonomy","max_decisions","最大轮次，0 为持续运行","number")}
            {field("autonomy","model_timeout_seconds","单次模型总超时（秒）","number")}{field("autonomy","max_tool_rounds","每轮最多连续工具回合","number")}
          </Grid></Stack></Accordion>
          <Inline><Button disabled={busy} tone="primary" onClick={saveDraft}>保存设置</Button>
            <Button onClick={()=>{setEditing(false)}}>取消编辑</Button></Inline>
        </Stack>}
      </Stack></Accordion>
      <Accordion title="当前事实"><DataTable data={runtime.facts || []} columns={[{key:"key",label:"类型"},{key:"text",label:"最近观测（限长）"}]} emptyText="等待框架观测" /></Accordion>
      <Accordion title="决策与中间结果"><Stack gap={10}>
        <Text>每类最多读取文件末尾 128 KiB 中的最近 20 条完整记录；统计仅覆盖此样本。展示实际模型回复与工具回执，不生成额外分析。</Text>
        <DataTable data={audit.decisions || []} columns={[{key:"route",label:"模型路由"},{key:"status",label:"结果"},{key:"tools",label:"选用工具"},{key:"latency_ms",label:"耗时 ms"},{key:"reply",label:"回复摘要"}]} emptyText="尚无决策记录" />
        <DataTable data={audit.receipts || []} columns={[{key:"tool",label:"工具"},{key:"failed",label:"失败"},{key:"text",label:"原生回执摘要"}]} emptyText="尚无工具回执" />
        <Accordion title="原生执行标识与审计样本"><JsonView data={audit} /></Accordion>
      </Stack></Accordion>
    </Stack>
  </Page>
}
