# TRUSTVAULT — MCP-FIRST IMPLEMENTATION PLAN

> **Product:** TrustVault — Covenant Transactions / Conditional Funding Network  
> **Competition:** RMIT Hackathon 2026 — Challenge 2: UNLOCKED (Tide)  
> **Version:** 1.0 · 22/10/2026 (Asia/Ho_Chi_Minh)  
> **Development agents:** OpenAI Codex + Google Antigravity  
> **Stack:** Next.js (TypeScript) · NestJS (TypeScript) · PostgreSQL · Prisma · Docker Compose · TideCloak · Tide Raziel MCP · Tide Forseti (spike)  
> **Status:** Implementation blueprint, not a claim that services or Tide policies have already been deployed.

## 0. QUICK START — READ THIS FIRST

**Business goal:** Allow multiple independent organizations to contribute to one conditional financial transaction without giving any one organization or backend unrestricted authority to redirect funds. For the hackathon, all funds and settlement are **simulated**.

**One-sentence pitch:** *TrustVault lets independent funders jointly execute a purpose-bound transaction while keeping contributor conditions, private evidence, and release authority protected from unilateral override.*

**Hard deadline per provided challenge brief:** 18:00, 22/10/2026 (Vietnam local time). Reconfirm with on-site organizers because remote web status and per-city times may disagree. **Do not postpone submission to add features.**

**P0 success in one demo:**

1. Sign in as real TideCloak users; authenticate NestJS API requests server-side.
2. Show three restricted contributions pooled to fund one request.
3. Freeze a **canonical** transaction payload and bind approvals to its digest.
4. Obtain and verify a **real Tide-governed authorization** if the Forseti spike succeeds; the mock gateway refuses altered/unsigned requests.
5. Demonstrate a genuine denied case — no UI-only fake “blocked” message.
6. Repository can be cloned and run; README, threat model, automated tests, and 2-minute `.mp4` are present.

**Critical scope truth:** Tide MCP **is documentation/playbooks for coding agents, not a runtime payment authorization service**. A TideCloak realm and Tide Fabric are still required. Tide QEA governs sensitive administrative changes; it does **not** automatically approve arbitrary payments. Forseti is the candidate for transaction-specific Tide authorization. If Forseti cannot be integrated and verified, narrow the claims and demonstrate real E2EE + QEA instead.

### Starting commands (after files are created)

```bash
# Requirements: Node.js LTS >= 20.9, npm, Git, Docker + Compose, Codex / Antigravity
mkdir trustvault && cd trustvault && git init
mkdir -p .codex .agents apps services docs tests tide packages

# Put the two MCP config files and AGENTS.md from §2 into this repo.
codex mcp list
# Open Antigravity IDE > MCP Servers > Manage MCP Servers; verify Tide is connected.

# Start database only; hosted TideCloak is preferred when provisioned.
docker compose up -d postgres

# Follow MCP feasibility prompts in §3 BEFORE generating most of the application.
```

---

## 1. PRODUCT SCOPE & DECISION RECORD

### 1.1 Personas

- **Donor / funder**: Organization with a fixed contribution amount and restrictions (`MEDICAL`, `TUITION`, etc.).
- **Treasurer**: Proposes a transaction but cannot authorize or settle on their own.
- **Independent verifier**: Reviews relevant beneficiary evidence where duly authorized.
- **Approver**: Endorses one *immutable* transaction with role/org constraints.
- **Beneficiary**: Receives simulated disbursement; uploads private supporting evidence.
- **Auditor / judge**: Sees non-sensitive trace, payload digest, approval status, authorization result.
- **Rogue admin / compromised API**: Threat actors attempting privilege escalation or payload tampering.

### 1.2 User journey — only one vertical slice

Scenario: A beneficiary needs **VND 12,000,000 in MEDICAL assistance**. Organization A contributes 5M (medical only), Organization B 8M (medical or tuition), Organization C 4M (requires independent verification). The matching engine picks A=5M, B=5M, C=2M. The beneficiary privately submits evidence. Approvers from distinct organizations endorse the fixed payload. Tide-protected release authorization is attempted. An isolated mock gateway only executes an authorized payload and guards replay/double spending.

**Attack story:** After approval, a treasurer changes `recipientRef` or `amount`. The new payload's digest differs; the gateway must reject the modified request. A rogue admin's attempted role escalation must be governed by Tide QEA, not by a frontend button.

### 1.3 In scope vs out of scope

| In scope / MVP | Out of scope |
|---|---|
| 3 organizations, 1 vault, 3 contributions, 1–2 funding requests | Banking integration, real money custody, KYC/AML |
| Conditional matching, reservation, approval flow, audited mock settlement | Crypto tokens / blockchain for decoration |
| TideCloak login, protected NestJS API | Building our own cryptographic algorithms |
| Tide E2EE + QEA where actual integration is proven | Fraud/identity claims unsupported by evidence |
| One Forseti signing spike + real proof if successful | Full smart-contract platform or arbitrary policy language |
| One human-friendly end-to-end demo + focused denial test | Complex OCR, LLM fine-tuning, elaborate analytics |

### 1.4 Five judging dimensions — evidence mapping

| Criterion | Weight | Concrete artifact |
|---|---:|---|
| Vision & originality | 25% | One transaction assembled from independent *restricted* contributions; no central unrestricted controller |
| Trust constraint insight | 20% | Diagram of conflicting actors and the specific unilateral-override threat |
| Value & impact | 20% | Student emergency funding case with privacy-preserving verification |
| Why TideCloak matters | 20% | Actual E2EE/QEA outcome and, if proven, Forseti-signed release; comparison with backend RBAC |
| Prototype & storytelling | 15% | Live successful request, denied tamper case, 2-minute video, reproducible instructions |

> Originality is an argument, not a claim of world-first invention. Safe multisig, donor-restricted funds, escrow, and Open Collective already exist. Differentiate through the precise *cross-organization experience* and Tide-enforced trust boundary.

---

## 2. MCP-FIRST SETUP FOR CODEX & GOOGLE ANTIGRAVITY

### 2.1 Confirmed correct project config: Codex

**Path:** `trustvault/.codex/config.toml` (project-scoped config; Codex must trust the project). Preferred remote Streamable HTTP:

```toml
[mcp_servers.tide]
url = "https://mcp.tide.org/mcp"
```

**Equivalent Codex CLI command (global config):**

```bash
codex mcp add tide --url https://mcp.tide.org/mcp
codex mcp list
# In the Codex TUI, inspect /mcp and ask for a Tide integration playbook.
```

**STDIO fallback** if remote MCP is unavailable (use INSTEAD of the remote stanza, not both under the same name):

```toml
[mcp_servers.tide]
command = "npx"
args = ["-y", "@tideorg/mcp"]
startup_timeout_sec = 30
```

**Important compatibility note:** Some Tide documentation still shows a Codex `~/.codex/config.json` example. The **current official Codex config** is `config.toml` with `[mcp_servers.<name>]`. Follow the Codex CLI/IDE documentation for the installed version. `codex mcp list` should show a working server, not merely a saved file.

### 2.2 Confirmed correct project config: Google Antigravity

**Path:** `trustvault/.agents/mcp_config.json`. Antigravity remote transport uses **`serverUrl`**, not `url`:

```json
{
  "mcpServers": {
    "tide": {
      "serverUrl": "https://mcp.tide.org/mcp"
    }
  }
}
```

**Where to verify (IDE):** Agent side panel `…` → **MCP Servers** → **Manage MCP Servers** → **View raw config**. Confirm Tide is enabled/connected and the agent can call its playbooks. Global alternative: `~/.gemini/config/mcp_config.json`.

**STDIO fallback** (replace the remote entry if transport fails):

```json
{
  "mcpServers": {
    "tide": {
      "command": "npx",
      "args": ["-y", "@tideorg/mcp"]
    }
  }
}
```

For STDIO, Node/npm and internet access are required when the MCP package is first installed. For remote mode, verify the corporate/firewall network can reach `https://mcp.tide.org/mcp`. Do not add fabricated API tokens; use the server's documented authentication if it changes.

### 2.3 Shared agent instructions — `AGENTS.md`

Both Codex and Google Antigravity accept a repo-root `AGENTS.md`. Keep it in version control. Recommended content:

```markdown
# TrustVault agent instructions

- Read IMPLEMENTATION_PLAN.md before modifying architecture, IAM, or signing code.
- This is an idea-led hackathon MVP, not a bank. Never integrate real money or fabricate monetary settlement.
- Use Tide Raziel MCP's verified playbooks before making TideCloak/Forseti/E2EE/QEA security decisions; cite the relevant playbook in PR notes.
- Never invent Tide SDK function signatures, realms, keys, policy IDs, admin accounts, or proof of deployment.
- Never claim a NestJS if-statement is cryptographic enforcement or use mocked signatures in the real authorization path.
- If Forseti signing is not verified, mark the feature NOT IMPLEMENTED and limit the claims to features proven by Tide.
- Frontend Next.js, backend NestJS, database PostgreSQL/Prisma. Keep explicit interfaces and canonical transaction schemas.
- Verify access token signature, issuer, audience, expiry, and DPoP when enabled. Never trust user-controlled role claims from HTTP bodies.
- Keep all protected document plaintext client-side. Store only ciphertext/necessary metadata in NestJS.
- Amounts are integer VND; no floats. Every settlement has idempotency/replay controls.
- Backend cannot bypass mock gateway authorization or directly mark a transaction SETTLED.
- Implement focused success/denial tests; do not report tests as passed before execution.
- Every completed slice must include: code, run command, passing tests, known limitations, README update.
- Do not commit secrets or local credentials. Do not run destructive DB migrations without review.
```

**Team workflow:** Codex owns NestJS/domain/database + unit tests, Antigravity owns Next.js/UI/integration tests. One designated **Security Owner** controls Tide realm/Forseti changes. Agents work on separate branches (`feat/api`, `feat/web`, `feat/tide`) and agree on shared JSON schemas first; avoid simultaneous edits to `apps/web` Tide SDK initialization or `.env` files. Assign code reviews before merging.

### 2.4 MCP verification gate (required)

In **each** coding agent, ask: 

> "Use the connected Tide/Raziel MCP tools. List the available setup, E2EE, QEA and Forseti signing playbooks, cite their version or source; identify current Next.js SDK interfaces. State which features require a running TideCloak realm and which require a deployed Forseti contract. Do not generate application code yet."

**Pass:** Agent demonstrates access to live MCP tools/resources and returns guidance with source links.  
**Fail:** It merely says it knows Tide from memory, invents methods or cannot list server capabilities. Fix MCP connection before work proceeds.

### 2.5 Hosted versus local TideCloak (runtime, separate from MCP)

1. **Preferred: hosted TideCloak realm** if the team actually has a provisionable, licensed realm and client information. Ask Raziel for the managed-hosting playbook. Verify the admin enrollment and OIDC discovery URL. Never assume a free hosted tenant exists.
2. **Fallback: dev TideCloak container** from the official Quickstart. This does **not** abandon MCP-first: Raziel still instructs the agent; Docker hosts the runtime identity server.

Local fallback command (development only):

```bash
docker run --name trustvault-tidecloak -d \
  -p 8080:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=change_me \
  -v tidecloak_h2:/opt/keycloak/data/h2 \
  tideorg/tidecloak-dev:latest
```

Then run `npm init @tidecloak/nextjs@latest web` inside `apps/` **if using the official scaffold**; follow its interactive enrollment instructions. The initializer may create/configure realm, client and license and must be allowed to finish. Never independently create a conflicting OIDC setup. On Windows, use PowerShell-equivalent line continuations or one line.

---

## 3. FEASIBILITY SPIKE — FIRST TECHNICAL TASK, BEFORE FULL BUILD

**Goal:** Avoid creating a full treasury UI whose claimed security cannot actually be implemented with Tide within the time limit.

### Spike A — Tide identity (must pass)

- [ ] MCP verified on Codex and Antigravity.
- [ ] Realm URL provisioned or local dev image running.
- [ ] User enrollment completed and Tide IdP / license configured.
- [ ] Client initialized, redirect URIs/web origins correct.
- [ ] Next.js login/logout works in a real browser.
- [ ] NestJS verifies a token with correct public JWKS, issuer/audience, and applicable DPoP rules.
- [ ] Capture redacted evidence (screenshots/logs) for README.

### Spike B — Forseti transaction signing (go/no-go for cryptographic settlement claim)

- [ ] Use Raziel's policy-governed signing scenario/playbook; identify supported SDK/package versions.
- [ ] Document `BaseTideRequest`, doken and role prerequisites.
- [ ] Deploy/configure ONE deterministic policy; confirm exact policy/contract ID.
- [ ] Obtain one real valid signature on canonical payload.
- [ ] Policy rejects one *actually invalid* payload/request before signature issuance.
- [ ] Mock gateway verifies signature against the correct pinned public key/policy identity.
- [ ] Changing recipient/amount/policy after authorization makes gateway reject.

**GO:** Build TrustVault with Forseti-governed payout claims.  
**NO-GO:** Immediately narrow demo to Tide E2EE + QEA proving that admins cannot access restricted evidence or self-elevate, with app-layer simulated payout **clearly labeled**. Do not assert Tide governs payments directly unless it does.

### Spike C — Tide E2EE/QEA (alternative/additional proof)

- [ ] Configure E2EE tags and roles; encryption requires QEA-enabled realm and doken as documented.
- [ ] Encrypt/decrypt using official SDK on client, store ciphertext only.
- [ ] Reviewer can decrypt; unauthorized treasurer cannot.
- [ ] Create three separate `tide-realm-admin` accounts if time allows; role-change attempt by one admin is not committed without required quorum.
- [ ] Clearly document master realm exceptions and admin collusion limitations.

---

## 4. ARCHITECTURE & TRUST BOUNDARIES

```mermaid
flowchart TD
  D[Donor / Beneficiary / Reviewer] --> W[Next.js Web + Tide SDK]
  W -->|Bearer/DPoP protected APIs| A[NestJS API]
  W -->|OIDC / E2EE / governed signing| T[TideCloak + Tide Fabric]
  A --> P[(PostgreSQL)]
  A --> F[Deterministic Funding Engine]
  F --> R[Frozen Canonical Request]
  R --> W
  W -->|Policy governed request if enabled| T
  T -->|Valid signed authorization| W
  W -->|Canonical payload + signature| G[Independent Mock Gateway]
  G -->|Receipt after verify + replay check| A
```

**Trust boundary B1 — Browser to API:** Token and role verification; frontend is untrusted.  
**B2 — API to database:** Database may be read by operator. No plaintext private evidence. A compromised DB could erase/alter availability; Tide does not make data indestructible.  
**B3 — API to Tide:** No backend-owned master signing key. Authorization is issued by real Tide policy/session if integrated.  
**B4 — API to gateway:** Settlement can occur only through independent verifier; NestJS has no `forceSettle` bypass.  
**B5 — Admin governance:** QEA for protected admin changes; not equivalent to authorization of an arbitrary funding request.  
**B6 — Between funders:** A cannot unilaterally modify another funder's covenant; signed/pinned conditions are required for stronger guarantees.

### Canonical transaction signing invariant

```
Only a canonical, frozen payload X with hash H(X), under fixed policy P,
whose required authorization is valid, may be settled exactly once.
```

**Do not blindly sign a hash prepared by a compromised NestJS backend.** The exact restrictions claimed to be Tide-enforced must either be checked by the Forseti contract (possibly using committed/pinned policy parameters), or the product claims must say they are only application-validated. Fully dynamic donor-specific restriction checking may require more than the hackathon spike supports.

---

## 5. MONOREPO & DEVELOPMENT ENVIRONMENT

### 5.1 Structure

```text
trustvault/
├── .codex/config.toml              # Codex Tide MCP
├── .agents/mcp_config.json         # Antigravity Tide MCP
├── AGENTS.md                       # Shared coding agent constraints
├── apps/
│   ├── web/                        # Next.js App Router + Tide SDK
│   └── api/                        # NestJS + Prisma
├── services/
│   └── mock-gateway/               # Separate verification + replay ledger
├── packages/
│   └── contracts/                  # Shared Zod DTO schemas / canonical serializer
├── tide/
│   └── forseti/                   # Policy contract + deployment instructions, if real
├── IMPLEMENTATION_PLAN.md
├── docs/
│   ├── threat-model.md
│   ├── security-evidence.md
│   ├── architecture.md
│   └── demo-storyboard.md
├── tests/
│   ├── integration/
│   └── adversarial/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### 5.2 Minimal `docker-compose.yml` — database only

Use hosted TideCloak where available; NestJS and Next.js run on host for fast debugging. This Compose file does not silently pretend that `mcp.tide.org` is your Tide identity server.

```yaml
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: trustvault
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-trustvault_dev_only}
      POSTGRES_DB: trustvault
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trustvault -d trustvault"]
      interval: 5s
      timeout: 3s
      retries: 15
volumes:
  postgres_data:
```

To start: `docker compose up -d postgres`. To check: `docker compose ps` and `docker compose logs postgres`.

### 5.3 Bootstrap commands

```bash
# From repository root, after the Tide feasibility spike:
mkdir -p apps packages services docs tide tests

# Web: official Tide scaffold first, NOT a second competing OIDC implementation
cd apps
npm init @tidecloak/nextjs@latest web

# API
npx @nestjs/cli@latest new api --package-manager npm
cd api
npm install @nestjs/config @nestjs/swagger class-validator class-transformer jose
npm install @prisma/client@6
npm install -D prisma@6
npx prisma init --datasource-provider postgresql
```

**Do not overwrite SDK-specific files generated by Tide scaffold.** Let Raziel inspect scaffold and its exact SDK version before adding wrappers or custom session logic. Run `npm run dev` separately in `apps/web` and `npm run start:dev` in `apps/api`. Adapt scripts to scaffold output.

### 5.4 `.env.example` (non-secret placeholders)

```dotenv
# Database on host
DATABASE_URL=postgresql://trustvault:YOUR_LOCAL_PASSWORD@localhost:5432/trustvault
PORT=3001
WEB_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3001

# Real values from provisioning; never use the MCP URL as the OIDC issuer.
TIDE_OIDC_ISSUER=https://REPLACE_WITH_REAL_TIDECLOAK_HOST/realms/REPLACE_REALM
TIDE_OIDC_JWKS_URI=https://REPLACE_WITH_REAL_TIDECLOAK_HOST/realms/REPLACE_REALM/protocol/openid-connect/certs
TIDE_API_AUDIENCE=REPLACE_WITH_CONFIGURED_API_AUDIENCE

# Transaction signing only if truly deployed and verified
FORSETI_CONTRACT_ID=REPLACE_AFTER_DEPLOYMENT
TIDE_AUTHORITY_PUBLIC_KEY=REPLACE_WITH_VERIFIED_PUBLIC_KEY
MOCK_GATEWAY_URL=http://localhost:3002
```

Use `.env.local`/`.env` ignored by Git. Keep Tide enrollment tokens, OAuth client secrets, signing configuration credentials and real user data out of source control and videos.

### 5.5 Dockerize apps later (not before passing auth)

Add multi-stage Dockerfiles and compose services after end-to-end localhost integration succeeds. Beware that browser `localhost` and Docker service DNS names are different: token `iss` is an **exact match**, so do not rewrite issuer strings merely to make a container connect. Decide a single browser-reachable issuer and configure network DNS/TLS consistently. If uncertain, leave Next.js/NestJS on host for the hackathon.

---

## 6. BACKEND MODULES, DATA MODEL & ENDPOINTS

### 6.1 NestJS modules

| Module | Responsibility |
|---|---|
| `AuthModule` | Verify Tide OIDC access tokens, issuer, audience, optional DPoP, role/org membership |
| `OrganizationsModule` | Three seeded organizations and memberships |
| `VaultsModule` | Vault metadata / immutable policy revision |
| `ContributionsModule` | Donor commitments with restrictions and available balances |
| `FundingRequestsModule` | Beneficiary request and finite state machine |
| `MatchingModule` | Deterministic eligible-source allocations |
| `EvidenceModule` | Only Tide-encrypted evidence blobs and metadata |
| `ApprovalsModule` | Who approved exactly what payload hash |
| `TideModule` | Ports/adapters for realm, encryption metadata, authorization result verification |
| `SettlementsModule` | Calls independent mock gateway; no local force-settlement |
| `AuditModule` | Append-only application activity events (not cryptographically immutable) |

### 6.2 Relational schema — conceptual

```text
User(id, tideSub UNIQUE, name)
Organization(id, name)
Membership(userId, orgId, role, UNIQUE(userId, orgId, role))
Vault(id, purpose, currency, policyVersion, status)
Contribution(id, vaultId, donorOrgId, originalAmount, availableAmount,
             reservedAmount, allowedCategories, requiresIndependentVerification,
             deadlineAt, conditionsHash, status)
FundingRequest(id, vaultId, beneficiaryId, category, amount, recipientRef,
               status, canonicalPayloadHash, nonce UNIQUE, expiresAt, policyVersion)
Allocation(id, fundingRequestId, contributionId, amount)
Approval(id, fundingRequestId, signerSub, signerOrgId, decision,
         payloadHash, approvedAt, UNIQUE(fundingRequestId, signerSub))
Evidence(id, fundingRequestId, ciphertext, encryptionMetadata, createdAt)
Authorization(id, fundingRequestId UNIQUE, policyContractId, payloadHash,
              signedArtifact, publicKeyFingerprint, issuedAt)
Settlement(id, fundingRequestId UNIQUE, idempotencyKey UNIQUE, receipt, status)
AuditEvent(id, actorSub, action, entityId, metadata, createdAt)
```

**Amounts:** use Prisma `BigInt` integer minor units (VND integer đồng) and return decimal strings over JSON; never binary floating point. Use unique constraints, checked invariants at application level or SQL, and serializable transactions/row locks when reserving balances. A `preview` never deducts money.

### 6.3 HTTP endpoints

| Verb | Endpoint | Role / meaning |
|---|---|---|
| GET | `/health` | public health, minimal details |
| GET | `/auth/me` | authenticated user's identity and memberships |
| GET / POST | `/vaults` | list/create (treasurer/admin) |
| GET | `/vaults/:id` | vault + contributions summary |
| POST | `/vaults/:id/contributions` | seed or register simulated funder contribution |
| POST | `/funding-requests` | create draft |
| POST | `/funding-requests/:id/preview` | eligibility matching (read-only) |
| POST | `/funding-requests/:id/submit` | reserve allocations and freeze payload |
| POST | `/funding-requests/:id/approvals` | attach approval to `payloadHash` |
| POST | `/funding-requests/:id/authorize` | initiate/verify real Tide signing flow, if integrated |
| POST | `/settlements/:id/execute` | forward signed payload to gateway; no bypass |
| GET | `/funding-requests/:id/audit` | safe timeline (redacted) |

Use DTO validation, consistent typed errors (`POLICY_DENIED`, `QUORUM_NOT_MET`, `INVALID_SIGNATURE`, `EXPIRED`, `REPLAY`, `INSUFFICIENT_ELIGIBLE_FUNDS`, `UNAUTHORIZED`), NestJS guards, Prisma transactions, and rate limits for security-sensitive mutation routes.

### 6.4 State machine

```text
DRAFT -> PENDING_REVIEW -> READY_TO_AUTHORIZE -> AUTHORIZED -> SETTLED
                 |                 |                |
                 v                 v                v
              REJECTED          REJECTED          EXPIRED
                 |
                 +--> EXPIRED (when allowed by state policy)
```

No direct `DRAFT -> SETTLED`. Terminal states do not revert. Any change to amount, recipient, allocations, or policy after submit creates a new revision/request with a fresh digest, approvals, and nonce.

### 6.5 Deterministic matching

1. Filter contributions by available balance, category, deadline, beneficiary constraints, verification status and permitted target.
2. Order by deterministic rule: earliest expiry, then ID (document the choice).
3. Allocate until request covered; if not fully covered return `INSUFFICIENT_ELIGIBLE_FUNDS`.
4. Lock/reserve amounts atomically on `submit` (not preview). Prevent two concurrent requests from reserving same funds.
5. Release reservations on reject/expire; convert reserved→spent only on verified gateway receipt.
6. Recalculate/check on every transition. Don't trust browser-provided allocation totals.

**Matching engine pseudocode:**

```ts
for (const c of eligibleContributionsSorted) {
  const take = min(c.available - c.reserved, remainingRequestAmount);
  if (take > 0n) allocations.push({ contributionId: c.id, amount: take });
  remainingRequestAmount -= take;
  if (remainingRequestAmount === 0n) break;
}
if (remainingRequestAmount > 0n) throw new InsufficientEligibleFundsError();
// Reserve only in a DB transaction with concurrency control.
```

---

## 7. COVENANT TRANSACTION PAYLOAD & CRYPTO BOUNDARY

### 7.1 Example payload

```json
{
  "schemaVersion": "1",
  "vaultId": "vault-student-relief",
  "requestId": "req-0001",
  "currency": "VND",
  "amount": "12000000",
  "category": "MEDICAL",
  "recipientRef": "hospital-demo-01",
  "allocations": [
    { "contributionId": "c-A", "amount": "5000000", "conditionsHash": "sha256:<A>" },
    { "contributionId": "c-B", "amount": "5000000", "conditionsHash": "sha256:<B>" },
    { "contributionId": "c-C", "amount": "2000000", "conditionsHash": "sha256:<C>" }
  ],
  "policyVersion": "1",
  "nonce": "req-0001-v1-once",
  "expiresAt": "2026-10-22T17:55:00+07:00"
}
```

The `<A>` fields above are **placeholders**, not actual SHA-256 digests. Build a deterministic/canonical JSON serializer (e.g. a well-documented canonical JSON standard) shared by NestJS, frontend, gateway and Tide adapter. Use UTF-8 byte sequence, hash the canonical bytes, and store exact bytes/signed payload. Do not sign a different representation per language/runtime. Bind the contract/policy identifier and verified key identity explicitly.

### 7.2 Trust enforcement matrix

| Rule | App check | Tide Forseti | Gateway check |
|---|---|---|---|
| Amount and recipient match approved payload | Yes | Must bind to signed payload | Recalculate hash and verify |
| Category/conditions are eligible | Deterministic engine | **Only claim enforced if encoded/checked in real policy** | Enforce signed policy identity; do not invent condition evaluation |
| Approval quorum and distinct organizations | Approval records | Forseti `ValidateApprovers` if implemented | Require valid Tide signed authorization |
| Authorized executor | NestJS role guard | Forseti `ValidateExecutor` if configured | Verify correct trusted signed result |
| Deadline | DB | Policy if supported | Independent expiration check |
| One-time transaction | DB reservation | Do not assume Forseti is stateful | Atomic unique nonce/idempotency check |
| Double spend | Serial transactions | Not automatically a Tide function | Durable gateway ledger and atomicity |

**Never claim 'cryptographically impossible to misuse funds'** if application admins can modify donor restrictions and have them accepted in the signing policy. The security proof must be scoped to exactly what the Tide nodes actually verify.

### 7.3 Forseti adaptation outline (not fabricated SDK code)

- Obtain verified official playbook from Raziel; inspect `@tidecloak/js`, `heimdall-tide`, doken and supported request formats for installed versions.
- Define a small C# contract enforcing a **fixed test policy**: e.g. request category `MEDICAL`, max amount, a known vault/policy revision, two distinct eligible approver organizations, authorized executor.
- Deploy policy via the documented Tide workflow; pin contract ID (source-hash-derived) and permitted verification key(s).
- Build a browser-side signing request using actual Tide SDK. Persist only completed, verifiable artifacts in NestJS.
- Gateway verifies on bytes and trusted authority, not on a client-provided boolean `approved: true`.
- Test valid, invalid, tampered and replay attempts. If developer cannot demonstrate the policy checked the advertised field, revise the claim.

**Important:** Forseti sandbox is intended to be deterministic/stateless. It cannot query our Prisma DB arbitrarily to learn donor balances. Data freshness, reservation and replay protection must be handled separately; the signed policy can verify committed input and participant authority, not magically prove every off-chain fact.

---

## 8. E2EE & QEA IMPLEMENTATION

### 8.1 Evidence E2EE

1. Define one data class `beneficiary_evidence` and required encryption/decryption roles/tags according to official E2EE playbook.
2. Configure and commit required Tide role changes through QEA.
3. Authorize encryption for beneficiary; authorize decryption only for independent reviewer (avoid giving all users a default decrypt role).
4. Browser encrypts data with Tide SDK. API stores ciphertext + encryption metadata; logs never print plaintext.
5. Reviewer opens evidence and decrypts via SDK; treasurer and rogue admin without rights cannot.
6. Revocation prevents future authorized access, **not** copies previously read by permitted reviewers.

**Prerequisite from Tide docs:** E2EE requires a Tide realm with QEA enabled; the sign-in doken is needed for encryption/decryption. Use playbook-recommended tag/role syntax for the exact SDK version.

### 8.2 Administrative governance QEA

- Three *distinct* Tide realm admin identities, where possible.
- Test new role assignment / self-escalation as a governed change request.
- Observe request pending when the actual quorum is not satisfied; commit only after required approvals.
- Keep screenshots of pending and committed states.
- QEA protects eligible administrative operations; it is **not** the payment-authorization workflow.
- Document exceptions and assumptions, including master realm, number of administrators, and collusion if quorum parties cooperate maliciously.

---

## 9. NEXT.JS UX — FIVE SCREENS

1. **`/dashboard`** — Total simulated vault, fundable balance, pending requests, cross-campus donor organizations, activity.
2. **`/vaults/[id]`** — Contributions with conditions/amounts, no unnecessary personal data, request new funding.
3. **`/requests/new`** — Request category, amount, recipient; show eligible contributions and preview allocations. Inform user matching is not authorization.
4. **`/requests/[id]` + `/approvals`** — Frozen payload with hash, exact conditions, independent approver state; retry/denial reason.
5. **`/security-demo`** — Side-by-side valid request vs tampered request: trust boundary, signature verification result, replay test. Clearly identify actual Tide result vs simulated financial ledger.

UX essentials: readable state labels, amount consistency, short explanations of trust constraints, responsive demo at 1440×900 or laptop size, avoid animation reliance. Build one polished vertical slice rather than five complex screens.

**Client→backend auth:** TideCloak OIDC SDK handles sign-in/session; NestJS must verify access tokens via JWKS and issuer/audience. If Tide requires DPoP sender-bound proof, verify that too. User-facing role selectors are not authority sources. Never put signing secrets in `NEXT_PUBLIC_*` environment variables.

---

## 10. INDEPENDENT MOCK SETTLEMENT SERVICE

Gateway must run in **separate process/port** (suggest `localhost:3002`) with its own verifier and durable unique transaction ledger. The API must not bypass it.

Interface draft:

```http
POST /settlements
Content-Type: application/json

{
  "canonicalPayload": "<base64url exact signed bytes>",
  "authorization": "<verifiable Tide artifact>",
  "policyId": "<pinned approved policy>"
}
```

Checks: trusted policy/authority, correct signature on **exact bytes**, required fields, allowed currency, expiration, idempotency nonce, non-negative simulated balance/reservation. All checks run before atomic transaction in gateway ledger. Persist unique `(requestId, nonce)` and return `receiptId` only once. Replays are rejected or deterministically return an idempotent prior receipt without double-debit; document chosen behavior.

No signing integration? Then gateway supports a separate `simulationOnly` route for UI tests but MUST reject claims that this is Tide-protected settlement. Do not include production-looking bypass endpoints in the demo path.

---

## 11. TEST PLAN, ADVERSARY SCRIPTS, AND THREAT MODEL

### 11.1 Functional tests

| ID | Test | Expected |
|---|---|---|
| F01 | Eligible contributions sum to 12M | Matching returns A=5M B=5M C=2M |
| F02 | `MEDICAL` request tries tuition-only contribution | Disallowed source excluded |
| F03 | Insufficient eligible money | Clear rejection, no reservation |
| F04 | Parallel submissions compete for same contribution | Exactly one valid reservation; no negative balance |
| F05 | Rejected request releases reservation | Available balance restored atomically |
| F06 | Repeated settlement request | No second debit |
| F07 | BigInt + currency handling | No rounding errors; decimal strings at API boundary |

### 11.2 Security tests

| ID | Attacker action | Expected observed evidence |
|---|---|---|
| S01 | No token / forged JWT | NestJS 401 (correct issuer, audience, signature) |
| S02 | Wrong org or role | NestJS 403 |
| S03 | Admin self-elevation with insufficient Tide quorum | QEA change pending/not committed |
| S04 | Treasurer tries to decrypt beneficiary evidence | Tide decryption refused |
| S05 | Change `recipientRef` after signing | Gateway signature verification rejects |
| S06 | Signed request expired | Gateway rejects |
| S07 | Replay nonce | No second settlement |
| S08 | Invalid policy payload or insufficient approvers | **Forseti refusal, only if integrated** |
| S09 | Direct unauthenticated gateway call | Gateway refuses without verifiable authorization |

**Evidence:** log the request hash, policy/contract ID, status and test assertion, not tokens, secrets or plaintext evidence. For scripts, use `tests/adversarial/attack-rogue-admin.md` to document interactive QEA UI, plus `tests/adversarial/tamper-recipient.test.ts`, `tests/adversarial/replay.test.ts` for deterministic attacks in our own local environment. Do not target real third-party systems.

### 11.3 Threat model — concise STRIDE-inspired

| Asset | Threat | Assumption / control | Residual risk |
|---|---|---|---|
| Contributions/balances | tampering/double spend | DB transaction, ledger consistency, gateway nonce | DB operator can disrupt availability |
| Identity and approvals | account takeover / escalation | Tide OIDC, QEA, role verification | Enough authorized parties can collude |
| Evidence | database dump | Tide client-side E2EE | Approved recipient can copy plaintext |
| Transaction release | compromised NestJS | Forseti policy + gateway verifies artifact | Depends on what policy actually checks |
| Audit | operator edits logs | correlation with signed payload/receipts | Local DB audit is not immutable |
| Signing | tampered recipient/amount | canonical payload binding | Incorrect key trust or implementation bug |

Never claim absolute resistance to root compromise, all insider collusion or every Tide network failure; define what is actually protected.

---

## 12. EXECUTION ROADMAP & PARALLEL TASKS

**Team of four, timeboxed; prioritization over complexity.** Indicative blocks, not promises. Switch to narrower security demo at the go/no-go gate.

| Track | Owner | Implementation tasks | Acceptance criteria |
|---|---|---|---|
| Security integration | A | MCP setup; realm/enrollment; Tide OIDC + E2EE/QEA; Forseti spike | Real account works, at least one authentic protected denial; signing proof if claimed |
| Backend/domain | B (Codex) | NestJS, Prisma, matching, reservation, states, tests | 12M matching + concurrency tests; endpoints validated |
| Frontend/UX | C (Antigravity) | Tide scaffold, request preview, vault, approvals, demo view | Users can run one happy path from UI |
| Integration/pitch | D | Docker, gateway, QA, attack tests, README, demo.mp4 | Fresh clone instructions; <=2-min video and repo |

### Gates

**Gate 0 — up to first 20 minutes:** MCP transport and real Tide realm status. Fork hosted vs local runtime.  
**Gate 1 — security feasibility (next ~30–45 minutes, concurrent):** Forseti proof-of-concept signing (or explicit NO-GO). No false claims.  
**Gate 2 — one vertical slice:** 3 contributions → request → allocation → approval → authorize (if real) → mock settlement.  
**Gate 3 — polish & attack tests:** real denied behavior + accessible error explanation.  
**Gate 4 — submission freeze:** README <=300-word overview, source, `demo.mp4` <=2 min and <100 MB, public GitHub repo, submit correct URL. Reserve time for upload and verification.

**Merge order:** shared contracts → API/seed → web integration → Tide proof adapter → gateway verification → tests → README/video.

### Contingency matrix

| Blocker | Immediate response |
|---|---|
| Remote MCP unavailable | Change both agents to documented stdio `@tideorg/mcp` form |
| Hosted TideCloak unavailable | Use dev image from official Tide Quickstart and same Raziel playbooks |
| E2EE role setup fails | Pause protected-document claims, fix realm QEA and tags, simplify demo |
| Forseti deployment/signing blocked | Keep E2EE/QEA real, simulate finances explicitly, remove cryptographic-payment guarantee |
| All three features fail | Do not submit fake security proof; reduce feature surface and disclose limitations |
| Gateway verifier not complete | Stop calling settlement "Tide-enforced"; settle only in clearly labeled simulation mode |

---

## 13. COPY-READY PROMPTS FOR CODEX AND ANTIGRAVITY

### Prompt A — Security Owner / Codex (FIRST)

```text
Project: TrustVault / RMIT Hackathon Challenge 2. Read AGENTS.md and IMPLEMENTATION_PLAN.md.
Use Tide Raziel MCP tools before Tide-related code. First prove MCP connectivity and retrieve the relevant
TideCloak authentication, E2EE/QEA and Forseti policy-governed signing playbooks. List verified prerequisites,
SDK versions, environment/realm setup and any unsupported features. Perform a REAL vertical integration spike:
1) provision or connect to a real TideCloak realm; 2) login; 3) determine if a policy-governed signature is possible;
4) show at least one valid and one policy-denied Tide result. Do not mock signatures, fabricate SDK calls, or assume
MCP provides a Tide runtime. Record status, exact commands, errors and evidence in docs/security-evidence.md.
Then advise GO/NO-GO for Forseti-backed TrustVault transactions.
```

### Prompt B — Backend (Codex)

```text
Read AGENTS.md and the implementation plan. Implement only NestJS + Prisma domain slice:
organizations, vault, 3 donor contributions with restrictive categories, funding request, deterministic matching,
atomic reservation, request state transitions, approval digest binding, and safe audit trail. Use BigInt for VND.
JWT authentication must be verified server-side using Tide OIDC discovery/JWKS with issuer and audience checks;
follow Raziel playbooks for DPoP if enabled. Expose API DTOs through shared contracts.
No direct settle bypass. Make a mocked authorization adapter clearly distinguishable from a real Tide one.
Add concurrency, authorization, matching, expiration and replay-focused tests. Provide run/seed/test commands.
```

### Prompt C — Frontend (Google Antigravity)

```text
Read AGENTS.md and IMPLEMENTATION_PLAN.md. Use connected Tide MCP playbooks and the official TideCloak
Next.js starter; do not replace OIDC/session implementation with ad-hoc auth. Build a polished, compact demo
of one conditional transaction: 3 funders, 12M VND medical assistance, eligibility matching preview,
immutable submitted payload, independent approvals, real Tide authorization status, security demo screen.
Display ONLY verified security results. Include human-readable explanation of denied transactions.
Use API contracts, do not hardcode the final status. Avoid sensitive info on donor dashboards.
```

### Prompt D — QA/Integration

```text
Audit TrustVault against the five challenge judging criteria. Test a real user journey and an attacker journey.
Record which controls are guaranteed by Tide, which by our NestJS application, which by an independent gateway,
and which are not implemented. Produce setup steps, threat model, reproducible tests, README <=300-word project
overview, and exact 120-second video storyboard. Never claim a test passed without logs.
```

---

## 14. JUDGE-FRIENDLY TWO-MINUTE DEMO

| Time | Screen/action | Judges should understand |
|---|---|---|
| 0–18s | Three independent organizations want to help one student; each has different conditions | The *trust bottleneck* |
| 18–42s | Create restricted contributions; user requests 12M; matching engine allocates funds | The new experience / originality |
| 42–62s | Show private evidence permission and a legitimate reviewer, if E2EE works | Privacy without total transparency |
| 62–89s | Rogue actor changes recipient or attempts privilege escalation; real Tide/gateway denial | Trust boundary is not a UI button |
| 89–108s | Valid approvers authorize exact transaction; real signature verified if implemented | Working Tide-based authorization |
| 108–120s | Show verified mock receipt + contributors' privacy-safe view | Human value, strong close |

**Pitch:** “We made one transaction possible across independent funders — without making any one person the owner of everyone else's trust.”

For a fallback E2EE/QEA-only build, replace “Tide-signed disbursement” with what Tide is genuinely doing: restricting access to evidence and the administrative ability to change who can read it. Explicitly label financial settlement as **simulated application logic**.

---

## 15. REPOSITORY DELIVERY, README, AND PROOF MATRIX

Recommended root `README.md` order:

1. **Project overview — <=300 words in English:** one sentence + direct responses to five Tide rubric questions.
2. Demo video (relative link `demo.mp4`) and 3–4 screenshots.
3. Architecture and trust boundaries.
4. Setup (tested OS, Node, Docker, ports, MCP config, Tide realm and enrollment prerequisites).
5. How to run a successful case, malicious case and the automated tests.
6. Security guarantees **versus non-goals** and known limitations.
7. Technical references, author/team acknowledgments.

**Claim-to-proof table (complete only after execution):**

| Claim | Proof to attach | Actual status |
|---|---|---|
| Tide login works | Recorded browser login + API token verification | NOT YET VERIFIED |
| E2EE means treasurer cannot decrypt | Tide client SDK denied result | NOT YET VERIFIED |
| Admin cannot unilaterally grant decrypt role | QEA pending/commit evidence | NOT YET VERIFIED |
| Invalid transaction cannot obtain Tide authorization | Real Forseti rejection and policy ID | NOT YET VERIFIED |
| Tampered signature cannot settle | Gateway test logs and signed bytes | NOT YET VERIFIED |
| Concurrent fund use not double-spent | Test output / DB row invariants | NOT YET VERIFIED |

**Submission checklist:**

- [ ] Repo public, code and all required files committed.
- [ ] `.codex/config.toml`, `.agents/mcp_config.json` included and readable (no credentials).
- [ ] `AGENTS.md` included for both agents.
- [ ] README project overview <=300 English words and answers all 5 rubric criteria.
- [ ] Setup actually tested from a fresh clone.
- [ ] Demos real Tide security boundary or explicitly discloses incomplete work.
- [ ] `demo.mp4` <=2 minutes and <100MB saved in repo.
- [ ] Attack scripts easy to execute; evidence saved without secrets.
- [ ] Team naming and Kaggle/Google Form instructions reconfirmed at venue; repo URL submitted.

---

## 16. REFERENCES — VERIFIED OFFICIAL MATERIAL

1. Tide UNLOCKED Challenge 2: https://tide.org/unlocked
2. Tide Raziel MCP official setup/playbooks: https://docs.tide.org/ai-agent-pack
3. Tide Raziel source: https://github.com/tide-foundation/raziel-mcp
4. OpenAI Codex MCP configuration (TOML): https://learn.chatgpt.com/docs/extend/mcp?surface=cli
5. Google Antigravity MCP configuration (`serverUrl`): https://antigravity.google/docs/mcp
6. Google Antigravity project rules / `AGENTS.md`: https://antigravity.google/docs/rules/
7. Codex `AGENTS.md`: https://learn.chatgpt.com/docs/agent-configuration/agents-md
8. TideCloak Quickstart/runtime: https://docs.tide.org/get-started/Tidecloak%20Quickstart
9. Tide E2EE setup: https://docs.tide.org/Admin/e2ee
10. Tide Forseti policies: https://docs.tide.org/Core-Concepts/forseti-engine
11. NestJS: https://docs.nestjs.com/
12. Prisma: https://www.prisma.io/docs/

### Notes on provenance and limitations

- Deadline, 5-criterion rubric and submission details originate from the challenge brief supplied by the team. Host answers on Kaggle emphasize an **idea-led hackathon**, clear README/demo, and repository review. The technical plan above is an engineering proposal, not an official Tide reference implementation.
- MCP config syntax above was independently checked against current **Codex** and **Antigravity** documentation; some examples on Tide's MCP page show older Codex config syntax. Prefer first-party docs for each client's installed version.
- No live MCP, Tide realm, Forseti contract or gateway was run as part of writing this document. Actual features must pass gates before being marked operational.

**Final guiding rule:** Ship a small, credible product that proves a new cooperation model and one unforgeable Tide trust boundary; never trade technical honesty for extra-looking features.
