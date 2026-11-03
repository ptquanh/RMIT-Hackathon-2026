import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { AddressInfo } from "node:net";
import { sha256Canonical, type CanonicalTransaction } from "@trustvault/contracts";
import { createGatewayServer } from "./app";

async function withServer<T>(callback: (baseUrl: string) => Promise<T>): Promise<T> {
  const server = createGatewayServer().listen(0);
  await new Promise<void>((resolve) => server.once("listening", resolve));
  const { port } = server.address() as AddressInfo;
  try {
    return await callback(`http://127.0.0.1:${port}`);
  } finally {
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
}

async function post(baseUrl: string, path: string, body: unknown) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { status: response.status, body: await response.json() as Record<string, unknown> };
}

function payload(): CanonicalTransaction {
  return {
    schemaVersion: "1",
    vaultId: "vault-student-relief",
    requestId: "req-test",
    currency: "VND",
    amount: "12000000",
    category: "MEDICAL",
    recipientRef: "hospital-demo-01",
    allocations: [],
    policyVersion: "1",
    nonce: "nonce-test",
    expiresAt: new Date(Date.now() + 60_000).toISOString(),
  };
}

describe("simulation gateway", () => {
  it("accepts once and rejects replay", async () => {
    await withServer(async (baseUrl) => {
      const canonicalPayload = payload();
      const body = {
        canonicalPayload,
        expectedHash: sha256Canonical(canonicalPayload),
        approvalOrganizations: ["org-a", "org-b"],
      };
      assert.equal((await post(baseUrl, "/simulation/settlements", body)).status, 201);
      const replay = await post(baseUrl, "/simulation/settlements", body);
      assert.equal(replay.status, 409);
      assert.equal(replay.body.code, "REPLAY");
    });
  });

  it("rejects a changed recipient against the approved digest", async () => {
    await withServer(async (baseUrl) => {
      const original = payload();
      const tampered = { ...original, recipientRef: "attacker-wallet" };
      const response = await post(baseUrl, "/simulation/settlements", {
        canonicalPayload: tampered,
        expectedHash: sha256Canonical(original),
        approvalOrganizations: ["org-a", "org-b"],
      });
      assert.equal(response.status, 403);
      assert.equal(response.body.code, "PAYLOAD_TAMPERED");
    });
  });

  it("keeps the real authorization route disabled", async () => {
    await withServer(async (baseUrl) => {
      const response = await post(baseUrl, "/settlements", {});
      assert.equal(response.status, 503);
      assert.equal(response.body.tideVerified, false);
    });
  });
});
