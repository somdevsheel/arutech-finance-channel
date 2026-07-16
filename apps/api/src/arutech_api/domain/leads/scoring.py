"""A simple, deterministic scoring heuristic — not a model. Every rule here
is inspectable and testable (see tests/unit/test_lead_scoring.py); nothing
here is meant to approximate the AI assistant layer that's a much later,
separate phase. Real signal will replace/extend this once there's real
outcome data (conversions) to learn from — premature to build that now.
"""

_LOAN_KEYWORDS = ("loan", "emi", "eligib", "apply", "interest rate", "disburs")

_BASE_SCORE = 20
_PHONE_BONUS = 30
_SUBSTANTIVE_MESSAGE_BONUS = 20
_SUBSTANTIVE_MESSAGE_MIN_LENGTH = 50
_LOAN_KEYWORD_BONUS = 30

MAX_SCORE = 100


def score_lead(*, phone: str | None, subject: str, message: str) -> int:
    score = _BASE_SCORE

    if phone:
        # A phone number means they're reachable beyond email — a real
        # signal of intent to be contacted, not just curiosity.
        score += _PHONE_BONUS

    if len(message) >= _SUBSTANTIVE_MESSAGE_MIN_LENGTH:
        score += _SUBSTANTIVE_MESSAGE_BONUS

    haystack = f"{subject} {message}".lower()
    if any(keyword in haystack for keyword in _LOAN_KEYWORDS):
        score += _LOAN_KEYWORD_BONUS

    return min(score, MAX_SCORE)
