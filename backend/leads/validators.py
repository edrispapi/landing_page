import re
from django.core.exceptions import ValidationError

PHONE_PATTERN = re.compile(r"^09[0-9]{9}$")


def validate_phone_number(phone_number: str) -> str:
    if not PHONE_PATTERN.match(phone_number or ""):
        raise ValidationError(
            "Invalid phone number. Use the format 09123456789.",
            code="invalid_phone_format",
        )
    return phone_number
