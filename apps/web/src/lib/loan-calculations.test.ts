import { describe, expect, it } from "vitest";
import { calculateEligibility, calculateEmi } from "@/lib/loan-calculations";

describe("calculateEmi", () => {
  it("matches a known EMI calculation", () => {
    // ₹1,00,000 at 10% p.a. for 12 months is a widely-published reference
    // value (~₹8,792/month) for this formula.
    const result = calculateEmi(100_000, 10, 12);
    expect(result.emi).toBeCloseTo(8792, 0);
    expect(result.totalPayment).toBeCloseTo(result.emi * 12, 5);
    expect(result.totalInterest).toBeCloseTo(result.totalPayment - 100_000, 5);
  });

  it("splits the principal evenly at 0% interest", () => {
    const result = calculateEmi(120_000, 0, 12);
    expect(result.emi).toBeCloseTo(10_000, 5);
    expect(result.totalInterest).toBe(0);
    expect(result.totalPayment).toBeCloseTo(120_000, 5);
  });

  it("increases EMI as tenure shortens for the same principal and rate", () => {
    const shortTenure = calculateEmi(500_000, 12, 24);
    const longTenure = calculateEmi(500_000, 12, 60);
    expect(shortTenure.emi).toBeGreaterThan(longTenure.emi);
  });

  it("rejects a non-positive principal", () => {
    expect(() => calculateEmi(0, 10, 12)).toThrow(RangeError);
    expect(() => calculateEmi(-100, 10, 12)).toThrow(RangeError);
  });

  it("rejects a negative interest rate", () => {
    expect(() => calculateEmi(100_000, -1, 12)).toThrow(RangeError);
  });

  it("rejects a non-positive tenure", () => {
    expect(() => calculateEmi(100_000, 10, 0)).toThrow(RangeError);
  });
});

describe("calculateEligibility", () => {
  it("estimates a maximum loan amount within the FOIR ceiling", () => {
    const result = calculateEligibility({
      netMonthlyIncome: 100_000,
      existingMonthlyObligations: 10_000,
      annualRatePercent: 10,
      tenureMonths: 60,
    });

    // 50% FOIR of 100k = 50k ceiling, minus 10k existing obligations.
    expect(result.maxAffordableEmi).toBeCloseTo(40_000, 5);
    expect(result.maxLoanAmount).toBeGreaterThan(0);

    // The resulting loan amount, run back through calculateEmi, should
    // reproduce (approximately) the same affordable EMI.
    const reconstructed = calculateEmi(result.maxLoanAmount, 10, 60);
    expect(reconstructed.emi).toBeCloseTo(result.maxAffordableEmi, 1);
  });

  it("returns zero eligibility when obligations meet or exceed the FOIR ceiling", () => {
    const result = calculateEligibility({
      netMonthlyIncome: 50_000,
      existingMonthlyObligations: 30_000,
      annualRatePercent: 10,
      tenureMonths: 60,
      foirPercent: 50,
    });

    expect(result.maxAffordableEmi).toBe(0);
    expect(result.maxLoanAmount).toBe(0);
  });

  it("honors a custom FOIR percentage", () => {
    const conservative = calculateEligibility({
      netMonthlyIncome: 100_000,
      existingMonthlyObligations: 0,
      annualRatePercent: 10,
      tenureMonths: 60,
      foirPercent: 30,
    });
    const lenient = calculateEligibility({
      netMonthlyIncome: 100_000,
      existingMonthlyObligations: 0,
      annualRatePercent: 10,
      tenureMonths: 60,
      foirPercent: 55,
    });

    expect(lenient.maxLoanAmount).toBeGreaterThan(conservative.maxLoanAmount);
  });

  it("handles a 0% assumed interest rate", () => {
    const result = calculateEligibility({
      netMonthlyIncome: 60_000,
      existingMonthlyObligations: 0,
      annualRatePercent: 0,
      tenureMonths: 24,
      foirPercent: 50,
    });
    expect(result.maxLoanAmount).toBeCloseTo(30_000 * 24, 5);
  });

  it("rejects an out-of-range FOIR percentage", () => {
    expect(() =>
      calculateEligibility({
        netMonthlyIncome: 60_000,
        existingMonthlyObligations: 0,
        annualRatePercent: 10,
        tenureMonths: 24,
        foirPercent: 0,
      }),
    ).toThrow(RangeError);
    expect(() =>
      calculateEligibility({
        netMonthlyIncome: 60_000,
        existingMonthlyObligations: 0,
        annualRatePercent: 10,
        tenureMonths: 24,
        foirPercent: 101,
      }),
    ).toThrow(RangeError);
  });
});
