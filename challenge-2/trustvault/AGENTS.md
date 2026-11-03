# TrustVault agent instructions

- Read `IMPLEMENTATION_PLAN.md` before modifying architecture, IAM, evidence encryption, or signing code.
- This is a hackathon MVP using simulated money only. Never integrate a bank or claim real settlement.
- Use Tide Raziel MCP playbooks before TideCloak, E2EE, QEA, DPoP, or Forseti changes.
- Authentication is temporarily simulated under written organiser guidance. Keep it visibly labelled and isolated behind `AUTH_MODE=simulation`.
- Never represent simulation checks, backend role checks, or hashes as Tide-enforced authorization.
- Do not enable Forseti claims until a Tide-deployed custom contract and real positive/negative proof exist.
- Keep protected evidence plaintext client-side; the API may store ciphertext and non-sensitive metadata only.
- Use integer `BigInt` VND, canonical payload bytes, digest-bound approvals, and replay controls.
- Do not commit secrets, credentials, tokens, adapter exports, or plaintext beneficiary evidence.
- Run tests before reporting them as passed and keep security limitations synchronized with the README.
