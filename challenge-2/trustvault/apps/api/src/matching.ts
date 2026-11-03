import type { FundingCategory } from "@trustvault/contracts";

export interface MatchableContribution {
  id: string;
  availableAmount: bigint;
  reservedAmount: bigint;
  maxPerRequestAmount: bigint | null;
  allowedCategories: FundingCategory[];
  requiresIndependentVerification: boolean;
  deadlineAt: Date | null;
  conditionsHash: string;
}

export interface MatchAllocation {
  contributionId: string;
  amount: bigint;
  conditionsHash: string;
}

export class InsufficientEligibleFundsError extends Error {
  code = "INSUFFICIENT_ELIGIBLE_FUNDS";
  constructor(public readonly missingAmount: bigint) {
    super(`Insufficient eligible funds; missing ${missingAmount.toString()} VND.`);
  }
}

export function matchContributions(
  contributions: MatchableContribution[],
  category: FundingCategory,
  requestedAmount: bigint,
  verificationComplete: boolean,
  now = new Date(),
): MatchAllocation[] {
  let remaining = requestedAmount;
  const allocations: MatchAllocation[] = [];

  const eligible = contributions
    .filter((item) => item.allowedCategories.includes(category))
    .filter((item) => !item.deadlineAt || item.deadlineAt > now)
    .filter((item) => !item.requiresIndependentVerification || verificationComplete)
    .sort((left, right) => {
      const leftDeadline = left.deadlineAt?.getTime() ?? Number.MAX_SAFE_INTEGER;
      const rightDeadline = right.deadlineAt?.getTime() ?? Number.MAX_SAFE_INTEGER;
      return leftDeadline - rightDeadline || left.id.localeCompare(right.id);
    });

  for (const contribution of eligible) {
    const unreserved = contribution.availableAmount - contribution.reservedAmount;
    const perRequest = contribution.maxPerRequestAmount ?? unreserved;
    const usable = unreserved < perRequest ? unreserved : perRequest;
    const amount = usable < remaining ? usable : remaining;
    if (amount > 0n) {
      allocations.push({
        contributionId: contribution.id,
        amount,
        conditionsHash: contribution.conditionsHash,
      });
      remaining -= amount;
    }
    if (remaining === 0n) return allocations;
  }

  throw new InsufficientEligibleFundsError(remaining);
}
