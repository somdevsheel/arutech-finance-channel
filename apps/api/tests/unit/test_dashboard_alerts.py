from arutech_api.domain.dashboard.alerts import evaluate_alerts
from arutech_api.domain.dashboard.entities import AlertSeverity


def test_no_alerts_when_everything_is_healthy() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=2,
        customers_without_relationship_manager=0,
        leads_new_count=1,
        leads_total=10,
    )
    assert alerts == []


def test_pending_approval_warning_threshold() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=10,
        customers_without_relationship_manager=0,
        leads_new_count=0,
        leads_total=0,
    )
    assert len(alerts) == 1
    assert alerts[0].code == "loans_pending_approval_warning"
    assert alerts[0].severity == AlertSeverity.WARNING
    assert alerts[0].value == 10


def test_pending_approval_critical_threshold_supersedes_warning() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=25,
        customers_without_relationship_manager=0,
        leads_new_count=0,
        leads_total=0,
    )
    assert len(alerts) == 1
    assert alerts[0].code == "loans_pending_approval_critical"
    assert alerts[0].severity == AlertSeverity.CRITICAL


def test_unassigned_customers_triggers_info_alert() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=0,
        customers_without_relationship_manager=3,
        leads_new_count=0,
        leads_total=0,
    )
    assert len(alerts) == 1
    assert alerts[0].code == "customers_without_relationship_manager"
    assert alerts[0].severity == AlertSeverity.INFO
    assert alerts[0].value == 3


def test_lead_backlog_fires_above_ratio_and_sample_size() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=0,
        customers_without_relationship_manager=0,
        leads_new_count=6,
        leads_total=10,
    )
    assert len(alerts) == 1
    assert alerts[0].code == "lead_backlog"


def test_lead_backlog_does_not_fire_below_minimum_sample_size() -> None:
    # 2 of 2 leads are NEW — a 100% ratio, but too small a sample to be
    # meaningful (see NEW_LEAD_BACKLOG_MIN_SAMPLE).
    alerts = evaluate_alerts(
        loans_pending_approval=0,
        customers_without_relationship_manager=0,
        leads_new_count=2,
        leads_total=2,
    )
    assert alerts == []


def test_lead_backlog_does_not_fire_at_or_below_ratio_threshold() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=0,
        customers_without_relationship_manager=0,
        leads_new_count=5,
        leads_total=10,
    )
    assert alerts == []


def test_multiple_alerts_can_fire_together() -> None:
    alerts = evaluate_alerts(
        loans_pending_approval=30,
        customers_without_relationship_manager=1,
        leads_new_count=8,
        leads_total=10,
    )
    codes = {alert.code for alert in alerts}
    assert codes == {
        "loans_pending_approval_critical",
        "customers_without_relationship_manager",
        "lead_backlog",
    }
