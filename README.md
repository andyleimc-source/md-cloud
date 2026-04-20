# md-cloud

MCP Server for Mingdao Collaboration-era v1 API — **cloud-token mode**, no OAuth, no local secrets.

> 这是 [`mdold`](https://github.com/andyleimc-source/mdold) 的简化版，把 token 获取从本地 OAuth 流程改成远端 hook 三参数换 token，由服务端代为保管 access_token 并自动每日刷新。客户端只需要两个字段就能跑起来。

## 功能

提供约 **44 个**明道协作 v1 API 工具，覆盖 8 个模块：

| 模块 | 数量 | 主要能力 |
|------|-----|---------|
| 动态 (post) | 9 | 全公司/我的/用户/群组动态、详情、评论、发布、删除 |
| 日程 (calendar) | 8 | 列表、详情、邀请、搜索、创建、编辑、删除 |
| 私信 (webchat) | 6 | 会话、消息、未读、发送 |
| 收件箱 (message) | 2 | 系统通知、动态相关通知 |
| 群组 (group) | 10 | 详情、成员、加入/创建、管理员管理 |
| 用户 (user) | 6 | 联系人、组织成员、@搜索、按手机/邮箱查找 |
| 组织 (company) | 3 | 组织、部门、按 ID 查询 |
| 个人账户 (passport) | 4 | 当前用户详情、设置、未读、名片 |

工具签名与 [mdold](https://github.com/andyleimc-source/mdold) 完全一致，可作 drop-in 替换。

## 快速开始

```bash
git clone https://github.com/andyleimc-source/md-cloud.git
cd md-cloud
python3 install.py
```

一条命令走完全流程，脚本会引导你：

1. 创建 `.venv` 并安装依赖
2. 获取 `MD_ACCOUNT_ID` / `MD_KEY`（默认走浏览器隐身窗口 OAuth 授权；也可手动输入已有凭据）
3. 写入 `.env`
4. 可选把 md-cloud 注册到 Claude Code（项目级 `.mcp.json` 或调 `claude mcp add` 写到用户级，或两个都配）
5. 跑一次 token 换取验证

完成后重启 Claude Code，就能直接对话操作明道：

- "帮我看看张三最近发了什么动态"
- "创建一个明天上午 10 点的日程，邀请李四"
- "给王五发一条消息说下午 3 点开会"
- "列出公司所有部门"

### 高阶：手动安装

不想跑 `install.py` 的老用户看这里：

```bash
python3 -m venv .venv
.venv/bin/pip install .        # Python 3.14+ 必须用非 editable
.venv/bin/mdcloud-auth          # 或手动 cp .env.example .env 填 MD_ACCOUNT_ID / MD_KEY
```

然后在 `.mcp.json`（项目级）或用 `claude mcp add`（用户级）注册：

```json
{
  "mcpServers": {
    "md-cloud": {
      "type": "stdio",
      "command": "/绝对路径/md-cloud/.venv/bin/python3",
      "args": ["-m", "md_cloud.server"],
      "env": {
        "MD_ACCOUNT_ID": "你的-uuid",
        "MD_KEY": "你的-key"
      }
    }
  }
}
```

可选环境变量（几乎不用动）：

```env
# MD_APPNAME=mdcloud
# MD_HOOK_URL=https://api.mingdao.com/workflow/hooks2/xxx
# MD_APP_KEY=<自定义 OAuth 应用 app_key>
# MD_REGISTER_URL=<自定义注册 hook URL>
# MD_CALLBACK_PORT=8080
```

## 与 mdold 的差异

| 维度 | mdold | md-cloud |
|------|-------|----------|
| Token 获取 | 浏览器 OAuth + 本地 .secrets.json | POST hook，3 个字段换 token |
| Token 刷新 | 客户端用 refresh_token 续期，14 天必失效 | 服务端代管，自动每日刷新，永不过期 |
| 配置项 | app_key / app_secret / redirect_uri | account_id / key |
| 本地凭证文件 | .secrets.json（敏感） | 无 |
| 工具集 | 8 个模块 | 同 8 个模块 |
| 适合 | 个人开发者，自己跑 OAuth | 团队/产品场景，运营方统一发放 key |

## 工具明细

每个 `tools_*.py` 文件顶部注释列出了该模块的全部工具及其参数。直接在 Claude Code 中用自然语言唤起即可，无需手动调用。

## Token 缓存策略

- 启动时不预拉，第一次工具调用触发 `ensure_access_token()` 拉一次
- 命中后缓存到当天本地时间 23:59:59，次日 00:00 后下次调用时重新拉
- 拉取失败抛 `RuntimeError`，工具调用失败但 MCP server 不退出

不持久化到磁盘 — 重启进程即重新拉一次（多一个 ~200ms RTT，但无任何文件凭证残留）。

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `Missing MD_ACCOUNT_ID or MD_KEY` | .env 没配或 env 没注入 | 检查 .env / `.mcp.json` 的 env 字段 |
| `Token endpoint returned no token` | 服务端拒绝（key 不对、account_id 不存在、appname 拼错） | 确认 key 与 account_id；联系运营方 |
| HTTP 401 | token 失效（极少见，服务端日刷新） | 重启 MCP server 强制清缓存 |

## 注册 hook 协议（给自部署运营方）

`mdcloud-auth` 拿到 `code` 后会 POST 到 `MD_REGISTER_URL`（默认 `REGISTER_URL_DEFAULT`），协议：

**请求**：

```json
{ "code": "xxx", "redirect_uri": "http://localhost:8964/callback" }
```

**服务端应做**：

1. 用 `{app_key, app_secret, code, redirect_uri, grant_type=authorization_code}` 调 `https://api.mingdao.com/oauth2/access_token`
2. 用返回的 `access_token` 调 `/v1/passport/get_detail` 拿 `account_id`
3. Upsert `{account_id → refresh_token}` 到映射表；为该 `account_id` 复用或新生成一个 `key`
4. 返回：

```json
{ "account_id": "...", "key": "..." }
```

后续该 `account_id` 的 token 刷新由你现有的日刷 hook 负责。

## API 参考

明道开放平台：<https://open.mingdao.com/document>

## License

MIT

---

## 关于

由 [雷码工坊](https://github.com/andyleimc-source) 维护。

姊妹项目：

- [mdold](https://github.com/andyleimc-source/mdold) — 本地 OAuth 完整版（功能等同，自己跑授权）
