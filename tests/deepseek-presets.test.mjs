import assert from 'node:assert/strict';
import test from 'node:test';
import {deepseekPreset} from '../ui/deepseek-presets.js';

test('adaptive mode keeps one route and uses native profile signals for thinking changes',()=>{
  const original={server:{username:'Alice'},autonomy:{context_tokens:65536,model_timeout_seconds:180},
    planner:{provider:'openai-compatible',api_key_env:'LOCAL_ONLY',tool_schema_profile:'llamacpp',
      context_counter:{type:'local-counter'},parameters:{enable_thinking:true}}};
  const next=deepseekPreset(original,'adaptive');
  assert.equal(next.planner.model,'deepseek-flash');
  assert.equal(next.planner.api_key_env,'DEEPSEEK_API_KEY');
  assert.equal(next.planner.tool_schema_profile,'default');
  assert.equal(next.planner.output_parameter,'max_tokens');
  assert.equal(next.planner.reasoning_history,'all');
  assert.deepEqual(next.planner.context_counter,{});
  assert.equal(next.decision_policy.enabled,true);
  assert.deepEqual(next.decision_policy.routine_parameters,{thinking:{type:'disabled'},reasoning_effort:'none'});
  assert.deepEqual(next.decision_policy.complex_parameters,{thinking:{type:'enabled'},reasoning_effort:'low'});
  assert.equal(next.autonomy.model_timeout_seconds,180);
  assert.equal(next.autonomy.context_tokens,262144);
  assert.equal(next.server.username,'Alice');
  assert.equal(original.planner.provider,'openai-compatible');
});

test('fixed modes and a DeepSeek credential reference survive normal edits',()=>{
  for(const mode of ['off','low','high','max']) {
    const next=deepseekPreset({planner:{provider:'deepseek',api_key_env:'MY_DEEPSEEK_KEY'}},mode);
    assert.equal(next.planner.api_key_env,'MY_DEEPSEEK_KEY');
    assert.equal(next.decision_policy.enabled,false);
    assert.equal(next.planner.parameters.reasoning_effort,mode==='off'?'none':mode);
    assert.equal(next.planner.parameters.thinking.type,mode==='off'?'disabled':'enabled');
    assert.ok(next.autonomy.max_output_tokens>=2048);
  }
  assert.throws(()=>deepseekPreset({},'unknown'));
});
