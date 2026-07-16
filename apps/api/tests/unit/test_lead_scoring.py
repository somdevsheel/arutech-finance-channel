from arutech_api.domain.leads.scoring import MAX_SCORE, score_lead


class TestScoreLead:
    def test_baseline_submission_gets_the_base_score(self) -> None:
        score = score_lead(phone=None, subject="Hello", message="Just curious.")
        assert score == 20

    def test_a_phone_number_adds_points(self) -> None:
        with_phone = score_lead(phone="9876543210", subject="Hello", message="Just curious.")
        without_phone = score_lead(phone=None, subject="Hello", message="Just curious.")
        assert with_phone > without_phone

    def test_a_substantive_message_adds_points(self) -> None:
        short = score_lead(phone=None, subject="Hi", message="Hi there")
        long = score_lead(
            phone=None,
            subject="Hi",
            message="I would like to know more details about your offerings please.",
        )
        assert long > short

    def test_loan_related_language_adds_points(self) -> None:
        generic = score_lead(phone=None, subject="General question", message="Tell me more")
        loan_related = score_lead(
            phone=None, subject="Home loan enquiry", message="What is the interest rate?"
        )
        assert loan_related > generic

    def test_score_is_capped_at_max(self) -> None:
        score = score_lead(
            phone="9876543210",
            subject="Loan enquiry",
            message="I want to apply for a loan, what is the EMI, interest rate, eligibility?",
        )
        assert score == MAX_SCORE

    def test_score_never_exceeds_max_even_with_a_huge_message(self) -> None:
        score = score_lead(
            phone="9876543210", subject="loan " * 50, message="apply now " * 200
        )
        assert score <= MAX_SCORE
