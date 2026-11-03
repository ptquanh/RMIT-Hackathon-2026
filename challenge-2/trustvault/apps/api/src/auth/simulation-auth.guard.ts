import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Inject,
  Injectable,
  ServiceUnavailableException,
  UnauthorizedException,
} from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import type { Request } from "express";
import type { DemoPrincipal } from "@trustvault/contracts";
import { IS_PUBLIC_KEY, ROLES_KEY } from "./auth.decorators";

export const demoPrincipals: Record<string, DemoPrincipal> = {
  beneficiary: { id: "beneficiary-1", displayName: "Minh — beneficiary", organizationId: null, roles: ["beneficiary"] },
  treasurer: { id: "treasurer-1", displayName: "Lan — treasurer", organizationId: "org-a", roles: ["treasurer"] },
  approverA: { id: "approver-a", displayName: "Ari — Org A approver", organizationId: "org-a", roles: ["approver"] },
  approverB: { id: "approver-b", displayName: "Bao — Org B approver", organizationId: "org-b", roles: ["approver"] },
  reviewer: { id: "reviewer-1", displayName: "Chi — independent reviewer", organizationId: "org-c", roles: ["reviewer"] },
  auditor: { id: "auditor-1", displayName: "Dee — auditor", organizationId: null, roles: ["auditor"] },
};

export type AuthenticatedRequest = Request & { principal: DemoPrincipal };

@Injectable()
export class SimulationAuthGuard implements CanActivate {
  constructor(@Inject(Reflector) private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    if ((process.env.AUTH_MODE ?? "simulation") !== "simulation") {
      throw new ServiceUnavailableException(
        "Real Tide auth is not enabled. Recover/provision the realm and wire the official verifier before changing AUTH_MODE.",
      );
    }

    const request = context.switchToHttp().getRequest<AuthenticatedRequest>();
    const identity = request.header("x-demo-user");
    const principal = identity ? demoPrincipals[identity] : undefined;
    if (!principal) throw new UnauthorizedException("Select a valid demo identity using x-demo-user.");

    const requiredRoles = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (requiredRoles?.length && !requiredRoles.some((role) => principal.roles.includes(role))) {
      throw new ForbiddenException("Demo identity lacks the required role.");
    }

    request.principal = principal;
    return true;
  }
}
