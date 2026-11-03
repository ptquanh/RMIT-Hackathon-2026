import { Body, Controller, Get, Inject, Param, Post, Req } from "@nestjs/common";
import { ApprovalDto, CreateFundingRequestDto, TamperDto } from "./dto";
import { Public, Roles } from "./auth/auth.decorators";
import { demoPrincipals, type AuthenticatedRequest } from "./auth/simulation-auth.guard";
import { TrustVaultService } from "./trustvault.service";

@Controller()
export class AppController {
  constructor(@Inject(TrustVaultService) private readonly trustVault: TrustVaultService) {}

  @Public()
  @Get("health")
  health() {
    return {
      status: "ok",
      authMode: process.env.AUTH_MODE ?? "simulation",
      tideVerified: false,
    };
  }

  @Public()
  @Get("demo-identities")
  demoIdentities() {
    return { identities: demoPrincipals, warning: "Simulation identities only; not TideCloak authority." };
  }

  @Get("auth/me")
  me(@Req() request: AuthenticatedRequest) {
    return { principal: request.principal, mode: "simulation", tideVerified: false };
  }

  @Get("dashboard")
  dashboard() {
    return this.trustVault.dashboard();
  }

  @Roles("beneficiary")
  @Post("funding-requests")
  createRequest(@Body() dto: CreateFundingRequestDto, @Req() request: AuthenticatedRequest) {
    return this.trustVault.createRequest(dto, request.principal);
  }

  @Get("funding-requests/:id")
  getRequest(@Param("id") id: string) {
    return this.trustVault.getRequest(id);
  }

  @Roles("beneficiary", "treasurer")
  @Post("funding-requests/:id/preview")
  preview(@Param("id") id: string) {
    return this.trustVault.preview(id);
  }

  @Roles("beneficiary", "treasurer")
  @Post("funding-requests/:id/submit")
  submit(@Param("id") id: string, @Req() request: AuthenticatedRequest) {
    return this.trustVault.submit(id, request.principal);
  }

  @Roles("approver")
  @Post("funding-requests/:id/approvals")
  approve(
    @Param("id") id: string,
    @Body() _dto: ApprovalDto,
    @Req() request: AuthenticatedRequest,
  ) {
    return this.trustVault.approve(id, request.principal);
  }

  @Roles("treasurer", "auditor")
  @Post("funding-requests/:id/authorize-simulation")
  authorizeSimulation(@Param("id") id: string) {
    return this.trustVault.simulateAuthorization(id);
  }

  @Roles("treasurer", "auditor")
  @Post("funding-requests/:id/tamper-demo")
  tamperDemo(@Param("id") id: string, @Body() dto: TamperDto) {
    return this.trustVault.tamper(id, dto);
  }

  @Roles("treasurer")
  @Post("funding-requests/:id/settle-simulation")
  settleSimulation(@Param("id") id: string) {
    return this.trustVault.simulateSettlement(id);
  }
}
