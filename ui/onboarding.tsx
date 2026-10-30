import {Button, FileDownload, Accordion, Field, Input} from '@neko/plugin-ui'
import {accountView} from './account-state.js'

const css = `
.mc-app { --mc-accent:#207454; --mc-soft:rgba(43,133,96,.09); --mc-muted:var(--muted,#667085); max-width:1080px; margin:0 auto; }
.mc-app h2,.mc-app h3,.mc-app p { margin-top:0; }
.mc-app .neko-page-title { font-size:26px; letter-spacing:-.6px; }
.mc-app .neko-page-subtitle { font-size:13px; }
.mc-app .neko-card { border-radius:16px; }
.mc-app .neko-button { min-height:40px; font-size:13px; border-radius:9px; box-shadow:none; }
.mc-app .neko-button:hover { transform:none; }
.mc-app .mc-primary { background:var(--mc-accent); border-color:var(--mc-accent); color:#fff; }
.mc-app .mc-secondary { color:var(--text); background:var(--surface); border-color:var(--border); }
.mc-app .mc-hero { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:18px; padding:4px 0 12px; }
.mc-app .mc-hero-copy { display:flex; align-items:center; gap:15px; }
.mc-app .mc-world-mark { display:grid; place-items:center; width:48px; height:48px; flex:0 0 48px; border-radius:13px; background:var(--mc-soft); color:var(--mc-accent); font-size:29px; }
.mc-app .mc-eyebrow { color:var(--mc-muted); font-size:11px; font-weight:650; letter-spacing:1.6px; }
.mc-app .mc-hero h1 { font-size:24px; letter-spacing:-.6px; line-height:1.35; margin:3px 0 5px; }
.mc-app .mc-sub { color:var(--mc-muted); font-size:13px; line-height:1.7; margin:0; }
.mc-app .mc-progress { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:6px; }
.mc-app .mc-progress-item { display:flex; align-items:center; gap:10px; padding:13px 14px; border:1px solid var(--border); border-radius:12px; background:var(--surface); min-width:0; }
.mc-app .mc-progress-number { display:grid; place-items:center; width:28px; height:28px; border-radius:50%; color:var(--mc-muted); background:var(--bg); font-size:12px; flex:0 0 28px; }
.mc-app .mc-progress-item[data-done=true] .mc-progress-number { background:var(--mc-soft); color:var(--mc-accent); }
.mc-app .mc-progress-item strong { display:block; font-size:13px; font-weight:650; }
.mc-app .mc-progress-item small { display:block; color:var(--mc-muted); font-size:11px; margin-top:2px; }
.mc-app .mc-world-picker { display:flex; flex-wrap:wrap; gap:8px; padding:3px 0 10px; }
.mc-app .mc-world-picker .neko-button { background:transparent; border:1px solid var(--border); color:var(--mc-muted); }
.mc-app .mc-world-picker .mc-selected { background:var(--mc-soft); border-color:var(--mc-accent); color:var(--mc-accent); }
.mc-app .mc-stage { padding:22px 0; border-bottom:1px solid var(--border); }
.mc-app .mc-stage:first-child { padding-top:7px; }
.mc-app .mc-stage:last-child { border-bottom:0; }
.mc-app .mc-section-head { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.mc-app .mc-section-head h2 { font-size:15px; font-weight:650; margin:0; }
.mc-app .mc-section-index { color:var(--mc-accent); font-size:12px; font-weight:650; }
.mc-app .mc-section-body { margin-left:26px; display:grid; gap:12px; }
.mc-app .mc-account { display:grid; gap:17px; border:1px solid var(--border); border-radius:12px; background:var(--surface-strong); padding:20px; }
.mc-app .mc-account-header { display:flex; justify-content:space-between; align-items:flex-start; gap:14px; }
.mc-app .mc-account h3 { font-size:16px; line-height:1.55; font-weight:650; margin:0 0 5px; }
.mc-app .mc-label { flex:0 0 auto; border:1px solid var(--border); border-radius:6px; color:var(--mc-muted); padding:3px 7px; font-size:11px; }
.mc-app .mc-account[data-kind=ready] .mc-label { color:var(--mc-accent); background:var(--mc-soft); border-color:transparent; }
.mc-app .mc-role { display:flex; align-items:center; gap:10px; font-size:12px; color:var(--mc-muted); }
.mc-app .mc-role code { color:var(--text); font-size:12px; overflow-wrap:anywhere; }
.mc-app .mc-actions { display:flex; flex-wrap:wrap; align-items:center; gap:9px; }
.mc-app .mc-account .neko-accordion { background:transparent; border-radius:8px; }
.mc-app .mc-account .neko-accordion-trigger { font-size:12px; color:var(--mc-muted); }
.mc-app .mc-account .neko-text { font-size:12px; }
.mc-app .mc-account-note { border-left:2px solid var(--border); padding-left:12px; font-size:12px; color:var(--mc-muted); line-height:1.7; }
.mc-app .mc-launch { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:14px; padding:20px 0 4px; }
.mc-app .mc-launch .mc-primary { min-height:44px; padding:10px 23px; }
.mc-app .mc-compact { font-size:12px; color:var(--mc-muted); line-height:1.7; }
.mc-app .mc-connection-card > .neko-card-body { padding:18px 22px 22px; gap:0; }
.mc-app .mc-connection-card > .neko-card-header { display:none; }
.mc-app .mc-model-line { font-size:13px; color:var(--mc-muted); margin:0; line-height:1.7; }
@media(prefers-color-scheme:dark) { .mc-app { --mc-accent:#79ceab; --mc-soft:rgba(91,184,143,.11); } .mc-app .mc-primary { background:#367f61; border-color:#439171; color:#fff; } }
@media(max-width:620px) { .mc-app { padding:14px; } .mc-app .mc-progress { gap:6px; } .mc-app .mc-progress-item { padding:10px 8px; gap:7px; } .mc-app .mc-progress-number { width:22px; height:22px; flex-basis:22px; } .mc-app .mc-progress-item small { font-size:10px; } .mc-app .mc-account { padding:15px; } .mc-app .mc-section-body { margin-left:0; } .mc-app .mc-account-header { flex-wrap:wrap-reverse; gap:9px; } .mc-app .mc-connection-card > .neko-card-body { padding:15px; } .mc-app .mc-hero h1 { font-size:21px; } .mc-app .mc-progress-item strong { font-size:12px; } }
@media(max-width:380px) { .mc-app .mc-progress-number { display:none; } }
@media(prefers-reduced-motion:reduce) { .mc-app * { animation:none!important; transition:none!important; } }
`

// Keep the hosted entry's only export before JSX helper bodies. Older shipped
// renderers do not consistently link declarations following JSX closing tags.
export default function Onboarding(props:any) {
  if(props.kind==='styles')return <style>{css}</style>
  if(props.kind==='progress')return <SetupProgress {...props} />
  return <AccountConnection {...props} />
}

function SetupProgress({accountReady,needsAccount,componentsReady}:any) {
  const items=[['账号',accountReady?'已准备':needsAccount?'等待接入':'连接服务器',accountReady],
    ['游戏环境',componentsReady?'已准备':'首次准备一次',componentsReady],['模型','在 Neko 中选择',false]]
  return <nav className="mc-progress" aria-label="游玩准备步骤">{items.map(([title,hint,done],index)=><div className="mc-progress-item" data-done={String(done)} key={String(title)}>
    <span className="mc-progress-number" aria-hidden="true">{done?'✓':index+1}</span><div><strong>{title}</strong><small>{hint}</small></div>
  </div>)}</nav>
}

function AccountConnection({account,configured,original,username,busy,disabled,agentName,onName,onConnect,onPause,legacy,legacyRevision,onLegacy}:any) {
  const view=accountView(account,{configured,original})
  const authorizing=account.active&&account.phase==='authorization_required'&&account.verification_url
  return <div className="mc-account" data-kind={view.kind}>
    <div className="mc-account-header"><div><h3>{view.title}</h3><p className="mc-sub">{view.detail}</p></div><span className="mc-label">{view.badge}</span></div>
    {(username||account.username)&&<div className="mc-role"><span>游戏角色</span><code>{configured?username:account.username||username}</code></div>}
    <div className="mc-actions">
      {authorizing?<FileDownload href={account.verification_url} label="前往官网授权" openExternal className="mc-primary" />:
        view.action&&<Button className={view.kind==='unavailable'?'mc-secondary':'mc-primary'} disabled={busy||disabled||account.active} onClick={onConnect}>{view.action}</Button>}
      {account.active&&<Button className="mc-secondary" disabled={busy} onClick={onPause}>暂停查询</Button>}
      {!configured&&<Button className={view.kind==='unavailable'||original?'mc-primary':'mc-secondary'} onClick={onLegacy}>使用已有账号</Button>}
      {configured&&<FileDownload href="https://mc.kangqiang.site/join" label="在官网管理账号 ↗" openExternal className="mc-secondary" />}
    </div>
    {!account.selected&&!original&&!configured&&<Accordion open={false} title="自定义游戏昵称（可选）"><Field label="游戏昵称"><Input value={agentName} placeholder="留空自动生成，或输入 ag_ 开头的昵称" onChange={onName} /></Field></Accordion>}
    {view.kind==='attention'&&<div className="mc-account-note" role="status">{account.message||view.detail}</div>}
    <Accordion key={`${original}-${legacyRevision}`} open={legacyRevision>0||original} title="已有账号与邀请接入">{legacy}</Accordion>
  </div>
}
