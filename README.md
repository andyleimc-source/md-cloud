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

### 1. 安装

```bash
git clone https://github.com/andyleimc-source/md-cloud.git
cd md-cloud
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. 配置 .env

```bash
cp .env.example .env
```

编辑 `.env`：

```env
MD_ACCOUNT_ID=你的明道账号 UUID
MD_KEY=你的接入 key

# 可选,跑自己的 hook 后端时才需要:
# MD_APPNAME=mdcloud
# MD_HOOK_URL=https://api.mingdao.com/workflow/hooks2/xxx
```

> `MD_ACCOUNT_ID` 是你在明道云的 account_id（UUID 格式）。
> `MD_KEY` 是 md-cloud 运营方分配给你的接入凭据。
> 这两个字段共同确定一个明道账号；服务端用此映射到该账号的 OAuth token，并自动每日刷新。
>
> `MD_APPNAME` / `MD_HOOK_URL` 默认指向官方 mdcloud hook，**绝大多数用户不需要改**。仅当你部署了自己的 token 发放后端时才覆盖。

### 3. 在 Claude Code 中使用

`.mcp.json`（项目级）或通过 `claude mcp add`（用户级）：

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

> 把 env 写在 `.mcp.json` 里就不用 `.env` 文件了，二选一。

重启 Claude Code，就能直接对话操作明道：

- "帮我看看张三最近发了什么动态"
- "创建一个明天上午 10 点的日程，邀请李四"
- "给王五发一条消息说下午 3 点开会"
- "列出公司所有部门"

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

## API 参考

明道开放平台：<https://open.mingdao.com/document>

## License

MIT

---

## 关于

由 [雷码工坊](https://github.com/andyleimc-source) 维护。

姊妹项目：

- [mdold](https://github.com/andyleimc-source/mdold) — 本地 OAuth 完整版（功能等同，自己跑授权）
