# TrustVault MCP-first starter configuration

This is **not** a working full-stack application; it contains validated client MCP configuration files, shared `AGENTS.md`, local PostgreSQL Compose, an env template and the implementation plan.

1. Open this directory as the workspace in Codex and Google Antigravity.
2. Ensure the Codex CLI trusts the project, then run `codex mcp list`.
3. In Antigravity, open MCP Servers > Manage MCP Servers and verify the Tide remote MCP server.
4. Ask both agents to read `IMPLEMENTATION_PLAN.md` and complete the feasibility spike.
5. Run `docker compose up -d postgres` for PostgreSQL.
6. Create Next.js/NestJS apps using the plan after Tide runtime setup is validated.

If the remote MCP transport fails, switch to the **stdio fallback** described in the implementation plan. Do not commit real secrets.
