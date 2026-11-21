export function modelProbeMessage(usingHost, check) {
  const passed = usingHost && check?.mode === "text" ? check.structured_probe_passed : !usingHost ? check?.tool_call_valid : undefined
  if (passed === true) return "上次模型测试通过，可以返回工具调用。"
  if (passed !== false) return ""
  const reason = check.model_status?.reason || check.reason
  if (usingHost && reason === "model_usage_not_bound") return "上次测试时未绑定 decision，请选择一个支持工具调用的模型。"
  if (usingHost && reason === "model_capability_mismatch") return "上次测试时所绑定的模型不支持工具调用。"
  return "上次模型测试未通过，请核对模型、凭据和工具调用支持。"
}
