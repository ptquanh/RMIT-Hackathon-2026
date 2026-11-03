import { createHash } from "node:crypto";

export const fundingCategories = ["MEDICAL", "TUITION", "HOUSING"] as const;
export type FundingCategory = (typeof fundingCategories)[number];

export type RequestStatus =
  | "DRAFT"
  | "PENDING_REVIEW"
  | "READY_TO_AUTHORIZE"
  | "AUTHORIZED"
  | "SETTLED"
  | "REJECTED"
  | "EXPIRED";

export interface CanonicalAllocation {
  contributionId: string;
  amount: string;
  conditionsHash: string;
}

export interface CanonicalTransaction {
  schemaVersion: "1";
  vaultId: string;
  requestId: string;
  currency: "VND";
  amount: string;
  category: FundingCategory;
  recipientRef: string;
  allocations: CanonicalAllocation[];
  policyVersion: string;
  nonce: string;
  expiresAt: string;
}

export interface DemoPrincipal {
  id: string;
  displayName: string;
  organizationId: string | null;
  roles: string[];
}

export interface SimulationDisclosure {
  mode: "simulation";
  tideVerified: false;
  message: string;
}

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, normalize(child)]),
    );
  }
  if (typeof value === "bigint") return value.toString();
  return value;
}

/** Stable UTF-8 JSON shared by the API and gateway. */
export function canonicalize(value: unknown): string {
  return JSON.stringify(normalize(value));
}

export function sha256Canonical(value: unknown): string {
  return `sha256:${createHash("sha256").update(canonicalize(value), "utf8").digest("hex")}`;
}

export function formatVnd(value: bigint | string | number): string {
  return `${BigInt(value).toLocaleString("vi-VN")} ₫`;
}
