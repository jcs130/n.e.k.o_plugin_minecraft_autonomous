import {
  Page, Card, Stack, Grid, Inline, Text, StatCard, StatusBadge, DataTable,
  Field, Input, Select, Switch, Textarea, Button, ActionButton, RefreshButton,
  Alert, Accordion, JsonView, useState,
} from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"

export default function Panel(props: PluginSurfaceProps<any>) {
  const { state, actions } = props
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<any>(null)
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState("append")
  const [requestId, setRequestId] = useState("")
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState("")
  const [failure, setFailure] = useState(false)
  const [modelCheck, setModelCheck] = useState<any>(null)
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
      if (id === "check_model") setModelCheck(result)
      setNotice("请求已受理，请核对更新后的状态和回执。")
      await props.api.refresh()
      return true
    } catch (error: any) {
      setFailure(true); setNotice(error?.message || "请求未确认，重试将沿用同一个请求 ID。")
      return false
    } finally { setBusy(false) }
  }
  const change = (section: string, key: string, value: any) => setDraft({ ...draft, [section]: { ...draft[section], [key]: value } })
  const field = (section: string, key: string, label: string, type = "text") =>
    <Field label={label}><Input type={type} value={draft?.[section]?.[key] ?? ""} onChange={v => change(section, key, type === "number" ? Number(v) : v)} /></Field>

  return <Page title="Minecraft 自主游玩" subtitle="Java 1.21.1 · 原生任务队列 · Neko 高层目标与演出">
    <Stack gap={18}>
      {state.error && <Alert tone="danger" message="配置或观测暂不可用。请先检查插件配置。" />}
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
      <Card title="当前工作与用户反馈"><Stack gap={12}>
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
        <Text>受理、原生动作完成、规划器报告和实际目标达成是不同状态。解说读取观测，不重新派发动作。</Text>
      </Stack></Card>
      <Card title="模型与感知"><Stack gap={10}>
        <Text>{external ? "当前由独立运行配置决定模型；本插件的模型槽不覆盖外部进程。" : "在 Neko 的模型 API 页面配置模型，并在本插件模型绑定中选择用途。凭据由宿主保管。"}</Text>
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
        {modelCheck && <JsonView data={modelCheck} />}
        <Text>此 headless 后端可读取背包地图图像；现代 3D 画面还需匹配的观战适配。没有真实图像时按文字运行。</Text>
        <Accordion title="上下文预算与最近图像"><JsonView data={{context:runtime.context,perception:runtime.perception}} /></Accordion>
      </Stack></Card>
      <Card title="插件设置"><Stack gap={12}>
        <Text>保存不会启动或重启游戏。嵌入式运行期间请先显式停止再改设置。外部模式下，这些设置只改变 Neko 观察入口；独立运行的模型与策略请同步到 standalone 配置。</Text>
        {!editing && <Button onClick={() => { setDraft(JSON.parse(JSON.stringify(settings))); setEditing(true) }}>编辑设置</Button>}
        {editing && draft && <Stack gap={12}>
          <Grid cols={2}>
            {field("server","host","服务器地址")}{field("server","port","端口","number")}
            {field("server","username","玩家名 / Microsoft 账号")}
            <Field label="认证方式"><Select value={draft.server.auth} options={["offline","microsoft"]} onChange={v=>change("server","auth",v)} /></Field>
            <Field label="运行方式"><Select value={draft.runtime.mode} options={[{value:"embedded",label:"Neko 嵌入式"},{value:"external",label:"独立运行观察入口"}]} onChange={v=>change("runtime","mode",v)} /></Field>
            {field("runtime","data_directory","共享数据目录")}{field("backend","directory","已验证后端目录")}{field("viewer","url","外部观战地址")}
          </Grid>
          <Switch checked={draft.autonomy.enabled} label="允许显式启动自主游玩" onChange={v=>change("autonomy","enabled",v)} />
          <Switch checked={draft.perception.enabled} label="接收核心真实图像（无图像或模型时文字回退）" onChange={v=>change("perception","enabled",v)} />
          <Field label="快决策方式"><Select value={draft.fast.mode} options={[{value:"rules",label:"规则（默认）"},{value:"neko",label:"Neko fast 模型槽"},{value:"system_one",label:"System One：远程 Jev / 本地 Decider"}]} onChange={v=>change("fast","mode",v)} /></Field>
          {draft.fast.mode === "system_one" && <Grid cols={2}>
            {field("fast","endpoint","完整 System One 端点")}{field("fast","model","模型名")}
            {field("fast","api_key_env","API Key 所在环境变量名（不填密钥）")}
            {field("fast","min_confidence","最低置信度 0–1","number")}
          </Grid>}
          <Accordion title="调用预算"><Grid cols={2}>
            {field("autonomy","context_tokens","上下文窗口","number")}{field("autonomy","max_output_tokens","输出预算","number")}
            {field("autonomy","min_decision_seconds","最小决策间隔（秒）","number")}{field("autonomy","max_decisions","最大轮次，0 为持续运行","number")}
          </Grid></Accordion>
          <Inline><Button disabled={busy} tone="primary" onClick={async()=>{if(await call("save_settings",{settings:draft}))setEditing(false)}}>保存设置</Button>
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
