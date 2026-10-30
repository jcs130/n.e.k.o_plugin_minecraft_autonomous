// Presentation follows authority: an application is never a configured account.
export function accountView(account = {}, {configured = false, original = false} = {}) {
  if (configured) return {kind:'ready',badge:'已就绪',title:'游戏账号已准备好',
    detail:'以后直接开始，猫娘会自动完成游戏登录。',action:''};
  if (original) return {kind:'existing',badge:'已有账号',title:'继续使用原来的游戏角色',
    detail:'核对已保存身份，或填写原昵称和游戏密码。',action:''};
  const phase = account.phase;
  if (phase === 'provider_not_configured') return {kind:'unavailable',badge:'尚未开放',title:'账号关联暂未开放',
    detail:'当前可使用已有的千灯纪游戏账号。新账号关联需等待站点开放。',action:'检查是否已开放'};
  if (phase === 'authorization_required') return {kind:'authorize',badge:'等待你确认',title:'在官网确认这次账号关联',
    detail:'用猫娘计划账号登录，核对角色名并允许接入。确认后这里会继续准备。',action:'继续关联'};
  if (phase === 'expired') return {kind:'attention',badge:'需要确认',title:'这次授权已过期',
    detail:account.renewable?'重新授权即可，仍然使用这个角色。':'先核对原申请结果，避免重复创建角色。',action:account.renewable?'重新授权':'核对原申请'};
  if (['failed','unknown','neko_link_result_unconfirmed','neko_link_configuration_unconfirmed','neko_link_response_mismatch'].includes(phase))
    return {kind:'attention',badge:'需要核对',title:'原申请还需要确认',
      detail:'角色和申请已保留。继续核对原结果，不会换名或重复建号。',action:'继续核对'};
  if (account.active) return {kind:'working',badge:'正在准备',title:phase==='checking'?'正在检查账号接入':'正在准备游戏账号',
    detail:'保留同一份申请，准备完成后会在这里通知你。',action:'正在准备…'};
  if (phase === 'paused') return {kind:'idle',badge:'已暂停',title:'随时继续这次关联',
    detail:'角色与申请都已保留，继续后查询原来的结果。',action:'继续关联'};
  return {kind:'idle',badge:'首次连接',title:'用猫娘计划账号进入千灯纪',
    detail:'在官网确认一次，插件会准备游戏角色和自动登录。',action:account.selected?'继续关联':'使用猫娘计划账号登录'};
}
