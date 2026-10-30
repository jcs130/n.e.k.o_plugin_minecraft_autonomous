import assert from 'node:assert/strict';
import test from 'node:test';
import {accountView} from '../ui/account-state.js';

test('a server-ready request is not a privately configured game login',()=>{
  for(const phase of ['ready','pending','approved','unknown'])assert.notEqual(accountView({phase}).kind,'ready');
  assert.equal(accountView({phase:'ready'},{configured:true}).kind,'ready');
  assert.equal(accountView({phase:'idle'},{original:true}).action,'');
});

test('closed registration offers an honest waiting state and preserves an existing-account route',()=>{
  const view=accountView({phase:'provider_not_configured',username:'ag_existing'});
  assert.equal(view.kind,'unavailable');assert.match(view.title,/暂未开放/);
  assert.doesNotMatch(view.action,/登录|已完成|开始游玩/);
  assert.match(view.detail,/已有.*账号/);
});

test('recovery offers renewal only when the original request allows it',()=>{
  assert.match(accountView({phase:'expired',renewable:true}).action,/重新授权/);
  assert.doesNotMatch(accountView({phase:'expired',renewable:false}).action,/重新授权|创建/);
  assert.doesNotMatch(accountView({phase:'unknown'}).action,/创建|重试建号/);
  assert.match(accountView({phase:'paused',selected:true}).detail,/保留/);
});
