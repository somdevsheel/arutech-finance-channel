from abc import ABC, abstractmethod

from arutech_api.domain.auth.entities import OtpPurpose


class OtpDeliveryPort(ABC):
    """Sends a one-time code to a user through some external channel.

    Phase 2 ships `LoggingOtpDeliveryChannel` (logs the code) as the only
    adapter. Phase 13 ("Notification Center") adds real SMS/email/WhatsApp
    adapters against this same interface — the auth service that calls it
    doesn't change.
    """

    @abstractmethod
    async def send(self, destination: str, code: str, purpose: OtpPurpose) -> None: ...
