"""EMI and eligibility math, ported line-for-line from
`apps/web/src/lib/loan-calculations.ts` so the backend's credit
assessment and the frontend's pre-qualification calculator agree on the
same numbers for the same inputs — two implementations of the same
formula drifting apart would be worse than either being simplified.
Credit scoring is a separate, explicitly-heuristic addition (see
`assess_credit`'s docstring) with no frontend equivalent.
"""

from decimal import Decimal

from arutech_api.domain.loans.entities import EligibilityStatus, RiskCategory

# Fixed Obligation to Income Ratio ceiling: the share of net income
# lenders typically allow toward all EMIs combined. Matches the
# frontend's DEFAULT_FOIR_PERCENT exactly.
DEFAULT_FOIR_PERCENT = Decimal(50)


def calculate_emi(
    principal: Decimal, annual_rate_percent: Decimal, tenure_months: int
) -> Decimal:
    """Standard reducing-balance EMI formula. Falls back to a straight-line
    split when annual_rate_percent is 0, since the formula divides by zero
    at r = 0 — same as the TypeScript original."""
    if annual_rate_percent == 0:
        return principal / tenure_months

    monthly_rate = annual_rate_percent / Decimal(12) / Decimal(100)
    growth = (1 + monthly_rate) ** tenure_months
    return principal * monthly_rate * growth / (growth - 1)


def assess_eligibility(
    *,
    monthly_income: Decimal,
    existing_monthly_obligations: Decimal,
    emi: Decimal,
    foir_percent: Decimal = DEFAULT_FOIR_PERCENT,
) -> EligibilityStatus:
    """Forward-checks a specific requested EMI against the FOIR ceiling —
    the frontend calculator inverts this same formula to estimate a max
    loan amount *before* applying; here there's already a concrete
    requested amount, so no inversion is needed."""
    max_total_emi = monthly_income * foir_percent / Decimal(100)
    max_affordable_emi = max(Decimal(0), max_total_emi - existing_monthly_obligations)
    if emi <= max_affordable_emi:
        return EligibilityStatus.ELIGIBLE
    return EligibilityStatus.INELIGIBLE


def assess_credit(
    *, monthly_income: Decimal, emi: Decimal, tenure_months: int
) -> tuple[int, RiskCategory]:
    """A simple, deterministic, inspectable heuristic — not a real credit
    bureau check. No CIBIL/Experian integration exists; this exists so the
    pipeline has *something* to gate approval on, the same honest-
    heuristic spirit as `domain/leads/scoring.py`'s score_lead(). Real
    bureau integration is a distinct, later, explicitly-scoped feature,
    not something to fake here."""
    emi_to_income_ratio = emi / monthly_income if monthly_income else Decimal(1)

    if emi_to_income_ratio > Decimal("0.75"):
        score = 20
    elif emi_to_income_ratio > Decimal("0.5"):
        score = 45
    elif emi_to_income_ratio > Decimal("0.35"):
        score = 70
    else:
        score = 90

    if tenure_months > 60:
        score -= 10

    score = max(0, min(100, score))

    if score >= 70:
        risk = RiskCategory.LOW
    elif score >= 40:
        risk = RiskCategory.MEDIUM
    else:
        risk = RiskCategory.HIGH

    return score, risk
