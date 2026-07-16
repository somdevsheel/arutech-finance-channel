from pydantic import BaseModel, EmailStr, Field


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=5_000)
    # Hidden on the real form (via CSS, not `type="hidden"`, so form-filling
    # bots that skip hidden inputs still trip it); left blank by real users.
    # Non-empty means "likely a bot" — see ContactService.submit.
    website: str = Field(default="", max_length=255)
