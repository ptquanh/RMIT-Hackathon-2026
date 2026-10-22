# TrustVault — shared instructions for Codex and Google Antigravity

Read `IMPLEMENTATION_PLAN.md` before making architectural/security changes.

- Use Tide Raziel MCP's live playbooks first for TideCloak, Forseti, E2EE and QEA tasks.
- Never invent Tide SDK method signatures, issuer URLs, role policy, cryptographic keys, or evidence of deployment.
- MCP is coding-agent guidance; it is not a replacement for a running TideCloak realm or Tide Fabric.
- Never claim backend `if` checks, mocked signatures, or UI badges are Tide-enforced authorization.
- If Forseti does not work, document the failure and scope claims down to real E2EE/QEA controls.
- Browser uses Next.js/Tide SDK; backend NestJS verifies access tokens/DPoP when applicable.
- Store sensitive beneficiary evidence as ciphertext only. Never log plaintext or credentials.
- Use BigInt integer VND, immutable canonical transaction payloads, and approval bound to exact payload hash.
- Mock gateway independently verifies authorized transactions and prevents replays; no force-settle bypass.
- Write focused success and denial tests. Do not report a test as passed without execution evidence.
- Only simulated monetary balances, no banking integration or real transfers.
- Keep README, setup commands, and known limitations synchronized with implementation.
