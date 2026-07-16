from typing import Annotated

from fastapi import APIRouter, Depends, Request

from arutech_api.api.deps import get_contact_service
from arutech_api.api.v1.schemas.common import MessageResponse
from arutech_api.api.v1.schemas.public import ContactRequest
from arutech_api.core.rate_limit import limiter
from arutech_api.services.contact_service import ContactService

router = APIRouter(prefix="/public", tags=["public"])

ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]


@router.post("/contact", response_model=MessageResponse)
@limiter.limit("5/minute")
async def submit_contact_form(
    request: Request, payload: ContactRequest, contact_service: ContactServiceDep
) -> MessageResponse:
    await contact_service.submit(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
        honeypot=payload.website,
    )
    return MessageResponse(message="Thanks for reaching out — we'll get back to you soon.")
