# 运行、接入与维护

## 本期采用的连接方式

`analyze.mjs` 使用上游公开 CLI 和官方 MCP JavaScript 客户端，启动本项目锁定的 REA 子进程。分析的是本期生成的原创 ASAR，随后读取同一会话保留的模块视图，并核对 CLI 与 MCP 完整 Evidence 的身份。

Evidence 是带来源与限制的结构化分析记录。启动器进一步核对两个脚本、两个指定导出、请求地址和路径的证据等级，不能只以“服务器连接了”作为分析通过。

```bash
python3 run.py run     # 重新生成归档并实际分析
python3 run.py check   # 只校验已有证据，不重新分析
python3 run.py serve   # 显示已有结果；Ctrl+C 停止
```

Windows 将 `python3` 换成 `py -3`。预览端口占用可用 `python3 run.py serve --port 5198`，浏览器同步改为 5198。

本期没有自动运行 `rea setup`，也没有修改任何全局 Agent 配置。若要让自己的 AI 软件长期使用 REA，先查 [官方安装文档](https://github.com/morluto/rea/blob/main/docs/installation.md) 对应客户端，审阅配置路径、备份与权限后再注册；本期独立 MCP 成功不代表你的软件已经注册成功。

支持手动 stdio 配置的客户端可参考以下形状，所有路径换成自己的绝对路径，别把示例直接照贴。stdio 表示客户端通过本地进程的标准输入输出通信。

```json
{
  "mcpServers": {
    "rea-repogo": {
      "command": "/absolute/path/to/supported/node",
      "args": ["/absolute/path/to/member/.runtime/node_modules/rea-agents/scripts/rea.mjs", "mcp"],
      "env": {"REA_LOG_LEVEL": "silent", "REA_MCP_OUTPUT_SCHEMA_PROFILE": "full"}
    }
  }
}
```

这只是手动配置参考，未验证某个 GUI 客户端重启后的接入；客户端的审批仍然有效。`analyze.mjs` 是本期已验证的可读接入示例，不要求你先给工具开放整个磁盘。

## 可向 Agent 提出的练习问题

“只分析我提供的原创 `original-notes.asar`，先调用 `analyze_javascript_application` 并使用 summary。列出脚本和导出；请求地址在哪里？页面路径是事实还是推断？引用 Evidence 与源文件行号，说明未知项，不执行样例。”

summary 只缩小返回内容，不代表少分析。继续查看时必须用本次返回的 `parent_evidence_id`；不要复制教程里的旧 ID 到新会话。`analyze.mjs` 演示了保留视图调用。没有分析工具时，Agent 自己猜的结果不能当作 REA 运行证据。

## 文件与恢复

- `fixture/`：原创假样例；手写紧凑 JS，不宣称由生产混淆器编译。
- `.runtime/node_modules/`：下载的程序依赖，更新或首次安装需联网。
- `.runtime/evidence/`：真实 CLI/MCP 输出、进程状态、工具 schema、归档指纹与核验记录。含本机路径，仅留本机排错，不上传公开文章。
- `.runtime/report/index.html`：从当前 Evidence 生成的 RepoGo 原创查看页；不是上游 UI。

代码修改后必须重新 `run`，不能拿旧页面当新结果。分析失败会中断，不启动预览；`serve` 也会先检查最近的 CLI 状态，拒绝失败后沿用旧成功报告。查看 `.runtime/evidence/cli-process.json`、`cli-stdout.log` 与 `mcp-stderr.log` 定位；分享日志先脱敏。

停止后重启预览不会重新下载。依赖锁变化时启动器重新执行 `npm ci`，会重建本项目依赖目录。需要重装同一锁版本时先停止进程，将 `.runtime` 改名保留旧证据，再重新启动。不要删除自己其他项目的配置或缓存。

## 版本与备份

固定 REA 6.8.0、MCP client 2.3.1，完整锁文件由 npm 官方 registry 安装验证。归档工具复用 REA 已有依赖 `@electron/asar`。没有全局安装，没有自动安装原生反编译引擎。

备份原创目录、锁文件与中文文档即可复建；如需保留一次分析身份，另外备份自己的 `.runtime/evidence`。升级先复制本项目到新目录，再审阅官方变更和许可、更新清单与锁，重新实跑并对照证据；不要把一次小练习的成功延伸为所有类型目标支持。
