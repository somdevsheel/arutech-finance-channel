import uuid
from dataclasses import dataclass

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.audit.entities import AuditLogEntity
from arutech_api.domain.audit.repository import AuditLogRepository
from arutech_api.domain.contact.entities import ContactSubmissionEntity
from arutech_api.domain.leads.entities import (
    LeadAnalyticsSummary,
    LeadEntity,
    LeadSource,
    LeadStatus,
    is_transition_allowed,
)
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.domain.leads.scoring import MAX_SCORE, score_lead
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService

# A resubmission from someone already an active lead is still a positive
# signal (they came back), just not a fresh pipeline entry — see
# create_from_contact_submission.
_DUPLICATE_RESUBMISSION_SCORE_BONUS = 10


@dataclass(frozen=True, slots=True)
class LeadImportItem:
    name: str
    email: str
    phone: str | None = None


class LeadService:
    def __init__(
        self,
        lead_repo: LeadRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
        audit_repo: AuditLogRepository,
    ):
        self._lead_repo = lead_repo
        self._user_repo = user_repo
        self._audit_service = audit_service
        self._audit_repo = audit_repo

    async def _auto_assign(self, lead: LeadEntity) -> LeadEntity:
        """Least-loaded assignment: among active employees, whoever
        currently owns the fewest open (non-terminal) leads gets the new
        one. Falls back to leaving the lead unassigned if there are no
        active employees yet — a real, expected state early in the
        platform's life, not an error."""
        employees = await self._user_repo.list_by_role(UserRole.EMPLOYEE, active_only=True)
        if not employees:
            return lead

        open_counts = await self._lead_repo.count_open_by_assignee([e.id for e in employees])
        least_loaded = min(employees, key=lambda e: open_counts.get(e.id, 0))

        assigned = await self._lead_repo.assign(lead.id, least_loaded.id)
        await self._audit_service.record(
            action="lead.auto_assigned",
            entity_type="lead",
            entity_id=str(lead.id),
            metadata={"assigned_to": str(least_loaded.id)},
        )
        return assigned

    async def _create_new_lead(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        source: LeadSource,
        contact_submission_id: uuid.UUID | None,
        score_context_subject: str,
        score_context_message: str,
    ) -> LeadEntity:
        score = score_lead(
            phone=phone, subject=score_context_subject, message=score_context_message
        )
        lead = await self._lead_repo.create(
            LeadEntity(
                contact_submission_id=contact_submission_id,
                source=source,
                name=name,
                email=email,
                phone=phone,
                score=score,
            )
        )
        await self._audit_service.record(
            action="lead.created",
            entity_type="lead",
            entity_id=str(lead.id),
            metadata={"source": source.value, "score": score},
        )
        return await self._auto_assign(lead)

    async def create_from_contact_submission(
        self, submission: ContactSubmissionEntity
    ) -> LeadEntity:
        duplicate = await self._lead_repo.find_active_duplicate(
            email=submission.email, phone=submission.phone
        )
        if duplicate is not None:
            bumped_score = min(duplicate.score + _DUPLICATE_RESUBMISSION_SCORE_BONUS, MAX_SCORE)
            updated = await self._lead_repo.update_score(duplicate.id, bumped_score)
            await self._audit_service.record(
                action="lead.duplicate_submission",
                entity_type="lead",
                entity_id=str(duplicate.id),
                metadata={"contact_submission_id": str(submission.id)},
            )
            return updated

        return await self._create_new_lead(
            name=submission.name,
            email=submission.email,
            phone=submission.phone,
            source=LeadSource.CONTACT_FORM,
            contact_submission_id=submission.id,
            score_context_subject=submission.subject,
            score_context_message=submission.message,
        )

    async def import_leads(self, items: list[LeadImportItem]) -> list[LeadEntity]:
        """Bulk-create leads (project.md's "Import Leads"), going through
        the same duplicate-detection + scoring + auto-assignment pipeline
        as a single contact-form submission — an imported CSV of stale
        contacts shouldn't create a duplicate pipeline entry for someone
        already an active lead any more than a resubmitted web form
        should."""
        results: list[LeadEntity] = []
        for item in items:
            duplicate = await self._lead_repo.find_active_duplicate(
                email=item.email, phone=item.phone
            )
            if duplicate is not None:
                bumped = min(duplicate.score + _DUPLICATE_RESUBMISSION_SCORE_BONUS, MAX_SCORE)
                results.append(await self._lead_repo.update_score(duplicate.id, bumped))
                continue

            results.append(
                await self._create_new_lead(
                    name=item.name,
                    email=item.email,
                    phone=item.phone,
                    source=LeadSource.MANUAL,
                    contact_submission_id=None,
                    score_context_subject="",
                    score_context_message="",
                )
            )
        return results

    async def get_lead(self, lead_id: uuid.UUID) -> LeadEntity:
        lead = await self._lead_repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError("Lead not found")
        return lead

    async def list_leads(
        self,
        *,
        status: LeadStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadEntity]:
        return await self._lead_repo.list_leads(
            status=status, assigned_to=assigned_to, limit=limit, offset=offset
        )

    async def get_analytics_summary(self) -> LeadAnalyticsSummary:
        return await self._lead_repo.get_analytics_summary()

    async def get_activity(self, lead_id: uuid.UUID) -> list[AuditLogEntity]:
        await self.get_lead(lead_id)  # 404s if the lead doesn't exist
        return await self._audit_repo.list_for_entity("lead", str(lead_id))

    async def update_status(
        self, *, lead_id: uuid.UUID, new_status: LeadStatus, actor_id: uuid.UUID
    ) -> LeadEntity:
        lead = await self.get_lead(lead_id)
        if not is_transition_allowed(lead.status, new_status):
            raise ConflictError(
                f"Cannot move a lead from '{lead.status}' to '{new_status}'"
            )

        updated = await self._lead_repo.update_status(lead_id, new_status)
        await self._audit_service.record(
            action="lead.status_changed",
            entity_type="lead",
            entity_id=str(lead_id),
            actor_id=actor_id,
            metadata={"from": lead.status.value, "to": new_status.value},
        )
        return updated

    async def assign(
        self, *, lead_id: uuid.UUID, assignee_id: uuid.UUID, actor_id: uuid.UUID
    ) -> LeadEntity:
        await self.get_lead(lead_id)

        assignee = await self._user_repo.get_by_id(assignee_id)
        if assignee is None:
            raise NotFoundError("Assignee not found")
        if assignee.role not in (UserRole.EMPLOYEE, UserRole.ADMIN):
            raise ConflictError("Leads can only be assigned to employees or admins")

        updated = await self._lead_repo.assign(lead_id, assignee_id)
        await self._audit_service.record(
            action="lead.assigned",
            entity_type="lead",
            entity_id=str(lead_id),
            actor_id=actor_id,
            metadata={"assigned_to": str(assignee_id)},
        )
        return updated
