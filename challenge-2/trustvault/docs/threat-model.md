# TrustVault threat model

## Protected assets

- Simulated contribution balances and reservations.
- Beneficiary evidence ciphertext and metadata.
- Canonical transaction payload and approval digest.
- Identity, organisation membership and roles.
- One-time settlement nonce and receipt.

## Trust boundaries

1. Browser → API: currently a labelled demo identity header; production requires Tide JWT, roles and DPoP verification.
2. API → PostgreSQL: serializable reservations and unique constraints protect consistency, not database availability or operator tampering.
3. Browser → Tide: not operational in simulation mode; intended for identity, E2EE and governed authorization.
4. API → gateway: separate process recalculates payload digest and protects nonce replay; it does not verify Tide while Forseti is unavailable.
5. Realm administration: intended to use Tide QEA; no current proof exists.

## Principal threats and controls

- **Concurrent reservation:** serializable transaction plus conditional SQL balance update.
- **Amount rounding:** integer `BigInt` VND, decimal strings over JSON.
- **Changed recipient/amount:** approvals reference a frozen canonical digest; changed data produces another digest.
- **Replay:** unique request nonce in the durable application schema and one-time gateway ledger.
- **Self-approved quorum:** API requires two distinct organisation IDs; this is application enforcement until Forseti exists.
- **Database disclosure:** evidence endpoint is intentionally not enabled until Tide client-side encryption is verified.
- **Forged identity:** simulation mode is explicitly non-production and must never be internet-exposed as real authorization.

## Residual risks

- A compromised application/database operator can alter or erase application records.
- Simulation actors are selectable and provide no identity assurance.
- The in-memory gateway ledger resets with the service; PostgreSQL persistence is required before a production-like deployment.
- Hashing detects mismatches but does not authenticate who approved a payload.
- Enough legitimate parties can collude, and an authorised evidence reader can copy plaintext.
