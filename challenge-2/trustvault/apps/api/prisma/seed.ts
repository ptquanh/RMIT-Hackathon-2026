import { PrismaClient } from "@prisma/client";
import { sha256Canonical } from "@trustvault/contracts";

const prisma = new PrismaClient();

async function main() {
  await prisma.settlement.deleteMany();
  await prisma.approval.deleteMany();
  await prisma.allocation.deleteMany();
  await prisma.auditEvent.deleteMany();
  await prisma.fundingRequest.deleteMany();
  await prisma.contribution.deleteMany();
  await prisma.vault.deleteMany();
  await prisma.organization.deleteMany();

  await prisma.organization.createMany({
    data: [
      { id: "org-a", name: "RMIT Relief Fund" },
      { id: "org-b", name: "Taylor Community Foundation" },
      { id: "org-c", name: "Independent Care Network" },
    ],
  });

  await prisma.vault.create({
    data: {
      id: "vault-student-relief",
      name: "Student Relief Vault",
      purpose: "Cross-organisation emergency support with purpose-bound contributions",
      policyVersion: "1",
      contributions: {
        create: [
          {
            id: "contribution-a",
            donorOrgId: "org-a",
            label: "Medical response grant",
            originalAmount: 5_000_000n,
            availableAmount: 5_000_000n,
            maxPerRequestAmount: 5_000_000n,
            allowedCategories: ["MEDICAL"],
            requiresIndependentVerification: false,
            conditionsHash: sha256Canonical({ categories: ["MEDICAL"], max: "5000000" }),
          },
          {
            id: "contribution-b",
            donorOrgId: "org-b",
            label: "Student continuity fund",
            originalAmount: 8_000_000n,
            availableAmount: 8_000_000n,
            maxPerRequestAmount: 5_000_000n,
            allowedCategories: ["MEDICAL", "TUITION"],
            requiresIndependentVerification: false,
            conditionsHash: sha256Canonical({ categories: ["MEDICAL", "TUITION"], maxPerRequest: "5000000" }),
          },
          {
            id: "contribution-c",
            donorOrgId: "org-c",
            label: "Verified care partnership",
            originalAmount: 4_000_000n,
            availableAmount: 4_000_000n,
            maxPerRequestAmount: 4_000_000n,
            allowedCategories: ["MEDICAL"],
            requiresIndependentVerification: true,
            conditionsHash: sha256Canonical({ categories: ["MEDICAL"], verification: "independent" }),
          },
        ],
      },
    },
  });
}

main()
  .then(() => console.log("TrustVault demo data seeded."))
  .finally(() => prisma.$disconnect());
