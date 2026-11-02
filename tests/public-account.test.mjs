import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {runAgentAccess} from '../assets/server-extensions/qiandengji/access/agent-register.mjs';

test('public joining saves one identity, sends no invite and never repeats uncertain activation',async()=>{
  const directory=await mkdtemp(path.join(os.tmpdir(),'neko-public-')),file=path.join(directory,'identity.json');
  const original=globalThis.fetch,requests=[],output=[];let registered=false,state='not_created',saved;
  globalThis.fetch=async(url,options)=>{
    saved=JSON.parse(await readFile(file,'utf8'));
    assert(saved.clientSecret&&saved.gamePassword&&saved.gameRequestId);
    assert(!url.includes('invite'));
    requests.push(url);
    const body=options.body&&JSON.parse(options.body);let value,status=200;
    if(url.endsWith('/sessions')){
      if(!registered){status=401;value={error:{reason:'CLIENT_NOT_FOUND'}};}
      else value={clientId:saved.clientId,username:saved.username,token:'qda_'+'t'.repeat(43)};
    }else if(url.endsWith('/public-register')){
      assert(!options.headers.Authorization);assert(!body.gamePassword);
      assert.equal(body.requestId,saved.clientId);registered=true;
      value={clientId:saved.clientId,username:saved.username,state:'registered'};
    }else if(url.endsWith('/activate')){state='unknown';throw Error('lost reply');}
    else value={state,username:saved.username,gameAccountCreated:state==='ready',game:{ready:true},gameAddress:'micro.kangqiang.site:25702',gameVersion:'1.21.1'};
    return {ok:status===200,status,json:async()=>value};
  };
  const args=['join-plugin','--portal','https://mc.kangqiang.site','--username','ag_Test','--identity-file',file];
  try{
    await assert.rejects(runAgentAccess(args,v=>output.push(v),{maxWaitMs:0}),/RESULT_UNKNOWN/);
    const first=JSON.parse(await readFile(file,'utf8'));
    assert.equal(first.joinActivationAttempted,true);
    await runAgentAccess(args,v=>output.push(v),{maxWaitMs:0});
    state='ready';await runAgentAccess(args,v=>output.push(v),{maxWaitMs:0});
    assert.equal(requests.filter(x=>x.endsWith('/public-register')).length,1);
    assert.equal(requests.filter(x=>x.endsWith('/activate')).length,1);
    assert.equal(JSON.parse(output.at(-1)).state,'ready');
    assert(!output.join('').includes(first.clientSecret));assert(!output.join('').includes(first.gamePassword));
  }finally{globalThis.fetch=original;await rm(directory,{recursive:true,force:true});}
});
