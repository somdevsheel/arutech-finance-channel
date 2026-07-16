from arutech_api.core.logging import get_logger
from arutech_api.domain.auth.entities import OtpPurpose
from arutech_api.domain.auth.ports import OtpDeliveryPort

logger = get_logger(__name__)


class LoggingOtpDeliveryChannel(OtpDeliveryPort):
    """Dev/local delivery channel: logs the code instead of sending it.

    Phase 13 ("Notification Center") adds real SMS/email/WhatsApp adapters
    against the same `OtpDeliveryPort` interface; nothing in the auth
    service changes when that happens, only which adapter is bound in DI.
    """

    async def send(self, destination: str, code: str, purpose: OtpPurpose) -> None:
        logger.info("otp_generated", destination=destination, purpose=purpose.value, code=code)
