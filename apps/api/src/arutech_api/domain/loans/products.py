"""Loan product bounds — duplicated from `apps/web/src/content/loan-
products.ts` (slug, interest rate range, tenure range, amount range,
required documents) on purpose, not joined to it: there's no shared
package between the two apps, and this is the minimum data the backend
needs to validate an application (requested amount/tenure in range,
interest rate in range) and seed its document checklist. The full catalog
(marketing copy, feature lists, eligibility highlights) stays
frontend-only static content — Phase 9's "Loan Product Management" is
what makes this the single, database-backed source of truth for both
sides; until then, changing a product's rates/limits/documents means
editing both files, same as any duplicated-by-necessity constant.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LoanProductLimits:
    slug: str
    name: str
    interest_rate_min: Decimal
    interest_rate_max: Decimal
    tenure_min_months: int
    tenure_max_months: int
    amount_min: int
    amount_max: int
    # Also mirrored from loan-products.ts's `documentsRequired` — seeds the
    # document checklist (domain/loans/entities.py's LoanDocumentEntity)
    # automatically on submission, so "Document Collection" is a working
    # checklist from day one instead of an empty list waiting for someone
    # to populate it by hand for every application.
    documents_required: tuple[str, ...]


LOAN_PRODUCTS: dict[str, LoanProductLimits] = {
    p.slug: p
    for p in [
        LoanProductLimits(
            slug="personal-loan",
            name="Personal Loan",
            interest_rate_min=Decimal("10.5"),
            interest_rate_max=Decimal("24"),
            tenure_min_months=12,
            tenure_max_months=60,
            amount_min=50_000,
            amount_max=4_000_000,
            documents_required=(
                "PAN card",
                "Aadhaar card",
                "Last 3 months' salary slips or 2 years' ITR for self-employed",
                "Last 6 months' bank statements",
            ),
        ),
        LoanProductLimits(
            slug="home-loan",
            name="Home Loan",
            interest_rate_min=Decimal("8.4"),
            interest_rate_max=Decimal("11.5"),
            tenure_min_months=60,
            tenure_max_months=360,
            amount_min=500_000,
            amount_max=50_000_000,
            documents_required=(
                "PAN and Aadhaar card",
                "Income proof (salary slips or ITR)",
                "Property documents and sale agreement",
                "Last 6 months' bank statements",
            ),
        ),
        LoanProductLimits(
            slug="business-loan",
            name="Business Loan",
            interest_rate_min=Decimal("11"),
            interest_rate_max=Decimal("22"),
            tenure_min_months=12,
            tenure_max_months=84,
            amount_min=100_000,
            amount_max=20_000_000,
            documents_required=(
                "PAN card of business and proprietor/partners/directors",
                "GST returns for the last 12 months",
                "Last 2 years' financial statements and ITR",
                "Last 12 months' bank statements",
            ),
        ),
        LoanProductLimits(
            slug="loan-against-property",
            name="Loan Against Property",
            interest_rate_min=Decimal("9"),
            interest_rate_max=Decimal("14"),
            tenure_min_months=36,
            tenure_max_months=180,
            amount_min=500_000,
            amount_max=30_000_000,
            documents_required=(
                "PAN and Aadhaar card",
                "Property title deed and encumbrance certificate",
                "Income proof (salary slips or ITR)",
                "Last 6 months' bank statements",
            ),
        ),
        LoanProductLimits(
            slug="car-loan",
            name="Car Loan",
            interest_rate_min=Decimal("8.5"),
            interest_rate_max=Decimal("13"),
            tenure_min_months=12,
            tenure_max_months=84,
            amount_min=100_000,
            amount_max=5_000_000,
            documents_required=(
                "PAN and Aadhaar card",
                "Income proof (salary slips or ITR)",
                "Proforma invoice from the dealer",
                "Last 3 months' bank statements",
            ),
        ),
        LoanProductLimits(
            slug="education-loan",
            name="Education Loan",
            interest_rate_min=Decimal("9.5"),
            interest_rate_max=Decimal("15"),
            tenure_min_months=60,
            tenure_max_months=180,
            amount_min=100_000,
            amount_max=15_000_000,
            documents_required=(
                "Admission letter and fee structure",
                "PAN and Aadhaar of applicant and co-applicant",
                "Co-applicant's income proof",
                "Academic records (10th, 12th, and prior degree)",
            ),
        ),
        LoanProductLimits(
            slug="gold-loan",
            name="Gold Loan",
            interest_rate_min=Decimal("7.5"),
            interest_rate_max=Decimal("16"),
            tenure_min_months=3,
            tenure_max_months=36,
            amount_min=10_000,
            amount_max=2_500_000,
            documents_required=(
                "PAN or Aadhaar card for KYC",
                "Proof of address",
                "Gold ownership (jewellery brought in-person for valuation)",
            ),
        ),
    ]
}


def get_product(slug: str) -> LoanProductLimits | None:
    return LOAN_PRODUCTS.get(slug)
