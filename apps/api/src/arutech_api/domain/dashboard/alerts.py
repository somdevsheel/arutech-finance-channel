from arutech_api.domain.dashboard.entities import Alert, AlertSeverity

# Named, honest thresholds — not user-configurable (that's a rules-engine
# feature this phase doesn't build; see Alert's docstring). Chosen as
# reasonable defaults for a small-to-mid DSA operation; revisit with real
# usage data rather than guessing tighter numbers now.
PENDING_APPROVAL_WARNING_THRESHOLD = 10
PENDING_APPROVAL_CRITICAL_THRESHOLD = 25
UNASSIGNED_CUSTOMER_INFO_THRESHOLD = 1
NEW_LEAD_BACKLOG_RATIO_WARNING = 0.5
NEW_LEAD_BACKLOG_MIN_SAMPLE = 5  # don't fire the ratio check on a handful of leads


def evaluate_alerts(
    *,
    loans_pending_approval: int,
    customers_without_relationship_manager: int,
    leads_new_count: int,
    leads_total: int,
) -> list[Alert]:
    """Pure function: metrics in, alerts out — no DB access, so this is
    unit-tested directly against hand-picked inputs rather than through
    integration tests. `DashboardService.get_alerts` is the only caller,
    supplying the live counts."""
    alerts: list[Alert] = []

    if loans_pending_approval >= PENDING_APPROVAL_CRITICAL_THRESHOLD:
        alerts.append(
            Alert(
                severity=AlertSeverity.CRITICAL,
                code="loans_pending_approval_critical",
                message=(
                    f"{loans_pending_approval} loan applications are awaiting review — "
                    "the approval queue needs attention."
                ),
                value=loans_pending_approval,
            )
        )
    elif loans_pending_approval >= PENDING_APPROVAL_WARNING_THRESHOLD:
        alerts.append(
            Alert(
                severity=AlertSeverity.WARNING,
                code="loans_pending_approval_warning",
                message=f"{loans_pending_approval} loan applications are awaiting review.",
                value=loans_pending_approval,
            )
        )

    if customers_without_relationship_manager >= UNASSIGNED_CUSTOMER_INFO_THRESHOLD:
        alerts.append(
            Alert(
                severity=AlertSeverity.INFO,
                code="customers_without_relationship_manager",
                message=(
                    f"{customers_without_relationship_manager} customers have no "
                    "relationship manager assigned."
                ),
                value=customers_without_relationship_manager,
            )
        )

    if (
        leads_total >= NEW_LEAD_BACKLOG_MIN_SAMPLE
        and leads_new_count / leads_total > NEW_LEAD_BACKLOG_RATIO_WARNING
    ):
        alerts.append(
            Alert(
                severity=AlertSeverity.WARNING,
                code="lead_backlog",
                message=(
                    f"{leads_new_count} of {leads_total} leads are still unworked (status NEW)."
                ),
                value=leads_new_count,
            )
        )

    return alerts
