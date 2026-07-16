import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from arutech_api.api.deps import (
    get_customer_service,
    get_interaction_service,
    get_user_repository,
    require_permission,
)
from arutech_api.api.v1.schemas.crm import (
    CustomerAnalyticsResponse,
    CustomerProfileResponse,
    CustomerTimelineEntryResponse,
    CustomerUserSummary,
    InteractionCreateRequest,
    InteractionResponse,
    RelationshipManagerRequest,
    SegmentUpdateRequest,
    TagRequest,
)
from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.crm.entities import (
    CustomerProfileEntity,
    CustomerSegment,
    InteractionEntity,
)
from arutech_api.domain.users.entities import UserEntity
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.customer_service import CustomerService
from arutech_api.services.interaction_service import InteractionService

router = APIRouter(prefix="/customers", tags=["customers"])

CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
InteractionServiceDep = Annotated[InteractionService, Depends(get_interaction_service)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
CanReadCustomers = Annotated[UserEntity, Depends(require_permission("customers.read"))]
CanManageCustomers = Annotated[UserEntity, Depends(require_permission("customers.manage"))]


async def _profile_response(
    profile: CustomerProfileEntity, user_repo: UserRepository
) -> CustomerProfileResponse:
    user = await user_repo.get_by_id(profile.user_id)
    if user is None:
        # The user existed when the profile was fetched/created moments
        # ago in the same request; this would only trip on a genuinely
        # concurrent deletion, not a normal path.
        raise NotFoundError("Customer not found")

    return CustomerProfileResponse(
        id=profile.id,
        user=CustomerUserSummary(
            id=user.id, full_name=user.full_name, email=user.email, phone=user.phone
        ),
        relationship_manager_id=profile.relationship_manager_id,
        segment=profile.segment,
        tags=list(profile.tags),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _interaction_response(interaction: InteractionEntity) -> InteractionResponse:
    return InteractionResponse(
        id=interaction.id,
        customer_user_id=interaction.customer_user_id,
        channel=interaction.channel,
        direction=interaction.direction,
        summary=interaction.summary,
        notes=interaction.notes,
        occurred_at=interaction.occurred_at,
        logged_by=interaction.logged_by,
        created_at=interaction.created_at,
    )


# --- Fixed-segment routes first: `/{user_id}` below would otherwise treat
# a literal segment like "tags" as a user ID and 422 before reaching the
# real handler (see Phase 5's leads.py for the same ordering constraint). ---


@router.get("", response_model=list[CustomerProfileResponse])
async def list_customers(
    _authorized: CanReadCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
    segment: CustomerSegment | None = None,
    tag: str | None = None,
    relationship_manager_id: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[CustomerProfileResponse]:
    profiles = await customer_service.list_customers(
        segment=segment,
        tag=tag,
        relationship_manager_id=relationship_manager_id,
        limit=limit,
        offset=offset,
    )
    return [await _profile_response(profile, user_repo) for profile in profiles]


@router.get("/analytics/summary", response_model=CustomerAnalyticsResponse)
async def customer_analytics_summary(
    _authorized: CanReadCustomers, customer_service: CustomerServiceDep
) -> CustomerAnalyticsResponse:
    summary = await customer_service.get_analytics_summary()
    return CustomerAnalyticsResponse(
        total_customers=summary.total_customers,
        by_segment=summary.by_segment,
        customers_without_relationship_manager=summary.customers_without_relationship_manager,
        total_interactions=summary.total_interactions,
        by_channel=summary.by_channel,
    )


@router.get("/tags", response_model=list[str])
async def list_tags(
    _authorized: CanReadCustomers, customer_service: CustomerServiceDep
) -> list[str]:
    return await customer_service.list_all_tags()


# --- `/{user_id}`-parametrized routes ---


@router.get("/{user_id}", response_model=CustomerProfileResponse)
async def get_customer(
    user_id: uuid.UUID,
    _authorized: CanReadCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
) -> CustomerProfileResponse:
    profile = await customer_service.get_profile(user_id)
    return await _profile_response(profile, user_repo)


@router.post("/{user_id}/relationship-manager", response_model=CustomerProfileResponse)
async def set_relationship_manager(
    user_id: uuid.UUID,
    payload: RelationshipManagerRequest,
    authorized: CanManageCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
) -> CustomerProfileResponse:
    profile = await customer_service.set_relationship_manager(
        user_id=user_id,
        relationship_manager_id=payload.relationship_manager_id,
        actor_id=authorized.id,
    )
    return await _profile_response(profile, user_repo)


@router.post("/{user_id}/segment", response_model=CustomerProfileResponse)
async def set_segment(
    user_id: uuid.UUID,
    payload: SegmentUpdateRequest,
    authorized: CanManageCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
) -> CustomerProfileResponse:
    profile = await customer_service.set_segment(
        user_id=user_id, segment=payload.segment, actor_id=authorized.id
    )
    return await _profile_response(profile, user_repo)


@router.post("/{user_id}/tags", response_model=CustomerProfileResponse)
async def add_tag(
    user_id: uuid.UUID,
    payload: TagRequest,
    authorized: CanManageCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
) -> CustomerProfileResponse:
    profile = await customer_service.add_tag(
        user_id=user_id, tag_name=payload.tag, actor_id=authorized.id
    )
    return await _profile_response(profile, user_repo)


@router.delete("/{user_id}/tags/{tag_name}", response_model=CustomerProfileResponse)
async def remove_tag(
    user_id: uuid.UUID,
    tag_name: str,
    authorized: CanManageCustomers,
    customer_service: CustomerServiceDep,
    user_repo: UserRepositoryDep,
) -> CustomerProfileResponse:
    profile = await customer_service.remove_tag(
        user_id=user_id, tag_name=tag_name, actor_id=authorized.id
    )
    return await _profile_response(profile, user_repo)


@router.get("/{user_id}/interactions", response_model=list[InteractionResponse])
async def list_interactions(
    user_id: uuid.UUID,
    _authorized: CanReadCustomers,
    interaction_service: InteractionServiceDep,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[InteractionResponse]:
    interactions = await interaction_service.list_for_customer(user_id, limit=limit, offset=offset)
    return [_interaction_response(interaction) for interaction in interactions]


@router.post("/{user_id}/interactions", response_model=InteractionResponse)
async def log_interaction(
    user_id: uuid.UUID,
    payload: InteractionCreateRequest,
    authorized: CanManageCustomers,
    interaction_service: InteractionServiceDep,
) -> InteractionResponse:
    interaction = await interaction_service.log_interaction(
        customer_user_id=user_id,
        channel=payload.channel,
        summary=payload.summary,
        notes=payload.notes,
        direction=payload.direction,
        occurred_at=payload.occurred_at,
        logged_by=authorized.id,
    )
    return _interaction_response(interaction)


@router.get("/{user_id}/timeline", response_model=list[CustomerTimelineEntryResponse])
async def get_customer_timeline(
    user_id: uuid.UUID, _authorized: CanReadCustomers, customer_service: CustomerServiceDep
) -> list[CustomerTimelineEntryResponse]:
    entries = await customer_service.get_timeline(user_id)
    return [
        CustomerTimelineEntryResponse(
            occurred_at=entry.occurred_at,
            kind=entry.kind,
            summary=entry.summary,
            detail=entry.detail,
        )
        for entry in entries
    ]
