/** User-selected payload presets; this module never calls a model or changes live routes. */
export function deepseekPreset(draft, mode) {
  if (!['off','low','adaptive','high','max'].includes(mode)) throw new Error('invalid_deepseek_preset');
  const next=JSON.parse(JSON.stringify(draft));
  const thinking=effort=>({thinking:{type:effort==='none'?'disabled':'enabled'},reasoning_effort:effort});
  const maximum=mode==='off'?2048:mode==='high'?16384:mode==='max'?32768:8192;
  next.planner={...next.planner,route:'direct',provider:'deepseek',model:'deepseek-flash',
    protocol:'chat',base_url:'https://api.deepseek.com/v1',stream:true,output_parameter:'max_tokens',reasoning_history:'all',
    api_key_env:draft.planner?.provider==='deepseek'&&draft.planner.api_key_env?draft.planner.api_key_env:'DEEPSEEK_API_KEY',
    auth:{mode:'api_key',credential_id:'agent-mc'},tool_schema_profile:'default',context_counter:{},
    parameters:thinking(mode==='off'||mode==='adaptive'?'none':mode)};
  // Full native schemas need more bytes than local model tokens. Keep a bounded
  // conservative window instead of reusing a local tokenizer's smaller budget.
  next.autonomy={...next.autonomy,max_output_tokens:maximum,
    context_tokens:Math.min(1048576,Math.max(262144,next.autonomy?.context_tokens||0))};
  next.decision_policy={enabled:mode==='adaptive',routine_output_tokens:Math.min(2048,maximum),
    complex_output_tokens:maximum,routine_parameters:mode==='adaptive'?thinking('none'):{},
    complex_parameters:mode==='adaptive'?thinking('low'):{}};
  return next;
}
