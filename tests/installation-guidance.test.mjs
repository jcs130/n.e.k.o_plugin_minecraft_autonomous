import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import * as guidance from '../ui/installation-guidance.js';
const {installationGuidance} = guidance;
test('local metadata stays separate from external renderer acceptance', () => {
  const value = {backend:'version_matches_not_integrity_verified',viewer:'text_only'};
  for (const [external,url] of [[true,''],[false,'http://example.test/view']]) {
    const result = installationGuidance(value, external, url);
    assert.match(result.backend, /版本匹配.*仍须完整性校验/);
    assert.match(result.localResources, /未配置本地/);
    assert.match(result.externalView, /外部执行器.*实际观战页面核验/);
  }
  assert.match(installationGuidance(value,false,'').externalView, /文字模式/);
  assert.match(installationGuidance({viewer:'metadata_matches_ready_to_attempt_rendering'},false,'').localResources, /实际画面仍待核验/);
  for (const code of ['private-untrusted-code','constructor','__proto__',undefined]) {
    const result = installationGuidance({backend:code,viewer:code},false,'');
    assert.equal(result.backend,'状态暂不可用，请检查配置与安装说明');
    assert.equal(result.localResources,result.backend);
  }
  const panel = readFileSync(new URL('../ui/panel.tsx',import.meta.url),'utf8');
  assert.match(panel, /installationGuidance\(state.installation, external, state.viewer_url\)/);
  assert.match(panel, /本地渲染资源：\{installation.localResources\}/);
  assert.doesNotMatch(panel, /\{state.installation\?\.(backend|viewer)\b/);
});

test('prepared runtime guidance keeps one visible preparation step and custom modes', () => {
  for (const prepared_runtime of ['missing','incompatible']) {
    assert.match(installationGuidance({prepared_runtime},false,'').preparedRuntime, /准备游戏组件/);
  }
  assert.match(installationGuidance({prepared_runtime:'prepared'},false,'').preparedRuntime, /显式启动.*完整性/);
  assert.match(installationGuidance({prepared_runtime:'custom'},false,'').preparedRuntime, /自定义.*不会混入/);
  assert.match(installationGuidance({prepared_runtime:'external'},true,'').preparedRuntime, /独立执行器/);
});

test('preparation progress is bounded and actionable without paths or command lines',()=>{
  assert.equal(typeof guidance.preparationView,'function');
  const view=guidance.preparationView({setup:{available:true,active:true,phase:'downloading',downloaded_bytes:512,total_bytes:1024}});
  assert.equal(view.progress,50);assert.match(view.label,/下载/);assert.equal(view.active,true);
  assert.equal(guidance.preparationView({setup:{phase:'extracting',files:20,total_files:10}}).progress,100);
  assert.equal(guidance.preparationView({setup:{phase:'extracting',files:-1,total_files:10}}).progress,null);
  assert.equal(guidance.preparationView({setup:{phase:'verifying'}}).progress,null);
  for(const phase of ['constructor','__proto__','untrusted'])assert.match(guidance.preparationView({setup:{phase}}).label,/准备游戏组件/);
  assert.match(guidance.preparationView({setup:{phase:'ready'}}).label,/已就绪/);
  assert.match(guidance.preparationView({setup:{phase:'failed'}}).button,/重试/);
});

test('an explicit old prepared-runtime selection preserves account, model and data choices', () => {
  assert.equal(typeof guidance.preparedRuntimeSelection, 'function');
  const raw = {server:{username:'my-role'},planner:{model:'my-model'},runtime:{mode:'embedded',bundle_root:'old-runtime',bundle_manifest_sha256:'old-hash',data_directory:'my-data'},
    backend:{node:'old-node',directory:'old-backend'},viewer:{renderer_directory:'old-renderer',catalog_file:'old-catalog',bundled_appearance_catalog_file:'old-appearance',auto_open:false}};
  const original = structuredClone(raw);
  const patch = guidance.preparedRuntimeSelection(raw,{prepared_runtime:'incompatible'});
  assert.deepEqual(Object.keys(patch).sort(),['backend','runtime','viewer']);
  const updated = {...raw,...Object.fromEntries(Object.entries(patch).map(([key,value])=>[key,{...raw[key],...value}]))};
  assert.deepEqual(raw,original);
  assert.deepEqual(updated.server,raw.server);assert.deepEqual(updated.planner,raw.planner);
  assert.equal(updated.runtime.data_directory,'my-data');assert.equal(updated.runtime.mode,'embedded');
  assert.equal(updated.viewer.auto_open,false);assert.equal(updated.backend.directory,'');
  assert.equal(updated.runtime.bundle_root,'');assert.equal(updated.runtime.bundle_manifest_sha256,'');
  for(const settings of [{...raw,runtime:{...raw.runtime,mode:'external'}},{...raw,runtime:{mode:'embedded'}},{...raw,viewer:{url:'https://my-view.example'}}])
    assert.equal(guidance.preparedRuntimeSelection(settings,{prepared_runtime:'incompatible'}),null);
  assert.equal(guidance.preparedRuntimeSelection(raw,{prepared_runtime:'prepared'}),null);
  assert.equal(guidance.preparedRuntimeSelection(raw,{prepared_runtime:'custom'}),null);
});
