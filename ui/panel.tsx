import {
  Page, Card, Stack, Grid, Inline, Text, StatCard, StatusBadge, DataTable,
  Field, Input, Select, Switch, Textarea, Button, ActionButton, RefreshButton,
  Alert, Accordion, JsonView, FileDownload, useState,
} from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"

export default function Panel(props: PluginSurfaceProps<any>) {
  const { state, actions } = props
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<any>(null)
  const [parametersText, setParametersText] = useState("{}")
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState("append")
  const [requestId, setRequestId] = useState("")
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState("")
  const [failure, setFailure] = useState(false)
  const [modelCheck, setModelCheck] = useState<any>(null)
  const [viewerDraft, setViewerDraft] = useState<string | null>(null)
  const settings = state.settings || {}
  const runtime = state.runtime || {}
  const audit = state.audit || {}
  const external = settings.runtime?.mode === "external"
  const action = (id: string) => actions.find(a => a.entry_id === id || a.id === id)
  const call = async (id: string, args: any) => {
    setBusy(true); setNotice(""); setFailure(false)
    try {
      const reply = await props.api.call(action(id)?.id || id, args, { userInitiated: true })
      const result = reply?.result ?? reply
      if (result?.is_error || result?.error || result?.success === false) throw new Error(result?.error?.message || "请求未成功，请检查回执。")
      if (id === "check_model" || id === "check_direct_model") setModelCheck(result)
      setNotice("请求已受理，请核对更新后的状态和回执。")
      await props.api.refresh()
      return true
    } catch (error: any) {
      setFailure(true); setNotice(error?.message || "请求未确认，重试将沿用同一个请求 ID。")
      return false
    } finally { setBusy(false) }
  }
  const change = (section: string, key: string, value: any) => setDraft({ ...draft, [section]: { ...draft[section], [key]: value,
    ...(section === "memory" && ((key === "mode" && value !== "remote") || (key === "provider" && !["powercontext","http"].includes(value))) ? {learning_enabled:false} : {}),
  } })
  const field = (section: string, key: string, label: string, type = "text") =>
    <Field label={label}><Input type={type} value={draft?.[section]?.[key] ?? ""} onChange={v => change(section, key, type === "number" ? Number(v) : v)} /></Field>
  const authField = (key: string, label: string) => <Field label={label}><Input value={draft?.planner?.auth?.[key] || ""}
    onChange={v=>change("planner","auth",{...draft.planner.auth,[key]:v})} /></Field>
  const saveDraft = async () => {
    try {
      const parameters = JSON.parse(parametersText)
      if (!parameters || Array.isArray(parameters) || typeof parameters !== "object") throw new Error()
      if (await call("save_settings",{settings:{...draft,planner:{...draft.planner,parameters}}})) setEditing(false)
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
      <Card title="观战与状态"><Stack gap={10}>
        <Text>在上方「观战与状态」页查看生命、饥饿、原生任务队列、决策耗时与中间结果，也可独立打开。</Text>
        <FileDownload href={`${props.host?.origin || ""}/plugin/minecraft_autonomous/ui/`} label="打开观战与状态" tone="primary" openExternal />
        <Field label="现代可视化页面地址"><Input value={viewerDraft ?? state.viewer_url ?? ""} placeholder="http://你的观战主机:端口/dungeon/" onChange={v=>setViewerDraft(v)} /></Field>
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
      <Card title="Neko 主脑决策心跳"><Stack gap={10}>
        <StatusBadge label={state.heartbeat?.explicit_stop ? "已停止" : state.heartbeat?.enabled ? "已启用" : "未启用"} tone={state.heartbeat?.enabled && !state.heartbeat?.explicit_stop ? "success" : "default"} />
        {external && state.heartbeat?.explicit_stop && <Stack gap={8}>
          <Text>独立框架重新启动后，需要显式恢复 Neko 反馈。下次正常心跳按原配置继续；此操作不启动游戏、不追加任务。</Text>
          <ActionButton action={action("resume_observation")} />
        </Stack>}
        <Text>没有新聊天也会根据新鲜的身体、口粮、物品、任务结果和当前目标复盘。主脑选择继续或插入阶段目标，再由 Neko 解说；正常长动作继续执行。</Text>
        <Text>变化合并后限频唤醒；定期复核带上实际进展。等待主脑回执时不重复派单，用户新反馈优先。通知受理不等于主脑决策或语音播放完成。</Text>
        <JsonView data={state.heartbeat || {enabled:false}} />
      </Stack></Card>
      <Card title="模型与感知"><Stack gap={10}>
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
      </Stack></Card>
      <Card title="插件设置"><Stack gap={12}>
        <Text>保存不会启动或重启游戏。嵌入式运行参数须先显式停止再修改，观战地址可在上方单独保存。外部模式下，这些设置只改变 Neko 观察入口；独立运行的模型与策略请同步到 standalone 配置。</Text>
        {!editing && <Button onClick={() => { setDraft(JSON.parse(JSON.stringify(settings))); setParametersText(JSON.stringify(settings.planner?.parameters || {},null,2)); setEditing(true) }}>编辑设置</Button>}
        {editing && draft && <Stack gap={12}>
          <Grid cols={2}>
            {field("server","host","服务器地址")}{field("server","port","端口","number")}
            {field("server","username","玩家名 / Microsoft 账号")}
            <Field label="认证方式"><Select value={draft.server.auth} options={["offline","microsoft"]} onChange={v=>change("server","auth",v)} /></Field>
            <Field label="运行方式"><Select value={draft.runtime.mode} options={[{value:"embedded",label:"Neko 嵌入式"},{value:"external",label:"独立运行观察入口"}]} onChange={v=>change("runtime","mode",v)} /></Field>
            {field("runtime","data_directory","共享数据目录")}{field("backend","directory","已验证后端目录")}{field("viewer","url","外部观战地址")}
            {field("viewer","renderer_directory","共享渲染器目录（可选）")}{field("viewer","catalog_file","版本资源目录 JSON（可选）")}{field("viewer","listen_port","本机观战端口","number")}
          </Grid>
          <Switch checked={draft.autonomy.enabled} label="允许显式启动自主游玩" onChange={v=>change("autonomy","enabled",v)} />
          <Switch checked={draft.viewer.auto_open !== false} label="进入游戏后自动打开观战界面" onChange={v=>change("viewer","auto_open",v)} />
          <Switch checked={draft.heartbeat?.enabled === true} label="让 Neko 主脑持续参与自主生存决策" onChange={v=>change("heartbeat","enabled",v)} />
          {field("heartbeat","target","主脑角色（留空跟随当前角色）")}
          {field("heartbeat","min_interval_seconds","变化唤醒最小间隔（秒）","number")}
          {field("heartbeat","review_interval_seconds","无新变化时复核间隔（秒）","number")}
          <Text>启用决策心跳后，自动解说合并到主脑决策中。此设置不启动游戏；关闭只停止主脑自动复盘，独立框架继续运行。</Text>
          <Switch checked={draft.presentation?.enabled === true} label="让 Neko 解说重要游戏变化" onChange={v=>change("presentation","enabled",v)} />
          {field("presentation","target","解说角色（留空跟随 Neko 当前角色）")}
          {field("presentation","min_interval_seconds","解说最小间隔（秒）","number")}
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
          <Accordion title="调用预算"><Grid cols={2}>
            {field("autonomy","context_tokens","上下文窗口","number")}{field("autonomy","max_output_tokens","输出预算","number")}
            {field("autonomy","min_decision_seconds","最小决策间隔（秒）","number")}{field("autonomy","max_decisions","最大轮次，0 为持续运行","number")}
            {field("autonomy","model_timeout_seconds","单次模型总超时（秒）","number")}{field("autonomy","max_tool_rounds","每轮最多连续工具回合","number")}
          </Grid></Accordion>
          <Inline><Button disabled={busy} tone="primary" onClick={saveDraft}>保存设置</Button>
            <Button onClick={()=>{setEditing(false)}}>取消编辑</Button></Inline>
        </Stack>}
      </Stack></Card>
      <Card title="当前事实"><DataTable data={runtime.facts || []} columns={[{key:"key",label:"类型"},{key:"text",label:"最近观测（限长）"}]} emptyText="等待框架观测" /></Card>
      <Card title="决策与中间结果"><Stack gap={10}>
        <Text>每类最多读取文件末尾 128 KiB 中的最近 20 条完整记录；统计仅覆盖此样本。展示实际模型回复与工具回执，不生成额外分析。</Text>
        <DataTable data={audit.decisions || []} columns={[{key:"route",label:"模型路由"},{key:"status",label:"结果"},{key:"tools",label:"选用工具"},{key:"latency_ms",label:"耗时 ms"},{key:"reply",label:"回复摘要"}]} emptyText="尚无决策记录" />
        <DataTable data={audit.receipts || []} columns={[{key:"tool",label:"工具"},{key:"failed",label:"失败"},{key:"text",label:"原生回执摘要"}]} emptyText="尚无工具回执" />
        <Accordion title="原生执行标识与审计样本"><JsonView data={audit} /></Accordion>
      </Stack></Card>
    </Stack>
  </Page>
}
