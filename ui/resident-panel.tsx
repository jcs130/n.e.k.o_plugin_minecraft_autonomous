import { Alert, Button, Card, Field, FileDownload, Inline, Input, Page, PasswordInput, RefreshButton, Select, Stack, StatusBadge, Text, Textarea, useEffect, useRef, useState, useToast } from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"
import { startPanelRefresh } from "./panel-refresh.js"

type Resident = { id: string, characterId: string, name: string, bodyKind: string, state: string }
type State = { role?: string, localRoles?: string[], resident?: string, connected?: boolean, authorized?: boolean,
  bodyKind?: string, control?: { phase?: string, health?: string, playerBusy?: boolean },
  uiToken?: string, browserCode?: string, waiting?: string, catalog?: { residents?: Resident[], availableBodies?: string[] } }

export default function ResidentPanel(props: PluginSurfaceProps<State>) {
  const state = props.state || {}
  const roles = state.localRoles || []
  const bodies = state.catalog?.availableBodies || []
  const residents = state.catalog?.residents || []
  const [mode, setMode] = useState("connect")
  const [role, setRole] = useState<string | null>(null)
  const [kind, setKind] = useState("")
  const [id, setId] = useState("")
  const [name, setName] = useState<string | null>(null)
  const [persona, setPersona] = useState("")
  const [code, setCode] = useState("")
  const [manual, setManual] = useState(false)
  const [busy, setBusy] = useState(false)
  const checking = useRef(false)
  const localRole = (role ?? state.role) || roles[0] || ""
  const selected = residents.find(row => row.id === id) || residents[0]
  const bodyKind = bodies.includes(kind) ? kind : bodies[0]
  const chosenName = name ?? localRole
  const phase = state.control?.phase || "stopped"
  const health = state.control?.health || "idle"
  const controlling = phase !== "stopped"
  const toast = useToast()
  const label = (kind: string) => kind === "maid" ? "车万女仆" : "Numen"

  async function call(entry: string, args: Record<string, unknown>) {
    setBusy(true)
    try {
      await props.api.call(entry, { ...args, uiToken: state.uiToken })
      if (entry === "pair_resident") setCode("")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    } finally {
      try { await props.api.refresh() } finally { setBusy(false) }
    }
  }

  useEffect(() => {
    const browser = state.browserCode && !state.authorized
    if (!browser && (!state.waiting || !state.authorized)) return
    const timer = window.setInterval(async () => {
      if (checking.current || document.hidden) return
      checking.current = true
      try {
        await props.api.call(browser ? "resident_browser_login" : "manage_residents", {
          op: browser ? "status" : "list", uiToken: state.uiToken,
        })
      } catch {
        // Network interruptions can be retried while this panel is open.
      } finally {
        try { await props.api.refresh() } catch {} finally { checking.current = false }
      }
    }, 3000)
    return () => window.clearInterval(timer)
  }, [state.waiting, state.browserCode, state.authorized, state.uiToken])

  useEffect(() => {
    if (!controlling || busy) return
    return startPanelRefresh({refresh: props.api.refresh, document, interval: 6000})
  }, [props.api.refresh, controlling, busy])

  return <Page title="连接千灯纪居民"><Stack gap={14}>
    <Card title={state.connected ? `${state.role} → ${state.resident}` : "使用千灯纪女仆或 Numen"}><Stack gap={10}>
      <Text>选择本机角色，在官网确认六位数字，再选择已有居民或新建。游戏服运行身体，桌面无需准备玩家游戏组件。</Text>
      <Inline>
        <FileDownload href={`${props.host?.origin || ""}/ui/plugins/minecraft_autonomous?tab=panel&surface=main`}
          label="切到玩家模式" openExternal />
        <RefreshButton label="刷新状态" />
      </Inline>
      {state.connected && <>
        <Inline>
          {state.bodyKind ? <StatusBadge label={label(state.bodyKind)} /> : null}
          <StatusBadge label={phase === "running" ? (health === "turn_open" ? "正在处理回合" : "桌面控制已开启")
            : phase === "stopping" ? "正在停止" : phase === "starting" ? "正在核对连接" : "已绑定，桌面控制已停止"}
            tone={phase === "running" && ["waiting", "turn_open"].includes(health) ? "success" : "default"} />
        </Inline>
        {health === "reauthorize" && <Alert tone="warning" message={controlling ? "授权已失效。请先停止桌面控制，再重新授权。" : "请重新在官网授权并选择原居民。"} />}
        {health === "unavailable" && <Alert tone="info" message="暂时无法获取或交付居民回合，可以刷新查看状态。" />}
        {state.control?.playerBusy && !controlling && <Alert tone="info" message="请先停止玩家模式，再开始居民桌面控制。" />}
        {controlling ? <Button tone="danger" disabled={busy || !state.uiToken} onClick={() => call("resident_stop", {})}>
          停止桌面控制
        </Button> : <Button tone="primary" disabled={busy || !state.uiToken || state.control?.playerBusy || health === "reauthorize"}
          onClick={() => call("resident_start", {})}>开始桌面控制</Button>}
        <Text>停止桌面控制后，千灯纪可依服务器设置继续托管该居民。</Text>
      </>}
    </Stack></Card>
    {!controlling && <>
    <Card title="本机 N.E.K.O. 角色"><Stack>
      <Text>若这个身体已经接到旧版「千灯纪居民」或酒狐，请先停止旧连接，再到这里授权原角色。</Text>
      <Field required label="由哪个角色在游戏里行动">{roles.length ?
        <Select value={localRole} options={roles.map(value => ({ value, label: value }))} onChange={setRole} /> :
        <Input value={localRole} onChange={setRole} placeholder="本机角色名" />}
      </Field>
      <Inline>
        <Button disabled={!state.uiToken || busy} onClick={() => call("open_resident_website", { page: "characters" })}>打开 N.E.K.O. 角色管理</Button>
        <Button disabled={busy} onClick={() => props.api.refresh()}>刷新本机角色</Button>
      </Inline>
    </Stack></Card>
    {!state.authorized ? <Card title="登录千灯纪"><Stack>
      <Button tone="primary" disabled={!state.uiToken || busy} onClick={() => call("resident_browser_login", { op: "start" })}>
        {state.browserCode ? "重新打开授权页" : "在浏览器登录并授权"}
      </Button>
      {state.browserCode ? <Text>请在官网输入 {state.browserCode}。确认后，这里会自动显示游戏角色。</Text> : null}
      <Button disabled={busy} onClick={() => setManual(!manual)}>{manual ? "收起授权码入口" : "改用授权码"}</Button>
      {manual ? <Stack>
        <Button disabled={!state.uiToken || busy} onClick={() => call("open_resident_website", { page: "authorize" })}>去官网获取授权码</Button>
        <Field label="官网授权码"><PasswordInput value={code} onChange={setCode} placeholder="XXXX-XXXX-XXXX" /></Field>
        <Button disabled={busy || !state.uiToken || !code.trim()}
          onClick={() => call("pair_resident", { code: code.trim(), localRole })}>验证授权码</Button>
      </Stack> : null}
    </Stack></Card> : <Card title="选择游戏角色"><Stack>
      <Inline>
        <Button tone={mode === "connect" ? "primary" : "default"} disabled={busy} onClick={() => { setMode("connect") }}>已有角色</Button>
        <Button tone={mode === "create" ? "primary" : "default"} disabled={busy} onClick={() => { setMode("create") }}>新建角色</Button>
      </Inline>
      {mode === "connect" ? (selected ? <Stack>
        <Field label="我的角色"><Select value={selected.id} onChange={setId} options={residents.map(row => ({
          value: row.id, label: row.name + " · " + label(row.bodyKind) + (row.state === "preparing" ? "（准备中）" : "")
        }))} /></Field>
        <Button disabled={busy || !!state.waiting || !localRole} onClick={() => call("manage_residents", {
          op: "connect", id: selected.id, characterId: selected.characterId, localRole
        })}>绑定这个角色</Button>
      </Stack> : <Text>这个账号还没有游戏角色，可以新建一个。</Text>) : (bodyKind ? <Stack>
        <Field label="身体"><Select value={bodyKind} onChange={setKind} options={bodies.map(value => ({ value, label: label(value) }))} /></Field>
        <Field required label="游戏角色名"><Input value={chosenName} onChange={setName} /></Field>
        <Field label="游戏中的角色设定（可选）"><Textarea value={persona} onChange={setPersona} /></Field>
        <Button disabled={busy || !!state.waiting || !localRole || !chosenName.trim()} onClick={() => call("manage_residents", {
          op: "create", localRole, bodyKind, name: chosenName.trim(), persona
        })}>创建并绑定</Button>
      </Stack> : <Text>服务器当前没有可用的新身体。</Text>)}
      {state.waiting ? <Text>正在准备 {state.waiting} 的游戏身体。准备好后会保存绑定，你可以再手动开始。</Text> : null}
      <Button disabled={busy} onClick={() => call("manage_residents", { op: "list" })}>刷新游戏角色</Button>
    </Stack></Card>}
    </>}
  </Stack></Page>
}
