from arutech_api.domain.contact.entities import ContactSubmissionEntity
from arutech_api.domain.contact.repository import ContactSubmissionRepository


class ContactService:
    def __init__(self, contact_repo: ContactSubmissionRepository):
        self._contact_repo = contact_repo

    async def submit(
        self,
        *,
        name: str,
        email: str,
        subject: str,
        message: str,
        phone: str | None,
        honeypot: str,
    ) -> None:
        """`honeypot` is a hidden form field real users never fill in; bots
        that auto-fill every field will. When it's non-empty, we pretend to
        succeed without persisting anything — tipping off spammers that
        they were caught would just teach them to leave the field blank."""
        if honeypot:
            return

        await self._contact_repo.create(
            ContactSubmissionEntity(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
            )
        )
