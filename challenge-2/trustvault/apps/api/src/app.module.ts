import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { APP_GUARD } from "@nestjs/core";
import { AppController } from "./app.controller";
import { SimulationAuthGuard } from "./auth/simulation-auth.guard";
import { PrismaService } from "./prisma.service";
import { TrustVaultService } from "./trustvault.service";

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true })],
  controllers: [AppController],
  providers: [
    PrismaService,
    TrustVaultService,
    { provide: APP_GUARD, useClass: SimulationAuthGuard },
  ],
})
export class AppModule {}
