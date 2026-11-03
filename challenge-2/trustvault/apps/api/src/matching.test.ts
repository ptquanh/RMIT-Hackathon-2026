import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { InsufficientEligibleFundsError, matchContributions } from "./matching";

const contributions = [
  {
    id: "contribution-a",
    availableAmount: 5_000_000n,
    reservedAmount: 0n,
    maxPerRequestAmount: 5_000_000n,
    allowedCategories: ["MEDICAL" as const],
    requiresIndependentVerification: false,
    deadlineAt: null,
    conditionsHash: "a",
  },
  {
    id: "contribution-b",
    availableAmount: 8_000_000n,
    reservedAmount: 0n,
    maxPerRequestAmount: 5_000_000n,
    allowedCategories: ["MEDICAL" as const, "TUITION" as const],
    requiresIndependentVerification: false,
    deadlineAt: null,
    conditionsHash: "b",
  },
  {
    id: "contribution-c",
    availableAmount: 4_000_000n,
    reservedAmount: 0n,
    maxPerRequestAmount: 4_000_000n,
    allowedCategories: ["MEDICAL" as const],
    requiresIndependentVerification: true,
    deadlineAt: null,
    conditionsHash: "c",
  },
];

describe("deterministic matching", () => {
  it("matches the 12M medical scenario as A=5M, B=5M, C=2M", () => {
    assert.deepEqual(matchContributions(contributions, "MEDICAL", 12_000_000n, true), [
      { contributionId: "contribution-a", amount: 5_000_000n, conditionsHash: "a" },
      { contributionId: "contribution-b", amount: 5_000_000n, conditionsHash: "b" },
      { contributionId: "contribution-c", amount: 2_000_000n, conditionsHash: "c" },
    ]);
  });

  it("excludes independently verified funds until verification is complete", () => {
    assert.throws(
      () => matchContributions(contributions, "MEDICAL", 12_000_000n, false),
      InsufficientEligibleFundsError,
    );
  });
});
