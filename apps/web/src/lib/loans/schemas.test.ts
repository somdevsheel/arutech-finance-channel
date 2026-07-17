import { describe, expect, it } from "vitest";
import { loanApplicationSchema } from "@/lib/loans/schemas";

describe("loanApplicationSchema", () => {
  const base = {
    loan_product_slug: "personal-loan",
    requested_amount: 200_000,
    tenure_months: 24,
    monthly_income: 50_000,
  };

  it("accepts a valid application", () => {
    expect(loanApplicationSchema.safeParse(base).success).toBe(true);
  });

  it("defaults existing_monthly_obligations to 0 when omitted", () => {
    const result = loanApplicationSchema.safeParse(base);
    expect(result.success && result.data.existing_monthly_obligations).toBe(0);
  });

  it("rejects a missing loan product", () => {
    const result = loanApplicationSchema.safeParse({ ...base, loan_product_slug: "" });
    expect(result.success).toBe(false);
  });

  it("rejects a non-positive requested amount", () => {
    const result = loanApplicationSchema.safeParse({ ...base, requested_amount: 0 });
    expect(result.success).toBe(false);
  });

  it("rejects a negative tenure", () => {
    const result = loanApplicationSchema.safeParse({ ...base, tenure_months: -12 });
    expect(result.success).toBe(false);
  });

  it("rejects a negative existing_monthly_obligations", () => {
    const result = loanApplicationSchema.safeParse({
      ...base,
      existing_monthly_obligations: -1,
    });
    expect(result.success).toBe(false);
  });
});
