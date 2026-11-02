// Executes only our explicitly selected original fixture and original rebuild.
// HTTP access is constrained to a server created by this script on loopback.
import {createServer} from 'node:http';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {dirname, resolve, join} from 'node:path';
import assert from 'node:assert/strict';
import {createSearch} from './rebuild.mjs';
const here = dirname(fileURLToPath(import.meta.url));
const original = join(here, 'original/chunks/search.js');
const originalMain = join(here, 'original/main.js');
const sha = b => createHash('sha256').update(b).digest('hex');
const originalBytes = await readFile(original);
const requests = [];
const notes = [{id:1,title:'周报：本周交付',text:'完成中文部署教程'},
  {id:2,title:'周报：下周计划',text:'补齐 Windows 验证'},
  {id:3,title:'读书笔记',text:'示例数据由 RepoGo 原创，不含真实账户资料'}];
let mode = 'normal';
const server = createServer(async (req,res) => {
  let raw = ''; for await (const chunk of req) raw += chunk;
  requests.push({path:req.url,method:req.method,contentType:req.headers['content-type'],body:JSON.parse(raw)});
  res.setHeader('Content-Type','application/json');
  if (mode === '503') { res.statusCode=503;res.end(JSON.stringify({error:'demo maintenance'}));return; }
  if (mode === 'bad-json') {res.end('not JSON');return;}
  const {query} = JSON.parse(raw);
  const items=notes.filter(n=>(n.title+' '+n.text).includes(String(query)));
  res.end(JSON.stringify({items,total:items.length}));
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`;
const nativeFetch=globalThis.fetch;
globalThis.fetch=(url,options)=> {
  const target=new URL(url,origin);
  if(target.origin!==origin) throw new Error('Non-loopback target refused');
  return nativeFetch(target,options);
};
const {findNotes}=await import(pathToFileURL(originalMain));
const rebuilt=createSearch(origin,globalThis.fetch);
const result=[];
const observe=async fn=>{try{return {state:'resolved',value:await fn()}}catch(e){return {state:'rejected',error:e.name}}};
try {
  for(const c of [{name:'中文检索',query:'周报',mode:'normal'},
    {name:'引号与换行原样传递',query:'"周报"\n',mode:'normal'},
    {name:'HTTP503仍读取JSON',query:'周报',mode:'503'},
    {name:'无效JSON保留解析错误',query:'周报',mode:'bad-json'}]) {
    mode=c.mode;const start=requests.length;
    const left=await observe(()=>findNotes(c.query));
    const right=await observe(()=>rebuilt(c.query));
    assert.deepEqual(left,right);assert.deepEqual(requests[start],requests[start+1]);
    result.push({...c,original:left,rebuilt:right,request:requests[start],match:true});
  }
  await new Promise(r=>server.close(r));
  const left=await observe(()=>findNotes('断网'));
  const right=await observe(()=>rebuilt('断网'));
  assert.deepEqual(left,right);assert.equal(left.state,'rejected');
  result.push({name:'本地服务停止后的连接错误',original:left,rebuilt:right,match:true});
} finally { globalThis.fetch=nativeFetch;if(server.listening)await new Promise(r=>server.close(r)); }
const report={passed:true,observed_at:new Date().toISOString(),node:process.version,
 original_source:original,original_sha256:sha(originalBytes),rebuild_sha256:sha(await readFile(join(here,'rebuild.mjs'))),
 scope:'Original RepoGo fixture only. Actual HTTP to this process-owned 127.0.0.1 server. Static REA evidence reused; reconstruction and behavior comparison are ordinary Node code.',
 design_choices:['Local fixture dataset and substring search are our design, not recovered backend behavior','Absolute base URL and injected fetch adapt original browser-relative request to Node'],
 remaining:['No real third-party software reconstructed','Response schema, authentication and real backend unknown','No claim of complete semantic equivalence beyond these cases'],cases:result};
await writeFile(join(here,'comparison.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
