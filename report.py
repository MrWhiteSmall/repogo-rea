"""Render only actual local Evidence; this is a RepoGo page, not REA's official UI."""
import hashlib
from html import escape
import json
from pathlib import Path


def read(root, name):
    return json.loads((root / '.runtime/evidence' / name).read_text(encoding='utf-8'))


def validate(root):
    connection = read(root, 'connection.json')
    evidence = read(root, 'cli-evidence.json')
    mcp = read(root, 'mcp-analysis-response.json')['structuredContent']
    process = read(root, 'cli-process.json')
    if not connection.get('passed') or process['status'] != 0:
        raise RuntimeError('本次分析未通过，不能用旧报告代替成功。')
    if mcp['normalized_result']['parent_evidence_id'] != evidence['evidence_id']:
        raise RuntimeError('CLI/MCP Evidence 不一致。')
    artifact = root / '.runtime/evidence/original-notes.asar'
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != connection['artifact_sha256']:
        raise RuntimeError('样例归档指纹已变化。')
    nodes = evidence['normalized_result']['graph']['nodes']
    observations = [o for n in nodes for o in n['observations']]
    if not any(o['properties'].get('value') == '/api/notes/search' and o['evidence']['state'] == 'observed' for o in observations):
        raise RuntimeError('没有找到请求地址的静态事实。')
    if not any(o['properties'].get('value') == '/notes/:id' and o['evidence']['state'] == 'inferred' for o in observations):
        raise RuntimeError('路径应保留为推断。')
    if not connection.get('checks') or read(root, 'mcp-module-page.json').get('isError'):
        raise RuntimeError('缺少保留证据视图核验。')
    return connection, evidence


def build(root):
    connection, evidence = validate(root)
    norm = evidence['normalized_result']
    sources = []
    endpoints = []
    for node in norm['graph']['nodes']:
        for o in node['observations']:
            p = o['properties']
            if p.get('semantic_role') == 'source-module':
                sources.append((p['path'], ', '.join(p.get('export_names', []))))
            if p.get('endpoint_kind') in ['network', 'route']:
                endpoints.append((p['value'], o['evidence']['state'], o['evidence']['location']['value']))
    code = lambda x: '<code>' + escape(str(x)) + '</code>'
    module_rows = ''.join('<tr><td>' + code(p) + '</td><td>' + code(names) + '</td></tr>' for p, names in sorted(sources))
    findings = ''.join('<article><span class="status">' + ('语法事实' if state == 'observed' else '推断候选') + '</span><h3>' + code(value) + '</h3><p>' + escape(location.get('source', '')) + ' · 行 ' + str(location.get('start', {}).get('line', '?')) + '</p></article>' for value, state, location in endpoints)
    observed = escape(connection['observed_at'])
    digest = escape(connection['artifact_sha256'])
    eid = escape(evidence['evidence_id'])
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RepoGo · 读懂一个打包程序</title><style>
    :root{--paper:#f4f1e8;--ink:#202721;--red:#b64229;--line:#b9bcaf}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.65}main{max-width:1120px;margin:auto;padding:30px 40px 70px}header{display:flex;justify-content:space-between;border-bottom:2px solid var(--ink);padding-bottom:14px;font-family:"Avenir Next",sans-serif;font-size:13px;letter-spacing:2px}.eyebrow{color:var(--red);font-size:13px;font-weight:bold;letter-spacing:3px;margin:36px 0 12px}.hero{display:grid;grid-template-columns:1.8fr 1fr;gap:40px;align-items:end}h1{font-size:clamp(36px,5vw,63px);line-height:1.13;letter-spacing:-2px;margin:0 0 24px}h1 em{font-style:normal;color:var(--red)}.lead{font-size:18px;max-width:650px;margin:0}.stamp{border:1px solid var(--ink);padding:20px;transform:rotate(-2deg);font-family:"Avenir Next",sans-serif}.stamp strong{font-size:26px;display:block}.stamp p{font-size:13px;margin:8px 0}.bar{display:flex;flex-wrap:wrap;gap:10px 25px;border-block:1px solid var(--line);padding:14px 0;margin:28px 0 0;font-size:14px}.sectionhead{display:flex;gap:20px;align-items:baseline;margin:26px 0 12px}.sectionhead span{color:var(--red);font-family:monospace}.sectionhead h2{margin:0;font-size:23px}table{border-collapse:collapse;width:100%;font-size:15px}td,th{text-align:left;border-bottom:1px solid var(--line);padding:10px 12px}th{font-size:12px;font-family:sans-serif}code{font-family:"SFMono-Regular",Consolas,monospace;font-size:.9em;overflow-wrap:anywhere}.findings{display:grid;grid-template-columns:1fr 1fr;gap:18px}.findings article{padding:18px;border-left:3px solid var(--red);background:#e9e7dd}.status{font-family:sans-serif;font-size:12px;color:var(--red);font-weight:bold}h3{margin:8px 0}article p{margin:0;font-size:13px}.boundary{margin-top:22px;border-top:2px solid var(--ink);padding-top:13px;font-size:15px}.boundary b{color:var(--red)}details{margin-top:22px;font-size:13px}details p{overflow-wrap:anywhere}summary{cursor:pointer;font-weight:bold}footer{margin-top:28px;color:#62685d;font-size:12px;border-top:1px solid var(--line);padding-top:12px}@media(max-width:650px){main{padding:20px}.hero{grid-template-columns:1fr;gap:22px}.stamp{transform:none}.findings{grid-template-columns:1fr}header{font-size:10px;letter-spacing:1px}td{padding:10px 5px;font-size:13px}h1{letter-spacing:-1px}.eyebrow{margin-top:25px}.bar{gap:5px 16px}.lead{font-size:16px}}
    </style><main><header><b>RepoGo / FIELD NOTES</b><span>007 · REA 实跑练习</span></header><p class="eyebrow">从一个原创练习包开始</p><div class="hero"><div><h1>打包之后，<br>还能看懂<em>什么？</em></h1><p class="lead">让 Agent 接入分析工具，沿着文件、函数和请求地址读证据。先学会分清“看到了”与“猜到了”。</p></div><aside class="stamp"><strong>CLI + MCP 已核验</strong><p>REA 6.8.0 · NODE ''' + escape(connection['node']) + '''</p><p>真实分析原创 ASAR 归档<br>只读取样例，从未执行样例代码</p></aside></div><div class="bar"><span>2 个脚本已解析</span><span>请求地址：语法事实</span><span>页面路径：推断候选</span></div><div class="sectionhead"><span>01</span><h2>包里有哪些入口</h2></div><table><tr><th>脚本文件</th><th>静态导出</th></tr>''' + module_rows + '''</table><div class="sectionhead"><span>02</span><h2>找到的线索，各有证据等级</h2></div><div class="findings">''' + findings + '''</div><div class="boundary"><b>这次不能下的结论</b><br>不能证明请求已发送、接口存在、页面可访问或后端如何实现；不能恢复完整原始源码。原生程序反编译、Windows / Linux 与全局 Agent 注册均未实测。</div><details><summary>展开本次证据身份与限制</summary><p>观察时间（UTC）：''' + observed + '''</p><p>ASAR SHA-256：''' + code(digest) + '''</p><p>完整 Evidence：''' + code(eid) + '''</p><p>CLI / MCP 的完整分析身份一致；保留模块视图已读取。语义分析仍含未知项，静态关系不证明运行行为。</p></details><footer>RepoGo 原创结果查看页 · 不是 REA 官方界面 · 自有手写 JavaScript 练习，不冒充第三方产品逆向</footer></main></html>'''
    report = root / '.runtime/report'
    report.mkdir(parents=True, exist_ok=True)
    (report / 'index.html').write_text(html, encoding='utf-8')
