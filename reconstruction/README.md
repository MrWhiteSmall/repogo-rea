# 从调用契约重建搜索客户端（RepoGo 原创）

这是已公开原创 ASAR 练习的补充，不是任何第三方软件的源码或后端。

先用主仓库 `python3 run.py run` 完成 REA 静态分析，定位 `findNotes`、`searchNotes` 与 `/api/notes/search`。本目录把读到的请求契约独立写成 `rebuild.mjs`，再与 `original/` 中同一原创函数做本机 HTTP 行为对照。

在本目录运行：

```sh
node run-comparison.mjs
```

使用 Node.js 26.12.1 验证，并经独立复核在 Node.js 26.9.0 通过；本补充无 npm 依赖，不调用模型，不访问外网。程序创建临时 `127.0.0.1` HTTP 服务，执行后自动关闭，生成本目录 `comparison.json`。输出 `passed: true`、五个 `match: true` 为本次成功标志。若运行环境禁止绑定本机端口，需要使用允许监听回环地址的正常终端；不要关闭系统保护。

`rebuild.mjs` 只包含客户端。笔记数据、子串搜索算法和响应 `{items,total}` 是练习服务自行设计，不能反推原来不存在的后端。新模块增加可配置的服务器地址，以适配 Node；原函数的相对路径通过受限制的 fetch 适配器转发到本进程创建的本机服务。对照覆盖中文、引号换行、503 JSON、无效 JSON 和服务停止；不证明任意输入下完全等价。

REA 在前一步负责提供静态依据；重建与 HTTP 对照由普通 Node.js 代码完成，不能说 REA 自动生成或自动验证了新模块。仅 macOS Apple Silicon Node26.12.1 实测本补充；Linux/Windows 未实测。主练习已有 Linux 核验的结论不自动延伸到本补充。

本目录 `original/`、`rebuild.mjs`、`run-comparison.mjs` 与本文档均为 RepoGo 原创练习，按主仓库 MIT 许可使用。归档的既有静态分析与本目录的运行证据分开保存。
