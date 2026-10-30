#!/usr/bin/env python3
"""RepoGo original launcher; no global installation or Agent configuration changes."""
import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'


def node():
    command = os.environ.get('REPOGO_NODE') or shutil.which('node')
    if not command:
        raise RuntimeError('请先安装受支持的 Node.js，或设置 REPOGO_NODE 指向它的可执行文件。')
    command = str(Path(command).resolve())
    version = subprocess.check_output([command, '--version'], text=True).strip()
    match = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise RuntimeError('无法识别 Node 版本：' + version)
    major, minor, patch = map(int, match.groups())
    if not ((major == 22 and (minor, patch) >= (23, 4)) or
            (major == 24 and (minor, patch) >= (22, 1)) or
            (major, minor, patch) >= (26, 12, 1)):
        raise RuntimeError('REA 6.8.0 不支持当前 Node ' + version + '；要求 ^22.23.4 || ^24.22.1 || >=26.12.1。')
    print('Node:', version, flush=True)
    return command


def setup(command):
    RUNTIME.mkdir(exist_ok=True)
    wanted = (ROOT / 'runtime-package.json').read_bytes()
    lock = (ROOT / 'runtime-lock.json').read_bytes()
    manifest = RUNTIME / 'package.json'
    locked = RUNTIME / 'package-lock.json'
    ready = RUNTIME / 'repogo-install.json'
    import hashlib
    identity = hashlib.sha256(wanted + lock).hexdigest()
    if ready.exists() and json.loads(ready.read_text()).get('sha256') == identity and (RUNTIME / 'node_modules/rea-agents/scripts/rea.mjs').is_file():
        return
    manifest.write_bytes(wanted)
    locked.write_bytes(lock)
    npm = shutil.which('npm')
    if not npm:
        raise RuntimeError('未找到 npm；请使用带 npm 的 Node 安装。')
    env = dict(os.environ)
    env['PATH'] = str(Path(command).parent) + os.pathsep + env.get('PATH', '')
    args = [npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
    subprocess.run(args, cwd=RUNTIME, env=env, check=True)
    ready.write_text(json.dumps({'sha256': identity}), encoding='utf-8')


def serve(port):
    from report import validate
    validate(ROOT)
    directory = RUNTIME / 'report'
    if not (directory / 'index.html').is_file():
        raise RuntimeError('还没有本机结果；先运行 python3 run.py run。')
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    with http.server.ThreadingHTTPServer(('127.0.0.1', port), handler) as server:
        print('本机原创结果页：http://127.0.0.1:%d/ （Ctrl+C 停止）' % port, flush=True)
        server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='原创 ASAR 练习 → REA CLI/MCP → 中文结果页')
    parser.add_argument('action', choices=['run', 'serve', 'check'], nargs='?', default='run')
    parser.add_argument('--port', type=int, default=5197)
    args = parser.parse_args()
    if args.action == 'serve':
        serve(args.port)
    elif args.action == 'check':
        from report import validate
        validate(ROOT)
        print('已保存证据核验通过；本命令没有重新运行 REA。')
    else:
        command = node()
        setup(command)
        subprocess.run([command, str(ROOT / 'analyze.mjs')], cwd=ROOT, check=True)
        from report import build
        build(ROOT)
        print('分析与核验完成。运行 python3 run.py serve 查看本机结果。')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print('未完成：' + str(error), file=sys.stderr)
        sys.exit(1)
