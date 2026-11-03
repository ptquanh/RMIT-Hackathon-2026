# Security evidence and go/no-go record

Updated: 22/10/2026 (Asia/Ho_Chi_Minh)

## Raziel MCP gate

- Remote endpoint reached successfully: `https://mcp.tide.org/mcp`.
- Agent Pack reported version `1.9.33`.
- Selected official scaffold: `nextjs-e2ee-vault`.
- Policy-governed signing scenario confirms that transaction signing needs a custom Forseti contract.
- Raziel explicitly states that custom Forseti deployment is experimental and performed by the Tide team; the project must not invent or reconstruct an upload step.

## Realm incident

The prior local realm bootstrap failed during wallet/license creation:

- Error: `TIDE-IDPEXT-VENDOR-KEYGEN_FAILED`
- Failure: `Midgard.FinalizeWallet` HTTP 500
- Runtime version: `0.14.41-DEV`
- Affected realm: `entruth`
- Consequence: partially created realm state; retries encounter realm entruth/linking problems.

The organiser response was to build as though TideCloak protects the app, use Tide MCP for placement and boundaries, and temporarily simulate sign-in, roles and access checks.

## Decision

### Tide identity/E2EE/QEA: NO-GO for current run

No real login, doken, encrypted evidence result, denied decryption, or QEA approval has been observed in this repository. The official provider, DPoP page, server-side verifier and bootstrap assets are preserved for recovery, but runtime claims remain disabled.

### Forseti transaction signing: NO-GO until Tide deployment

No custom policy ID, authority public key, signed artifact, valid signing result or Forseti denial exists. The real gateway endpoint therefore fails closed with `TIDE_AUTHORIZATION_NOT_CONFIGURED`.

### Application simulation: implemented

The simulation demonstrates product flow only:

- explicit simulated sign-in and identity switching;
- server-owned identity-to-role/organisation claims (roles are never accepted from request bodies);
- protected-route checks with `401` for no identity and `403` for insufficient role;
- deterministic contribution matching;
- serializable database reservation;
- canonical payload and SHA-256 digest;
- distinct-organisation application approvals bound to that digest;
- changed-recipient denial;
- isolated gateway digest check and one-time nonce ledger.

These are application controls and must not be described as Tide enforcement.

The future replacement seam is deliberately narrow: TideCloak will authenticate the user and supply verified claims; the API route policies and organisation-level business checks remain server-side. The current `x-demo-user` header is accepted only while `AUTH_MODE=simulation`. Any other auth mode fails closed until the official Tide verifier is wired and verified.

## Tide Doctor result

The official Tide Doctor was run in check-only mode against the built app at `http://localhost:3000`:

- 10 checks passed, including byte-exact DPoP relay content, rewrite, CSP/`Allow-CSP-From`, server token-verifier presence and secret hygiene.
- One expected failure: no exported `data/tidecloak.json`, because the realm is not bootstrapped/recovered.
- One expected warning: the active provider is the organiser-approved simulation shell, so client DPoP is not enabled at runtime.

These findings are intentionally unresolved in simulation mode. Enabling the Tide provider without a valid adapter would make the UI look connected while login cannot work.

## Executed integration evidence

The full HTTP vertical slice was executed locally against PostgreSQL, NestJS and the separate gateway:

- protected dashboard without an identity returned `401`;
- an authenticated auditor calling a beneficiary-only route returned `403`;
- the Org A demo session resolved to the server-owned `approver` role and `org-a` organisation claim;
- allocation amounts: `5,000,000 + 5,000,000 + 2,000,000 VND`;
- two distinct application approvals moved the request to `READY_TO_AUTHORIZE`;
- changed recipient produced a different digest and was denied;
- security response retained `tideVerified: false`;
- simulation gateway issued one `APPLICATION_SIMULATION_ONLY` receipt;
- immediate replay was rejected.

## Evidence still required before enabling Tide mode

- [ ] Successful browser login against recovered/new realm.
- [ ] Server JWT issuer/audience/signature and DPoP verification.
- [ ] Client-side evidence encryption and authorised reviewer decryption.
- [ ] Genuine treasurer decryption denial.
- [ ] QEA role escalation pending without quorum.
- [ ] Tide-deployed Forseti contract ID and pinned verification key.
- [ ] One genuine signing success and one policy denial.
- [ ] Gateway verification of a real Tide artifact against exact canonical bytes.
