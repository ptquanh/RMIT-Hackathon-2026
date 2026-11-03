# Forseti integration status

Status: **NOT DEPLOYED — fail closed**.

TrustVault requires policy-governed signing because it authorizes a canonical transaction, not merely encryption/decryption of a record. Raziel Agent Pack v1.9.33 confirms that the built-in `RelationshipAttestation:1` contract does not cover signing.

A custom contract must eventually validate at least:

- schema and exact canonical payload bytes;
- `MEDICAL` category and configured maximum amount;
- pinned vault and policy revision;
- two eligible approvers from distinct organisations;
- authorised executor and expiry.

Custom contract deployment is experimental and performed by the Tide team. This repository intentionally contains no invented upload process, policy ID, public key or mock Tide signature. Contact `info@tide.org` or the Tide Discord for review and test-network deployment.
