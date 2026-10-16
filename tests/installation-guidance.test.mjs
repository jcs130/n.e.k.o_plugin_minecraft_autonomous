import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {installationGuidance} from '../ui/installation-guidance.js';
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

test('prepared runtime guidance keeps one preparation step and custom modes', () => {
  for (const prepared_runtime of ['missing','incompatible']) {
    assert.match(installationGuidance({prepared_runtime},false,'').preparedRuntime, /prepare.cmd/);
  }
  assert.match(installationGuidance({prepared_runtime:'prepared'},false,'').preparedRuntime, /显式启动.*完整性/);
  assert.match(installationGuidance({prepared_runtime:'custom'},false,'').preparedRuntime, /自定义.*不会混入/);
  assert.match(installationGuidance({prepared_runtime:'external'},true,'').preparedRuntime, /独立执行器/);
});
