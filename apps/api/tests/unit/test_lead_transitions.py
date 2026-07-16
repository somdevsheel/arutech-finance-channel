import pytest

from arutech_api.domain.leads.entities import ALLOWED_TRANSITIONS, LeadStatus, is_transition_allowed


class TestLeadTransitions:
    @pytest.mark.parametrize(
        "current,target",
        [
            (LeadStatus.NEW, LeadStatus.CONTACTED),
            (LeadStatus.NEW, LeadStatus.DISQUALIFIED),
            (LeadStatus.CONTACTED, LeadStatus.QUALIFIED),
            (LeadStatus.CONTACTED, LeadStatus.DISQUALIFIED),
            (LeadStatus.QUALIFIED, LeadStatus.CONVERTED),
            (LeadStatus.QUALIFIED, LeadStatus.DISQUALIFIED),
        ],
    )
    def test_allowed_transitions(self, current: LeadStatus, target: LeadStatus) -> None:
        assert is_transition_allowed(current, target) is True

    @pytest.mark.parametrize(
        "current,target",
        [
            (LeadStatus.NEW, LeadStatus.QUALIFIED),  # can't skip a stage
            (LeadStatus.NEW, LeadStatus.CONVERTED),
            (LeadStatus.CONTACTED, LeadStatus.NEW),  # no going backward
            (LeadStatus.CONVERTED, LeadStatus.NEW),  # terminal state
            (LeadStatus.CONVERTED, LeadStatus.CONTACTED),
            (LeadStatus.DISQUALIFIED, LeadStatus.NEW),  # terminal state
            (LeadStatus.DISQUALIFIED, LeadStatus.QUALIFIED),
            (LeadStatus.NEW, LeadStatus.NEW),  # no-op transition
        ],
    )
    def test_disallowed_transitions(self, current: LeadStatus, target: LeadStatus) -> None:
        assert is_transition_allowed(current, target) is False

    def test_every_status_has_an_explicit_transition_entry(self) -> None:
        # Guards against a future LeadStatus member being added without
        # anyone deciding what it can transition to/from.
        for status in LeadStatus:
            assert status in ALLOWED_TRANSITIONS
