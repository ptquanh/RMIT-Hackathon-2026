import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { randomUUID } from "node:crypto";
import { sha256Canonical, type CanonicalTransaction } from "@trustvault/contracts";

interface SimulationRequest {
  canonicalPayload: CanonicalTransaction;
  expectedHash: string;
  approvalOrganizations: string[];
}

function send(response: ServerResponse, status: number, body: Record<string, unknown>) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

async function readJson(request: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    size += buffer.length;
    if (size > 100_000) throw new Error("Request body is too large.");
    chunks.push(buffer);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}") as Record<string, unknown>;
}

export function createGatewayServer() {
  const receipts = new Map<string, string>();
  return createServer(async (request, response) => {
    try {
      if (request.method === "GET" && request.url === "/health") {
        return send(response, 200, { status: "ok", mode: "application-simulation", tideVerified: false });
      }
      if (request.method === "POST" && request.url === "/settlements") {
        return send(response, 503, {
          code: "TIDE_AUTHORIZATION_NOT_CONFIGURED",
          message: "The real settlement route is disabled until a Tide-deployed Forseti contract is verified.",
          tideVerified: false,
        });
      }
      if (request.method !== "POST" || request.url !== "/simulation/settlements") {
        return send(response, 404, { code: "NOT_FOUND" });
      }

      const body = (await readJson(request)) as Partial<SimulationRequest>;
      const payload = body.canonicalPayload;
      if (!payload || !body.expectedHash || !Array.isArray(body.approvalOrganizations)) {
        return send(response, 400, { code: "INVALID_REQUEST", error: "Missing canonical payload, hash, or approvals." });
      }
      if (payload.currency !== "VND" || !/^[1-9][0-9]*$/.test(payload.amount)) {
        return send(response, 400, { code: "INVALID_PAYLOAD", error: "Only positive integer VND is supported." });
      }
      if (new Date(payload.expiresAt).getTime() <= Date.now()) {
        return send(response, 409, { code: "EXPIRED", error: "The frozen transaction has expired." });
      }
      if (new Set(body.approvalOrganizations).size < 2) {
        return send(response, 403, { code: "QUORUM_NOT_MET", error: "Two distinct organizations are required." });
      }
      const calculatedHash = sha256Canonical(payload);
      if (calculatedHash !== body.expectedHash) {
        return send(response, 403, {
          code: "PAYLOAD_TAMPERED",
          error: "Canonical payload digest does not match the approved digest.",
          expectedHash: body.expectedHash,
          calculatedHash,
        });
      }
      const ledgerKey = `${payload.requestId}:${payload.nonce}`;
      if (receipts.has(ledgerKey)) {
        return send(response, 409, { code: "REPLAY", error: "This nonce already produced a receipt." });
      }
      const receiptId = `sim-${randomUUID()}`;
      receipts.set(ledgerKey, receiptId);
      return send(response, 201, {
        receiptId,
        payloadHash: calculatedHash,
        mode: "APPLICATION_SIMULATION_ONLY",
        tideVerified: false,
        warning: "This receipt is not a Tide signature and represents no real transfer of funds.",
      });
    } catch (error) {
      return send(response, 400, { code: "INVALID_JSON", error: error instanceof Error ? error.message : "Invalid request." });
    }
  });
}
