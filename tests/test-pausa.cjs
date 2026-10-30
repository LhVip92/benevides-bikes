const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const code=readFileSync(require('node:path').join(__dirname,'../integracoes/kapso/pausar-atendimento-humano.js'),'utf8');
const conv='10000000-0000-4000-8000-000000000001';
const runId='20000000-0000-4000-8000-000000000002';
const flow='ac0feaf6-f912-4e5b-846e-ceb4b2721a07';
const base=()=>({execution_context:{system:{event:{type:'whatsapp.message.sent',message:{timestamp:String(Math.floor(Date.now()/1000)),kapso:{origin:'business_app',direction:'outbound',phone_number_id:'629422250252844'}},conversation:{id:conv}}}}});
const run={id:runId,workflow:{id:flow},whatsapp_conversation_id:conv,status:'waiting',started_at:new Date(Date.now()-60000).toISOString()};
let passed=0;
async function check(name,mutate,expected,apiMode='normal',env={KAPSO_API_KEY:'test-not-real'}){
 const calls=[]; const body=base();mutate(body);
 const fetch=async(url,opts)=>{
  calls.push({url,opts}); assert(url.startsWith('https://api.kapso.ai/platform/v1/'));
  assert.equal(opts.headers['X-API-Key'],'test-not-real');
  if(apiMode==='failure')return new Response('{}',{status:401});
  if(url.includes('/flow_executions?')){
   const rows=url.includes('status=waiting')?[run,{...run,id:'30000000-0000-4000-8000-000000000003',workflow:{id:'other-flow'}}]:[];
   return Response.json({data:rows,paging:{next:null}});
  }
  if(opts.method==='PATCH'){
   assert.equal(url.split('/').at(-1),runId);
   assert.deepEqual(JSON.parse(opts.body),{workflow_execution:{status:'handoff'}});
   return Response.json({data:{...run,status:'handoff'}});
  }
  return Response.json({data:apiMode==='already-handoff'?{...run,status:'handoff'}:run});
 };
 const sandbox={Request,Response,URLSearchParams,AbortSignal,console:{error(){}},fetch};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);
 const res=await sandbox.handler(new Request('https://local.test',{method:'POST',body:JSON.stringify(body)}),env);
 const data=await res.json();
 if(expected==='error'){assert.equal(res.status,500)}
 else{assert.equal(res.status,200);assert.equal(data.vars.pausa_humano.status,expected)}
 if(expected==='pausado')assert.equal(calls.filter(x=>x.opts.method==='PATCH').length,1);
 else assert.equal(calls.filter(x=>x.opts.method==='PATCH').length,0);
 if(['ignorado','simulacao'].includes(expected))assert.equal(calls.length,0);
 passed++;process.stdout.write(name+' OK\n');
}
(async()=>{
 await check('Manual app pauses only target workflow',()=>{},'pausado');
 await check('Bot response is ignored',b=>b.execution_context.system.event.message.kapso.origin='cloud_api','ignorado');
 await check('Imported history is ignored',b=>b.execution_context.system.event.message.kapso.origin='history_sync','ignorado');
 await check('Other phone ignored',b=>b.execution_context.system.event.message.kapso.phone_number_id='other','ignorado');
 await check('Incoming message ignored',b=>b.execution_context.system.event.type='whatsapp.message.received','ignorado');
 await check('Test mode never mutates real chats',b=>b.execution_context.system.test_mode=true,'simulacao');
 await check('Old manual event ignored',b=>b.execution_context.system.event.message.timestamp='1700000000','ignorado');
 await check('Already paused is not resumed',()=>{},'sem_execucao_ativa','already-handoff');
 await check('Missing secret reports error',()=>{},'error','normal',{});
 await check('API failure reports error',()=>{},'error','failure');
 console.log(passed+' checks passed; no real API calls or customer messages');
})().catch(e=>{console.error(e);process.exit(1)});
