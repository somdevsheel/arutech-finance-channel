import uuid

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.contact.entities import ContactSubmissionEntity
from arutech_api.domain.leads.entities import LeadEntity, LeadStatus, is_transition_allowed
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.domain.leads.scoring import score_lead
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService


class LeadService:
    def __init__(
        self,
        lead_repo: LeadRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ):
        self._lead_repo = lead_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def create_from_contact_submission(
        self, submission: ContactSubmissionEntity
    ) -> LeadEntity:
        score = score_lead(
            phone=submission.phone, subject=submission.subject, message=submission.message
        )
        lead = await self._lead_repo.create(
            LeadEntity(
                contact_submission_id=submission.id,
                name=submission.name,
                email=submission.email,
                phone=submission.phone,
                score=score,
            )
        )
        await self._audit_service.record(
            action="lead.created",
            entity_type="lead",
            entity_id=str(lead.id),
            metadata={"source": "contact_form", "score": score},
        )
        return lead

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
        return await self._lead_repo.list(
            status=status, assigned_to=assigned_to, limit=limit, offset=offset
        )

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
