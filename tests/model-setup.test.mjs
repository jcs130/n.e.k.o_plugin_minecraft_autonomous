import test from 'node:test'
import assert from 'node:assert/strict'
import { modelProbeMessage } from '../ui/model-setup.js'

test('N.E.K.O. readiness labels report a text probe and its binding failures', () => {
  assert.equal(modelProbeMessage(true, null), '')
  assert.match(modelProbeMessage(true, {mode:'text', structured_probe_passed:true}), /上次模型测试通过/)
  assert.match(modelProbeMessage(true, {mode:'text', structured_probe_passed:false, model_status:{reason:'model_usage_not_bound'}}), /未绑定 decision/)
  assert.match(modelProbeMessage(true, {mode:'text', structured_probe_passed:false, model_status:{reason:'model_capability_mismatch'}}), /不支持工具调用/)
})

test('a catalog, vision probe or other route does not confirm decision readiness', () => {
  assert.equal(modelProbeMessage(true, {mode:'vision', structured_probe_passed:true}), '')
  assert.equal(modelProbeMessage(true, {tool_call_valid:true}), '')
  assert.equal(modelProbeMessage(false, {mode:'text', structured_probe_passed:true}), '')
  assert.equal(modelProbeMessage(false, {models:[{id:'fixture'}]}), '')
  assert.match(modelProbeMessage(false, {tool_call_valid:true}), /上次模型测试通过/)
  assert.match(modelProbeMessage(false, {tool_call_valid:false, model_status:{reason:'private details'}}), /未通过/)
  assert.doesNotMatch(modelProbeMessage(false, {tool_call_valid:false, model_status:{reason:'private details'}}), /private/)
})
