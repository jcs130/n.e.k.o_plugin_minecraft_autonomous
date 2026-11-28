import assert from 'node:assert/strict';
import test from 'node:test';
import {applyConnectionPreset, connectionKind, javaAddress, parseJavaAddress} from '../ui/connection-presets.js';

test('Qiandeng preset only returns a new draft and keeps credentials on their own connection and preserves other settings', () => {
  const original = {server:{host:'localhost',port:25565,auth:'microsoft',username:'my-account'},operator:{port:0},autonomy:{enabled:false}};
  const before = structuredClone(original), draft = applyConnectionPreset(original, 'qiandeng');
  assert.deepEqual(original, before);
  assert.deepEqual(draft.server, {connection_type:'custom',host:'micro.kangqiang.site',port:25702,auth:'offline',version:'1.21.1',username:'',login_config_file:''});
  assert.deepEqual(draft.autonomy, {enabled:false});
  assert.deepEqual(draft.operator, {port:0});
  assert.throws(() => applyConnectionPreset(original, 'unknown'));
});

test('blank account stays blank and auth stays explicit', () => {
  const original = {server:{username:'',auth:'offline'}};
  const draft = applyConnectionPreset(original, 'qiandeng');
  assert.equal(draft.server.username, '');
  assert.equal(draft.server.auth, 'offline');
  assert.deepEqual(original, {server:{username:'',auth:'offline'}});
});


test('keeps the port of an already open LAN world and drops a previous endpoint login file', () => {
  const local = {server:{host:'127.0.0.1',port:52178,auth:'offline',username:'Neko'}};
  assert.deepEqual(applyConnectionPreset(local, 'vanilla'), local);
  const commercial = {server:{host:'micro.kangqiang.site',port:25702,login_config_file:'login.json'}};
  const next = applyConnectionPreset(commercial, 'vanilla');
  assert.equal(next.server.port, 25565);
  assert.equal(next.server.login_config_file, '');
  assert.equal(commercial.server.login_config_file, 'login.json');
  assert.equal(applyConnectionPreset(local, 'custom').server.host, '');
});

test('accepts an explicit Java join port and formats only plain host addresses', () => {
  assert.equal(javaAddress('127.0.0.1', 52178), '127.0.0.1:52178');
  assert.equal(javaAddress('::1', 25565), '[::1]:25565');
  assert.equal(javaAddress('[2001:db8::1]', 25565), '[2001:db8::1]:25565');
  for (const port of [0, 65536, NaN, 1.25, '25565']) assert.equal(javaAddress('localhost', port), '');
  for (const host of ['', 'https://host', 'me@host', 'hello world', 'host:25565']) assert.equal(javaAddress(host, 25565), '');
  assert.equal(connectionKind({host:'MICRO.KANGQIANG.SITE', port:25702}), 'qiandeng');
  assert.equal(connectionKind({host:'192.168.1.5', port:52178}), 'custom');
});


test('accepts pasted Java addresses with a default port or explicit port', () => {
  assert.deepEqual(parseJavaAddress(' play.example.org '), {host:'play.example.org',port:25565});
  assert.deepEqual(parseJavaAddress('play.example.org:25577'), {host:'play.example.org',port:25577});
  assert.deepEqual(parseJavaAddress('[::1]:25577'), {host:'::1',port:25577});
  for (const invalid of ['https://play.example.org', 'name@host', 'host:65536', 'host:0', 'host:', 'host:1.2', '[::1', 'host/path'])
    assert.equal(parseJavaAddress(invalid), null);
  assert.equal(connectionKind({host:'127.0.0.1',port:25577,connection_type:'custom'}), 'custom');
  assert.equal(connectionKind({host:'micro.kangqiang.site.',port:25702,connection_type:'custom'}), 'qiandeng');
});
