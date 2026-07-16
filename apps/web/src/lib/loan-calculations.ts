export interface EmiBreakdown {
  emi: number;
  totalInterest: number;
  totalPayment: number;
}

function assertPositiveFinite(value: number, name: string): void {
  if (!Number.isFinite(value) || value <= 0) {
    throw new RangeError(`${name} must be a positive number`);
  }
}

/**
 * Standard reducing-balance EMI formula:
 * EMI = P * r * (1+r)^n / ((1+r)^n - 1), where r is the *monthly* rate.
 * Falls back to a straight-line split when annualRatePercent is 0, since
 * the formula above divides by zero at r = 0.
 */
export function calculateEmi(
  principal: number,
  annualRatePercent: number,
  tenureMonths: number,
): EmiBreakdown {
  assertPositiveFinite(principal, "principal");
  assertPositiveFinite(tenureMonths, "tenureMonths");
  if (!Number.isFinite(annualRatePercent) || annualRatePercent < 0) {
    throw new RangeError("annualRatePercent must be zero or a positive number");
  }

  const roundedTenure = Math.round(tenureMonths);

  if (annualRatePercent === 0) {
    const emi = principal / roundedTenure;
    return { emi, totalInterest: 0, totalPayment: principal };
  }

  const monthlyRate = annualRatePercent / 12 / 100;
  const growth = Math.pow(1 + monthlyRate, roundedTenure);
  const emi = (principal * monthlyRate * growth) / (growth - 1);
  const totalPayment = emi * roundedTenure;
  const totalInterest = totalPayment - principal;

  return { emi, totalInterest, totalPayment };
}

export interface EligibilityParams {
  netMonthlyIncome: number;
  existingMonthlyObligations: number;
  annualRatePercent: number;
  tenureMonths: number;
  /** Fixed Obligation to Income Ratio lenders typically apply: the share
   * of net income they'll allow toward all EMIs combined. Defaults to
   * 50%, a common ceiling; individual lenders vary from ~40-55%. */
  foirPercent?: number;
}

export interface EligibilityResult {
  maxAffordableEmi: number;
  maxLoanAmount: number;
  foirPercent: number;
}

const DEFAULT_FOIR_PERCENT = 50;

/**
 * Inverts the EMI formula to estimate the largest loan a lender would
 * likely approve, given income, existing obligations, and a FOIR ceiling.
 * This is a pre-qualification estimate, not an underwriting decision —
 * actual approved amounts depend on the lender's full policy.
 */
export function calculateEligibility(params: EligibilityParams): EligibilityResult {
  const {
    netMonthlyIncome,
    existingMonthlyObligations,
    annualRatePercent,
    tenureMonths,
    foirPercent = DEFAULT_FOIR_PERCENT,
  } = params;

  assertPositiveFinite(netMonthlyIncome, "netMonthlyIncome");
  assertPositiveFinite(tenureMonths, "tenureMonths");
  if (!Number.isFinite(existingMonthlyObligations) || existingMonthlyObligations < 0) {
    throw new RangeError("existingMonthlyObligations must be zero or a positive number");
  }
  if (!Number.isFinite(annualRatePercent) || annualRatePercent < 0) {
    throw new RangeError("annualRatePercent must be zero or a positive number");
  }
  if (!Number.isFinite(foirPercent) || foirPercent <= 0 || foirPercent > 100) {
    throw new RangeError("foirPercent must be between 0 and 100");
  }

  const maxTotalEmi = netMonthlyIncome * (foirPercent / 100);
  const maxAffordableEmi = Math.max(0, maxTotalEmi - existingMonthlyObligations);

  if (maxAffordableEmi === 0) {
    return { maxAffordableEmi: 0, maxLoanAmount: 0, foirPercent };
  }

  const roundedTenure = Math.round(tenureMonths);
  let maxLoanAmount: number;

  if (annualRatePercent === 0) {
    maxLoanAmount = maxAffordableEmi * roundedTenure;
  } else {
    const monthlyRate = annualRatePercent / 12 / 100;
    const growth = Math.pow(1 + monthlyRate, roundedTenure);
    maxLoanAmount = (maxAffordableEmi * (growth - 1)) / (monthlyRate * growth);
  }

  return { maxAffordableEmi, maxLoanAmount, foirPercent };
}
