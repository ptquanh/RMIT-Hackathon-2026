import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { SimulationAuthGuard } from "./auth/simulation-auth.guard";

function context(identity?: string): ExecutionContext {
  const request = {
    header(name: string) {
      return name === "x-demo-user" ? identity : undefined;
    },
  };

  return {
    getHandler: () => function handler() {},
    getClass: () => class Controller {},
    switchToHttp: () => ({ getRequest: () => request }),
  } as unknown as ExecutionContext;
}

function reflector(requiredRoles?: string[]): Reflector {
  return {
    getAllAndOverride(key: string) {
      if (key === "isPublic") return false;
      if (key === "roles") return requiredRoles;
      return undefined;
    },
  } as unknown as Reflector;
}

describe("simulation auth boundary", () => {
  it("returns 401 when no demo session identity is supplied", () => {
    const guard = new SimulationAuthGuard(reflector());
    assert.throws(() => guard.canActivate(context()), (error: any) => error.getStatus() === 401);
  });

  it("returns 403 when an authenticated identity lacks the server-required role", () => {
    const guard = new SimulationAuthGuard(reflector(["treasurer"]));
    assert.throws(
      () => guard.canActivate(context("beneficiary")),
      (error: any) => error.getStatus() === 403,
    );
  });

  it("attaches the server-owned principal when its role is allowed", () => {
    const guard = new SimulationAuthGuard(reflector(["approver"]));
    const executionContext = context("approverA");
    assert.equal(guard.canActivate(executionContext), true);
    const request = executionContext.switchToHttp().getRequest() as any;
    assert.equal(request.principal.organizationId, "org-a");
    assert.deepEqual(request.principal.roles, ["approver"]);
  });
});
