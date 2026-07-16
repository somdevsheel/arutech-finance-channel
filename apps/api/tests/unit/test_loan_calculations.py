from decimal import Decimal

from arutech_api.domain.loans.calculations import assess_credit, assess_eligibility, calculate_emi
from arutech_api.domain.loans.entities import EligibilityStatus, RiskCategory


class TestCalculateEmi:
    def test_matches_the_standard_reference_value(self) -> None:
        # A commonly-cited reference figure: 1 lakh at 12% p.a. over 12
        # months works out to ~8884.88/month.
        emi = calculate_emi(Decimal(100_000), Decimal(12), 12)
        assert round(emi, 2) == Decimal("8884.88")

    def test_zero_rate_is_a_straight_line_split(self) -> None:
        emi = calculate_emi(Decimal(120_000), Decimal(0), 12)
        assert emi == Decimal(10_000)

    def test_higher_rate_means_higher_emi(self) -> None:
        low = calculate_emi(Decimal(500_000), Decimal(10), 60)
        high = calculate_emi(Decimal(500_000), Decimal(20), 60)
        assert high > low


class TestAssessEligibility:
    def test_eligible_when_emi_fits_within_foir(self) -> None:
        status = assess_eligibility(
            monthly_income=Decimal(100_000),
            existing_monthly_obligations=Decimal(0),
            emi=Decimal(30_000),
        )
        assert status == EligibilityStatus.ELIGIBLE

    def test_ineligible_when_emi_exceeds_foir(self) -> None:
        status = assess_eligibility(
            monthly_income=Decimal(50_000),
            existing_monthly_obligations=Decimal(0),
            emi=Decimal(30_000),
        )
        assert status == EligibilityStatus.INELIGIBLE

    def test_existing_obligations_reduce_affordable_emi(self) -> None:
        # 50% of 100,000 = 50,000 ceiling; a 40,000 EMI fits alone...
        without_obligations = assess_eligibility(
            monthly_income=Decimal(100_000),
            existing_monthly_obligations=Decimal(0),
            emi=Decimal(40_000),
        )
        # ...but not once 20,000/month is already committed elsewhere.
        with_obligations = assess_eligibility(
            monthly_income=Decimal(100_000),
            existing_monthly_obligations=Decimal(20_000),
            emi=Decimal(40_000),
        )
        assert without_obligations == EligibilityStatus.ELIGIBLE
        assert with_obligations == EligibilityStatus.INELIGIBLE


class TestAssessCredit:
    def test_low_emi_ratio_scores_low_risk(self) -> None:
        score, risk = assess_credit(
            monthly_income=Decimal(100_000), emi=Decimal(20_000), tenure_months=24
        )
        assert risk == RiskCategory.LOW
        assert score >= 70

    def test_high_emi_ratio_scores_high_risk(self) -> None:
        score, risk = assess_credit(
            monthly_income=Decimal(40_000), emi=Decimal(35_000), tenure_months=24
        )
        assert risk == RiskCategory.HIGH
        assert score < 40

    def test_moderately_high_emi_ratio_scores_medium_risk(self) -> None:
        score, risk = assess_credit(
            monthly_income=Decimal(50_000), emi=Decimal(30_000), tenure_months=24
        )
        assert risk == RiskCategory.MEDIUM
        assert 40 <= score < 70

    def test_long_tenure_reduces_score(self) -> None:
        short_score, _ = assess_credit(
            monthly_income=Decimal(100_000), emi=Decimal(20_000), tenure_months=24
        )
        long_score, _ = assess_credit(
            monthly_income=Decimal(100_000), emi=Decimal(20_000), tenure_months=72
        )
        assert long_score < short_score

    def test_score_is_always_within_bounds(self) -> None:
        score, _ = assess_credit(
            monthly_income=Decimal(1), emi=Decimal(1_000_000), tenure_months=360
        )
        assert 0 <= score <= 100
