[![Built with TideCloak](https://tide.org/badges/built-with-tidecloak.svg)](https://tide.org/tidecloak?utm_source=github&utm_medium=readme&utm_campaign=unlocked)

# TrustVault

*TrustVault lets independent funders combine purpose-bound contributions for one exact transaction without making any single organisation the owner of everyone else's trust.*

## Project overview

### 1. Vision & originality

TrustVault is a conditional funding network. Instead of sending unrestricted money to a central intermediary, organisations contribute funds with explicit covenants. A deterministic engine assembles compatible contributions into one immutable transaction.

### 2. Trust constraint insight

Cross-organisation funding normally requires one operator to control balances, beneficiary evidence, permissions and release. That administrator can become a shortcut around every donor condition. TrustVault separates proposal, verification, approval and settlement, then binds approvals to one canonical payload digest.

### 3. Value & impact

A student needing VND 12 million in medical support can be funded by three organisations with different restrictions. Each contributor retains its conditions while the beneficiary avoids exposing every private document to every donor.

### 4. Why TideCloak matters

The design places identity, protected evidence and governed role changes behind TideCloak. The official Tide scaffold, DPoP relay and server verifier are included. Our local realm currently cannot complete `Midgard.FinalizeWallet`, so authentication and roles are visibly simulated under organiser guidance. No Tide/Forseti security outcome is claimed yet.

### 5. Prototype & storytelling

The prototype starts with an explicit demo sign-in, then matches A=5M, B=5M and C=2M, freezes the payload, records approvals from distinct organisations, denies unauthorised and recipient-tampering attempts, and produces a one-time simulated gateway receipt.

## Current status

This prototype uses **simulated money** and **simulation authentication**. Real Tide login, E2EE, QEA and Forseti authorization remain disabled until a realm is recovered and a custom signing contract is deployed by Tide. See [security evidence](docs/security-evidence.md).

## Setup

Requirements: Node.js 20.9+, npm, Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up -d postgres
npm install
npm run db:generate
npm run db:push
npm run prisma:seed -w @trustvault/api
```

Run these in three terminals:

```bash
npm run dev:api
npm run dev:gateway
npm run dev:web
```

Open <http://localhost:3000>, sign in as the beneficiary, and click **Start the 12M demo**. Use the identity switcher to approve once as Org A, once as Org B, then settle as the treasurer. The switcher is a visible simulation seam that will be replaced by TideCloak redirect/token handling.

Simulation roles are resolved by the API, not accepted from request bodies:

- `beneficiary`: create, preview and submit a request;
- `approverA` / `approverB`: approve only for their server-mapped organisation;
- `treasurer`: submit, inspect controls and simulate settlement;
- `auditor`: inspect and run non-settlement security checks;
- `reviewer`: reserved for the future protected-evidence flow.

Missing identity returns `401`; an authenticated identity with the wrong role returns `403`.

## Verification

```bash
npm test
npm run build
```

The real gateway route `POST /settlements` deliberately returns `503 TIDE_AUTHORIZATION_NOT_CONFIGURED`. Only `/simulation/settlements` is active.

## Architecture

- `apps/web`: Next.js demo and preserved official Tide scaffold assets.
- `apps/api`: NestJS, Prisma, deterministic matching, reservations and approvals.
- `packages/contracts`: canonical JSON and shared transaction contracts.
- `services/mock-gateway`: isolated, replay-safe simulation ledger.
- `tide/forseti`: deployment status and handoff notes; no fabricated contract deployment.

## Security non-goals

- No banking, custody, KYC/AML or real transfer.
- Application approvals are not cryptographic Tide approvals.
- Local database audit events are not immutable.
- Hash comparison detects payload changes but does not replace a trusted signature.
- An authorised evidence recipient could copy plaintext after legitimate decryption.
