"""MCP Server entry point — md-cloud (Mingdao Collaboration v1, cloud-token mode)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import (
    tools_calendar,
    tools_company,
    tools_group,
    tools_message,
    tools_passport,
    tools_post,
    tools_user,
    tools_webchat,
)
# from . import tools_task  # 默认禁用，如需任务模块自行启用

mcp = FastMCP(
    "md-cloud",
    instructions=(
        "明道协作时代 v1 API 工具集（云端 token 模式）。"
        "覆盖 动态 (post)、日程 (calendar)、私信 (webchat)、收件箱 (message)、"
        "群组 (group)、用户 (user)、组织 (company)、个人账户 (passport) 八个模块。"
        "无需 OAuth 授权，仅需在 .env 中配置 MD_ACCOUNT_ID 与 MD_KEY，"
        "服务端自动每日刷新 token。"
    ),
)

tools_post.register(mcp)
tools_calendar.register(mcp)
tools_webchat.register(mcp)
tools_message.register(mcp)
tools_group.register(mcp)
tools_user.register(mcp)
tools_company.register(mcp)
tools_passport.register(mcp)
# tools_task.register(mcp)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
