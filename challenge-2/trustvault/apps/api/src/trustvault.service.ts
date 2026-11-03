import {
  BadRequestException,
  ConflictException,
  Inject,
  Injectable,
  NotFoundException,
} from "@nestjs/common";
import { Prisma, type FundingCategory } from "@prisma/client";
import {
  canonicalize,
  sha256Canonical,
  type CanonicalTransaction,
  type DemoPrincipal,
  type SimulationDisclosure,
} from "@trustvault/contracts";
import { randomUUID } from "node:crypto";
import { PrismaService } from "./prisma.service";
import { matchContributions, InsufficientEligibleFundsError } from "./matching";
import type { CreateFundingRequestDto, TamperDto } from "./dto";

const simulationDisclosure: SimulationDisclosure = {
  mode: "simulation",
  tideVerified: false,
  message: "Application simulation only. No TideCloak realm, DPoP proof, QEA decision, or Forseti signature was verified.",
};

function jsonSafe<T>(value: T): T {
  return JSON.parse(JSON.stringify(value, (_key, child) => (typeof child === "bigint" ? child.toString() : child)));
}

@Injectable()
export class TrustVaultService {
  constructor(@Inject(PrismaService) private readonly prisma: PrismaService) {}

  async dashboard() {
    const vault = await this.prisma.vault.findUnique({
      where: { id: "vault-student-relief" },
      include: {
        contributions: { include: { donorOrg: true }, orderBy: { id: "asc" } },
        requests: { orderBy: { createdAt: "desc" }, take: 8 },
      },
    });
    if (!vault) throw new NotFoundException("Seed the database first.");
    const totals = vault.contributions.reduce(
      (sum, item) => ({
        committed: sum.committed + item.originalAmount,
        available: sum.available + item.availableAmount - item.reservedAmount,
        reserved: sum.reserved + item.reservedAmount,
      }),
      { committed: 0n, available: 0n, reserved: 0n },
    );
    return jsonSafe({ vault, totals, security: simulationDisclosure });
  }

  async getRequest(id: string) {
    const request = await this.prisma.fundingRequest.findUnique({
      where: { id },
      include: {
        allocations: { include: { contribution: { include: { donorOrg: true } } } },
        approvals: { include: { signerOrg: true }, orderBy: { approvedAt: "asc" } },
        settlement: true,
        auditEvents: { orderBy: { createdAt: "asc" } },
      },
    });
    if (!request) throw new NotFoundException("Funding request not found.");
    return jsonSafe({ request, security: simulationDisclosure });
  }

  async createRequest(dto: CreateFundingRequestDto, principal: DemoPrincipal) {
    const amount = BigInt(dto.amount);
    if (amount <= 0n) throw new BadRequestException("Amount must be a positive integer VND value.");
    const id = `req-${randomUUID().slice(0, 8)}`;
    const request = await this.prisma.fundingRequest.create({
      data: {
        id,
        vaultId: "vault-student-relief",
        beneficiaryRef: principal.id,
        category: dto.category,
        amount,
        recipientRef: dto.recipientRef,
        nonce: `${id}-v1-once`,
        expiresAt: new Date(Date.now() + 60 * 60 * 1000),
        verificationComplete: dto.verificationComplete,
        auditEvents: {
          create: {
            actorId: principal.id,
            action: "REQUEST_CREATED",
            metadata: { category: dto.category, amount: dto.amount },
          },
        },
      },
    });
    return jsonSafe({ request, security: simulationDisclosure });
  }

  async preview(id: string) {
    const request = await this.prisma.fundingRequest.findUnique({ where: { id } });
    if (!request) throw new NotFoundException("Funding request not found.");
    const contributions = await this.prisma.contribution.findMany({ where: { vaultId: request.vaultId } });
    try {
      const allocations = matchContributions(
        contributions as Parameters<typeof matchContributions>[0],
        request.category,
        request.amount,
        request.verificationComplete,
      );
      return jsonSafe({ allocations, total: request.amount, reservationCreated: false, security: simulationDisclosure });
    } catch (error) {
      if (error instanceof InsufficientEligibleFundsError) {
        throw new BadRequestException({ code: error.code, message: error.message });
      }
      throw error;
    }
  }

  async submit(id: string, principal: DemoPrincipal) {
    return this.prisma.$transaction(
      async (tx) => {
        const request = await tx.fundingRequest.findUnique({ where: { id } });
        if (!request) throw new NotFoundException("Funding request not found.");
        if (request.status !== "DRAFT") throw new ConflictException("Only a draft request can be submitted.");

        const contributions = await tx.contribution.findMany({ where: { vaultId: request.vaultId } });
        let allocations;
        try {
          allocations = matchContributions(
            contributions as Parameters<typeof matchContributions>[0],
            request.category,
            request.amount,
            request.verificationComplete,
          );
        } catch (error) {
          if (error instanceof InsufficientEligibleFundsError) {
            throw new BadRequestException({ code: error.code, message: error.message });
          }
          throw error;
        }

        for (const allocation of allocations) {
          const changed = await tx.$executeRaw`
            UPDATE "Contribution"
            SET "reservedAmount" = "reservedAmount" + ${allocation.amount}
            WHERE "id" = ${allocation.contributionId}
              AND ("availableAmount" - "reservedAmount") >= ${allocation.amount}
          `;
          if (changed !== 1) throw new ConflictException("Contribution was reserved by another request. Retry preview.");
        }

        await tx.allocation.createMany({
          data: allocations.map((allocation) => ({
            fundingRequestId: id,
            contributionId: allocation.contributionId,
            amount: allocation.amount,
          })),
        });

        const canonicalPayload: CanonicalTransaction = {
          schemaVersion: "1",
          vaultId: request.vaultId,
          requestId: request.id,
          currency: "VND",
          amount: request.amount.toString(),
          category: request.category,
          recipientRef: request.recipientRef,
          allocations: allocations.map((allocation) => ({
            contributionId: allocation.contributionId,
            amount: allocation.amount.toString(),
            conditionsHash: allocation.conditionsHash,
          })),
          policyVersion: request.policyVersion,
          nonce: request.nonce,
          expiresAt: request.expiresAt.toISOString(),
        };
        const payloadHash = sha256Canonical(canonicalPayload);

        const updated = await tx.fundingRequest.update({
          where: { id },
          data: {
            status: "PENDING_REVIEW",
            canonicalPayload: canonicalize(canonicalPayload),
            canonicalPayloadHash: payloadHash,
            auditEvents: {
              create: {
                actorId: principal.id,
                action: "PAYLOAD_FROZEN",
                metadata: { payloadHash },
              },
            },
          },
        });
        return jsonSafe({ request: updated, canonicalPayload, payloadHash, security: simulationDisclosure });
      },
      { isolationLevel: Prisma.TransactionIsolationLevel.Serializable },
    );
  }

  async approve(id: string, principal: DemoPrincipal) {
    if (!principal.organizationId) throw new BadRequestException("Approver must belong to an organization.");
    const organizationId = principal.organizationId;
    return this.prisma.$transaction(async (tx) => {
      const request = await tx.fundingRequest.findUnique({ where: { id }, include: { approvals: true } });
      if (!request?.canonicalPayloadHash) throw new BadRequestException("Submit and freeze the payload first.");
      if (!["PENDING_REVIEW", "READY_TO_AUTHORIZE"].includes(request.status)) {
        throw new ConflictException("Request is not accepting approvals.");
      }
      if (request.approvals.some((approval) => approval.signerOrgId === organizationId)) {
        throw new ConflictException("This organization already approved the request.");
      }
      await tx.approval.create({
        data: {
          fundingRequestId: id,
          signerId: principal.id,
          signerOrgId: organizationId,
          payloadHash: request.canonicalPayloadHash,
          decision: "APPROVE",
        },
      });
      const approvalCount = request.approvals.length + 1;
      const updated = await tx.fundingRequest.update({
        where: { id },
        data: {
          status: approvalCount >= 2 ? "READY_TO_AUTHORIZE" : "PENDING_REVIEW",
          auditEvents: {
            create: {
              actorId: principal.id,
              action: "APPLICATION_APPROVAL_RECORDED",
              metadata: { organizationId, payloadHash: request.canonicalPayloadHash },
            },
          },
        },
      });
      return jsonSafe({ request: updated, approvalCount, security: simulationDisclosure });
    });
  }

  async simulateAuthorization(id: string) {
    const request = await this.prisma.fundingRequest.findUnique({ where: { id }, include: { approvals: true } });
    if (!request?.canonicalPayloadHash || request.status !== "READY_TO_AUTHORIZE") {
      throw new BadRequestException({ code: "QUORUM_NOT_MET", message: "Two distinct application approvals are required." });
    }
    return {
      acceptedByApplicationSimulation: true,
      payloadHash: request.canonicalPayloadHash,
      approvalOrganizations: [...new Set(request.approvals.map((item) => item.signerOrgId))],
      security: simulationDisclosure,
    };
  }

  async tamper(id: string, dto: TamperDto) {
    const request = await this.prisma.fundingRequest.findUnique({ where: { id } });
    if (!request?.canonicalPayload || !request.canonicalPayloadHash) {
      throw new BadRequestException("Submit and freeze the payload first.");
    }
    const original = JSON.parse(request.canonicalPayload) as CanonicalTransaction;
    const changed = { ...original, recipientRef: dto.recipientRef };
    const changedHash = sha256Canonical(changed);
    return {
      denied: changedHash !== request.canonicalPayloadHash,
      expectedHash: request.canonicalPayloadHash,
      receivedHash: changedHash,
      reason: "The changed recipient produces a different digest, so existing application approvals no longer match.",
      security: simulationDisclosure,
    };
  }

  async simulateSettlement(id: string) {
    const request = await this.prisma.fundingRequest.findUnique({
      where: { id },
      include: { approvals: true, allocations: true, settlement: true },
    });
    if (!request?.canonicalPayload || !request.canonicalPayloadHash) throw new BadRequestException("No frozen payload.");
    if (request.settlement) throw new ConflictException({ code: "REPLAY", message: "Request already settled once." });
    if (request.status !== "READY_TO_AUTHORIZE" || new Set(request.approvals.map((item) => item.signerOrgId)).size < 2) {
      throw new BadRequestException({ code: "QUORUM_NOT_MET", message: "Application approval quorum is incomplete." });
    }

    const response = await fetch(`${process.env.MOCK_GATEWAY_URL ?? "http://localhost:3002"}/simulation/settlements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        canonicalPayload: JSON.parse(request.canonicalPayload),
        expectedHash: request.canonicalPayloadHash,
        approvalOrganizations: [...new Set(request.approvals.map((item) => item.signerOrgId))],
      }),
    });
    const result = (await response.json()) as { receiptId?: string; error?: string };
    if (!response.ok || !result.receiptId) throw new BadRequestException(result);
    const receiptId = result.receiptId;

    await this.prisma.$transaction(async (tx) => {
      for (const allocation of request.allocations) {
        await tx.contribution.update({
          where: { id: allocation.contributionId },
          data: {
            reservedAmount: { decrement: allocation.amount },
            availableAmount: { decrement: allocation.amount },
            spentAmount: { increment: allocation.amount },
          },
        });
      }
      await tx.settlement.create({
        data: {
          fundingRequestId: id,
          idempotencyKey: request.nonce,
          receiptId,
          mode: "APPLICATION_SIMULATION_ONLY",
        },
      });
      await tx.fundingRequest.update({
        where: { id },
        data: {
          status: "SETTLED",
          auditEvents: {
            create: { actorId: "mock-gateway", action: "SIMULATED_SETTLEMENT_RECORDED", metadata: { receiptId } },
          },
        },
      });
    });
    return { ...result, security: simulationDisclosure };
  }
}
