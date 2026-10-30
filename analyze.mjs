// RepoGo original practice. Analyze only the supplied original fixture; never execute it.
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {dirname,join,delimiter} from 'node:path';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

const root=dirname(fileURLToPath(import.meta.url));
const requireRuntime=createRequire(join(root,'.runtime/package.json'));
const {createPackage}=await import(pathToFileURL(requireRuntime.resolve('@electron/asar')).href);
const {Client}=await import(pathToFileURL(requireRuntime.resolve('@modelcontextprotocol/client')).href);
const {StdioClientTransport}=await import(pathToFileURL(requireRuntime.resolve('@modelcontextprotocol/client/stdio')).href);
const out=join(root,'.runtime/evidence');await mkdir(out,{recursive:true});
const artifact=join(out,'original-notes.asar');
await createPackage(join(root,'fixture'),artifact);
const artifactSha=createHash('sha256').update(await readFile(artifact)).digest('hex');
const entry=join(root,'.runtime/node_modules/rea-agents/scripts/rea.mjs');
const env={PATH:dirname(process.execPath)+delimiter+(process.env.PATH??''),
  ...(process.env.SystemRoot?{SystemRoot:process.env.SystemRoot}:{}),
  REA_LOG_LEVEL:'silent',REA_MCP_OUTPUT_SCHEMA_PROFILE:'full'};
const cli=spawnSync(process.execPath,[entry,'analyze-javascript-application',artifact,'--format','json'],
  {cwd:root,env,encoding:'utf8',timeout:120000,maxBuffer:32*1024*1024});
await writeFile(join(out,'cli-stderr.log'),cli.stderr??'');
await writeFile(join(out,'cli-stdout.log'),cli.stdout??'');
await writeFile(join(out,'cli-process.json'),JSON.stringify({status:cli.status,signal:cli.signal,error:cli.error?{code:cli.error.code,message:cli.error.message}:null},null,2));
if(cli.error||cli.status!==0)throw new Error('REA CLI failed; inspect .runtime/evidence/cli-process.json and cli-stdout.log');
await writeFile(join(out,'cli-evidence.json'),cli.stdout);
const cliEvidence=JSON.parse(cli.stdout);
console.log('CLI response keys:',Object.keys(cliEvidence));

const transport=new StdioClientTransport({command:process.execPath,args:[entry,'mcp'],env,stderr:'pipe',cwd:root});
const client=new Client({name:'repogo-original-practice',version:'1.0.0'});
let stderr='';transport.stderr?.on('data',c=>{stderr=(stderr+c.toString()).slice(-32768)});
try{
  await client.connect(transport);
  const list=await client.listTools();
  const names=list.tools.map(t=>t.name);
  await writeFile(join(out,'mcp-tool-schemas.json'),JSON.stringify(list.tools.filter(t=>['analyze_javascript_application','inspect_analysis_view','export_evidence_bundle','trace_application_feature'].includes(t.name)),null,2));
  if(!names.includes('analyze_javascript_application'))throw new Error('Expected MCP tool absent');
  const result=await client.callTool({name:'analyze_javascript_application',arguments:{input_path:artifact,detail:'summary'}},{timeout:120000});
  await writeFile(join(out,'mcp-analysis-response.json'),JSON.stringify(result,null,2));
  if(result.isError)throw new Error('MCP analysis returned an error; inspect saved response');
  const evidence=result.structuredContent;
  if(!evidence?.evidence_id||!evidence.normalized_result)throw new Error('No structured Evidence');
  const source={kind:'retained-evidence',evidence_id:evidence.normalized_result.parent_evidence_id};
  if(source.evidence_id!==cliEvidence.evidence_id)throw new Error('CLI/MCP retained identity mismatch');
  const page=await client.callTool({name:'inspect_analysis_view',arguments:{source,view:{kind:'page',collection:'modules',offset:0,limit:16}}});
  await writeFile(join(out,'mcp-module-page.json'),JSON.stringify(page,null,2));
  if(page.isError)throw new Error('Retained module view failed');
  const observations=cliEvidence.normalized_result.graph.nodes.flatMap(n=>n.observations.map(o=>({kind:n.kind,...o})));
  const has=(f)=>observations.some(f);
  if(!has(o=>o.properties?.value==='/api/notes/search'&&o.evidence?.state==='observed'))throw new Error('Missing observed request endpoint');
  if(!has(o=>o.properties?.value==='/notes/:id'&&o.evidence?.state==='inferred'))throw new Error('Route candidate boundary lost');
  for(const path of ['main.js','chunks/search.js'])if(!has(o=>o.properties?.semantic_role==='source-module'&&o.properties.path===path))throw new Error('Missing parsed source module '+path);
  for(const name of ['findNotes','searchNotes'])if(!has(o=>o.properties?.semantic_role==='export-binding'&&o.properties.exported_name===name))throw new Error('Missing export '+name);
  const summary={passed:true,observed_at:new Date().toISOString(),node:process.version,rea_version:'6.8.0',
    artifact_sha256:artifactSha,artifact:'original-notes.asar',cli_evidence_id:cliEvidence.evidence_id??null,
    mcp_evidence_id:evidence.evidence_id,parent_evidence_id:evidence.normalized_result.parent_evidence_id??null,
    tool_count:names.length,tool_name:'analyze_javascript_application',server:client.getServerVersion(),
    checks:['CLI/MCP full Evidence identity match','retained module page read','two source modules parsed','two expected exports found','request endpoint observed in syntax','route stays inferred; no runtime claim'],
    scope:'Original ASAR fixture, static analysis only; fixture never executed; no global Agent registration',
    not_verified:['native decompilation','Windows/Linux execution','GUI client restart/registration','commercial target analysis']};
  await writeFile(join(out,'connection.json'),JSON.stringify(summary,null,2));
  console.log(JSON.stringify(summary,null,2));
}finally{
  await client.close();await writeFile(join(out,'mcp-stderr.log'),stderr);
}
