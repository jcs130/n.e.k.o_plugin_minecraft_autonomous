import { Alert, Button, Card, Field, FileDownload, Inline, Input, Page, PasswordInput, RefreshButton, Select, Stack, StatusBadge, Text, Textarea, useEffect, useRef, useState, useToast } from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"
import { startPanelRefresh } from "./panel-refresh.js"
import { residentSelection } from "./resident-selection.js"

type Resident = { id: string, characterId: string, name: string, bodyKind: string, state: string }
type Body = {characterId: string, name: string, activeKind: string | null, status: string,
  pendingRequestId: string | null, generation: number | null, targetKinds: string[], autonomous: boolean}
type Receipt = {characterId: string, requestId: string, status: string, activeKind: string | null,
  targetKind: string, generation: number, reason: string | null}
type VoiceStatus = {transcriptReceived: boolean, outputModes: string[],
  receipt: {state: string, captionRecipients?: number} | null}
const bodyNames: Record<string, string> = {maid: "车万女仆", numen: "Numen", mineflayer: "Mineflayer 玩家", villager: "村民"}
const statuses: Record<string, string> = {ready:"可用", switching:"交接中", recovery_required:"待核实",
  completed:"已完成", blocked:"本次未执行"}
const receiptReasons: Record<string, string> = {
  SOURCE_NOT_READY: "原身体未就绪", TARGET_NOT_READY: "目标身体未就绪",
  SOURCE_RELEASE_UNCONFIRMED: "原身体尚未确认释放", TARGET_ACQUIRE_UNCONFIRMED: "目标身体尚未确认接管",
  SERVICE_RESTART: "服务已重启，需核对原回执", ORIGINAL_RECEIPTS_CONFIRMED: "服务端已核对原回执",
}
const voiceModes: Record<string, string> = {text: "游戏文字", speech: "语音", native: "身体默认方式"}
const voiceStates: Record<string, string> = {
  submitted: "已提交", queued: "等待播报", playing: "正在播报", sent: "服务端已发送音频",
  failed: "播报失败", skipped: "已跳过播报", cancelled: "播报已取消", unknown: "待核实", unavailable: "语音暂不可用",
}
type State = { role?: string, localRoles?: string[], resident?: string, connected?: boolean, authorized?: boolean,
  bodyReadable?: boolean, bodyView?: {available: boolean, characters: Body[]},
  bodyReceipt?: Receipt,
  bodyDeviceAvailable?: boolean, bodyDevice?: {state: string, pairId?: string, characterId?: string, expiresAt?: number},
  bodyKind?: string, control?: { phase?: string, health?: string, playerBusy?: boolean, voice?: VoiceStatus },
  uiToken?: string, browserCode?: string, characterId?: string, waiting?: string, catalog?: { residents?: Resident[], availableBodies?: string[] } }

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
  const [characterId, setCharacterId] = useState("")
  const [receiptId, setReceiptId] = useState("")
  const bodyRows = state.bodyView?.available ? state.bodyView.characters : []
  const character = bodyRows.find(row => row.characterId === characterId) || bodyRows[0]
  const original = receiptId.trim() || character?.pendingRequestId || ""
  const receipt = state.bodyReceipt?.characterId === character?.characterId && state.bodyReceipt?.requestId === original
    ? state.bodyReceipt : null
  const canShowDevice = !!state.bodyDeviceAvailable && !!state.bodyView?.available &&
    (!!character || state.bodyDevice?.state === "pending" || state.bodyDevice?.state === "paired")
  const checking = useRef(false)
  const localRole = (role ?? state.role) || roles[0] || ""
  const selected = residentSelection(residents, id, state.characterId, state.bodyKind)
  const bodyKind = bodies.includes(kind) ? kind : bodies[0]
  const chosenName = name ?? localRole
  const phase = state.control?.phase || "stopped"
  const health = state.control?.health || "idle"
  const controlling = phase !== "stopped"
  const voice = state.control?.voice
  const offeredVoiceModes = voice?.outputModes.map(mode => voiceModes[mode]).filter(Boolean) || []
  const toast = useToast()
  const label = (kind: string) => Object.hasOwn(bodyNames, kind) ? bodyNames[kind] : "身体待核实"

  async function call(entry: string, args: Record<string, unknown>) {
    setBusy(true)
    try {
      const reply = await props.api.call(entry, { ...args, uiToken: state.uiToken })
      const result = reply?.result ?? reply
      if (result?.is_error || result?.error || result?.success === false) {
        throw new Error((result.error || result).message || "操作未确认，请刷新后核对。")
      }
      if (entry === "pair_resident") setCode("")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    } finally {
      try { await props.api.refresh() } finally { setBusy(false) }
    }
  }

  useEffect(() => {
    if (!state.waiting || !state.authorized) return
    const timer = window.setInterval(async () => {
      if (checking.current || document.hidden) return
      checking.current = true
      try {
        await props.api.call("manage_residents", {op: "list", uiToken: state.uiToken})
      } catch {
        // Network interruptions can be retried while this panel is open.
      } finally {
        try { await props.api.refresh() } catch {} finally { checking.current = false }
      }
    }, 3000)
    return () => window.clearInterval(timer)
  }, [state.waiting, state.authorized, state.uiToken])

  useEffect(() => {
    if (!state.browserCode || state.authorized || busy) return
    return startPanelRefresh({document, interval: 3000, refresh: async () => {
      await props.api.call("resident_browser_login", {op: "status", uiToken: state.uiToken})
      await props.api.refresh()
    }})
  }, [state.browserCode, state.authorized, state.uiToken, props.api.refresh, busy])

  useEffect(() => {
    if (!controlling || busy) return
    return startPanelRefresh({refresh: props.api.refresh, document, interval: 6000})
  }, [props.api.refresh, controlling, busy])

  return <Page title="连接千灯纪居民"><Stack gap={14}>
    <Card title={state.connected ? `${state.role} → ${state.resident}` : "使用千灯纪女仆或 Numen"}><Stack gap={10}>
      <Text>授权后选择已有的车万女仆或 Numen，绑定完成后点「开始桌面控制」。居民由千灯纪执行游戏动作，使用你选的 N.E.K.O. 角色处理回合。</Text>
      <Inline>
        <FileDownload href={`${props.host?.origin || ""}/ui/plugins/minecraft_autonomous?tab=panel&surface=main`}
          label="返回账号与玩法选择" openExternal />
        <FileDownload href="https://mc.kangqiang.site/#live" label="官网观战 · 女神之眼" openExternal />
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
    {state.connected && <Card title="Simple Voice Chat"><Stack gap={8}>
      <Text>在装有 Simple Voice Chat 的 Java 客户端开启麦克风和收听，走到居民附近说话。语音由游戏服务器转写和播报。</Text>
      {phase === "running" && voice && <>
        <Text>{voice.transcriptReceived ? "本次控制已收到游戏语音转写。" : "等待游戏语音转写。"}</Text>
        <Text>{offeredVoiceModes.length ? `本轮可用回复方式 · ${offeredVoiceModes.join("、")}` : "当前无可用的游戏回复方式。"}</Text>
        <Text>{voice.receipt ? `最近语音回执 · ${voiceStates[voice.receipt.state] || "待核实"}` : "尚无服务端语音回执。"}</Text>
        {voice.receipt && <>
          {typeof voice.receipt.captionRecipients === "number" && <Text>文字提示接收人数 · {voice.receipt.captionRecipients}</Text>}
          <Text>实际收听待听众确认。</Text>
        </>}
      </>}
    </Stack></Card>}
    {!controlling && <>
    <Card title="角色身体与换身"><Stack>
      {state.bodyView?.available !== false && <Button disabled={busy || !state.uiToken}
        onClick={() => call("open_resident_website", {page:"bodies"})}>在官网管理身体</Button>}
      {state.bodyReadable && <Stack>
        <Button disabled={busy} onClick={() => call("read_character_body", {op:"list"})}>查看身体状态</Button>
        {character ? <Stack>
          <Field label="我的角色"><Select value={character.characterId}
            options={bodyRows.map(row => ({value:row.characterId,label:row.name}))}
            onChange={value => { setCharacterId(value); setReceiptId("") }} /></Field>
          <Text>{bodyNames[character.activeKind || ""] || "身体待核实"} · {statuses[character.status] || "待核实"}</Text>
          {character.generation !== null && <Text>控制版本 · {character.generation}</Text>}
          <Text>{character.targetKinds.length ? "可换至 " + character.targetKinds.map(kind => bodyNames[kind]).join("、") : "当前没有可切换的身体。"}</Text>
          {character.autonomous && <Text>服务端已允许此角色自主申请换身。</Text>}
          <Field label="换身请求编号"><Input value={receiptId} placeholder={character.pendingRequestId || "填写原请求编号"} onChange={setReceiptId} /></Field>
          <Button disabled={busy || !original} onClick={() => call("read_character_body", {
            op:"receipt",characterId:character.characterId,requestId:original
          })}>查看原回执</Button>
          {receipt && <Stack gap={5}>
            <Text>{statuses[receipt.status] || "待核实"} · {bodyNames[receipt.targetKind]} · 控制版本 {receipt.generation}</Text>
            {receipt.reason && receiptReasons[receipt.reason] && <Text>{receiptReasons[receipt.reason]}</Text>}
          </Stack>}
        </Stack> : state.bodyView && <Text>{state.bodyView.available ? "当前账号还没有可管理身体的角色。" : "服务器尚未开放角色换身。"}</Text>}
      </Stack>}
    </Stack></Card>
    {canShowDevice && <Card title="桌面接力设备"><Stack>
      <Text>在上方选择本人角色，再到千灯纪官网批准该角色的桌面设备。官网可撤销设备权限。</Text>
      {state.bodyDevice?.state === "paired" ? <Stack>
          <StatusBadge label="官网已批准这台设备" tone="success" />
          <Text>回到账号与玩法主面板，开启桌面接力再启动游玩。</Text>
        </Stack> :
        state.bodyDevice?.state === "pending" && state.bodyDevice.pairId ?
          <Stack gap={8}>
            <StatusBadge label="等待官网批准" tone="default" />
            <Field label="一次性配对编号"><Text>{state.bodyDevice.pairId}</Text></Field>
            {state.bodyDevice.expiresAt && <Text>到期时间 · {new Date(state.bodyDevice.expiresAt).toLocaleTimeString()}</Text>}
            <Inline>
              <Button disabled={busy || !state.uiToken} onClick={() => call("pair_body_device", {op:"open"})}>打开官网批准</Button>
              <Button disabled={busy || !state.uiToken} onClick={() => call("pair_body_device", {op:"check"})}>核对批准结果</Button>
              <Button disabled={busy || !state.uiToken} onClick={() => call("pair_body_device", {op:"cancel"})}>取消本次配对</Button>
            </Inline>
          </Stack> :
          <Button disabled={busy || !state.uiToken || !character} onClick={() =>
            call("pair_body_device", {op:"start", characterId:character?.characterId})}>生成配对编号</Button>}
      {state.bodyDevice?.state === "expired" && <Text>配对编号已过期，可以重新生成。</Text>}
    </Stack></Card>}
    <Card title="本机 N.E.K.O. 角色"><Stack>
      <Text>已有旧版居民插件或酒狐控制同一身体时，先停止旧连接。随后在这里选回原居民。</Text>
      <Field required label="由哪个角色在游戏里行动">{roles.length ?
        <Select disabled={controlling || busy} value={localRole} options={roles.map(value => ({ value, label: value }))} onChange={setRole} /> :
        <Input disabled={controlling || busy} value={localRole} onChange={setRole} placeholder="本机角色名" />}
      </Field>
      <Inline>
        <Button disabled={!state.uiToken || busy} onClick={() => call("open_resident_website", { page: "characters" })}>打开 N.E.K.O. 角色管理</Button>
        <Button disabled={busy} onClick={() => props.api.refresh()}>刷新本机角色</Button>
      </Inline>
    </Stack></Card>
    {!state.authorized ? <Card title="官网授权"><Stack>
      <Button tone="primary" disabled={busy || controlling || !state.uiToken}
        onClick={() => call("resident_browser_login", {op: "start"})}>
        {state.browserCode ? "重新打开官网确认页" : "在浏览器登录并授权"}
      </Button>
      {state.browserCode && <Text>请在官网确认六位数字 {state.browserCode}。授权完成后，这里会显示你的居民。</Text>}
      <Button disabled={busy || controlling} onClick={() => setManual(!manual)}>{manual ? "收起授权码入口" : "改用已有官网授权码"}</Button>
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
      {mode === "connect" ? (residents.length ? <Stack>
        <Field label="我的角色"><Select disabled={busy || controlling} value={selected?.id || ""} onChange={setId} options={residents.map(row => ({
          value: row.id, label: row.name + " · " + label(row.bodyKind) + (row.state === "preparing" ? "（准备中）" : "")
        }))} /></Field>
        <Button disabled={busy || controlling || !!state.waiting || !localRole || !selected || selected.state !== "available"}
          onClick={() => selected && call("manage_residents", {
            op: "connect", id: selected.id, characterId: selected.characterId, localRole
          })}>绑定这个角色</Button>
        {selected?.state === "preparing" && <Text>服务器正在准备该居民。准备结束后刷新角色列表。</Text>}
      </Stack> : <Text>这个账号还没有游戏角色，可以新建一个。</Text>) : (bodyKind ? <Stack>
        <Field label="身体"><Select value={bodyKind} onChange={setKind} options={bodies.map(value => ({ value, label: label(value) }))} /></Field>
        <Field required label="游戏角色名"><Input value={chosenName} onChange={setName} /></Field>
        <Field label="游戏中的角色设定（可选）"><Textarea value={persona} onChange={setPersona} /></Field>
        <Button disabled={busy || controlling || !!state.waiting || !localRole || !chosenName.trim()} onClick={() => call("manage_residents", {
          op: "create", localRole, bodyKind, name: chosenName.trim(), persona
        })}>创建并绑定</Button>
      </Stack> : <Text>服务器当前没有可用的新身体。</Text>)}
      {state.waiting ? <Text>正在准备 {state.waiting} 的游戏身体。准备好后会保存绑定，你可以再手动开始。</Text> : null}
      <Button disabled={busy || controlling} onClick={() => call("manage_residents", { op: "list" })}>刷新游戏角色</Button>
    </Stack></Card>}
    </>}
  </Stack></Page>
}
