import { IsBoolean, IsIn, IsOptional, IsString, Matches, MaxLength } from "class-validator";

export class CreateFundingRequestDto {
  @IsIn(["MEDICAL", "TUITION", "HOUSING"])
  category!: "MEDICAL" | "TUITION" | "HOUSING";

  @Matches(/^[1-9][0-9]*$/)
  amount!: string;

  @IsString()
  @MaxLength(120)
  recipientRef!: string;

  @IsBoolean()
  @IsOptional()
  verificationComplete = false;
}

export class ApprovalDto {
  @IsIn(["APPROVE"])
  decision!: "APPROVE";
}

export class TamperDto {
  @IsString()
  @MaxLength(120)
  recipientRef!: string;
}
