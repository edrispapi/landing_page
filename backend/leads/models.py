from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

PHONE_REGEX = r"^09[0-9]{9}$"


class Lead(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        DUPLICATE = "duplicate", "Duplicate"
        FAILED = "failed", "Failed"

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=PHONE_REGEX,
                message="Phone number must be in the format 09123456789",
            )
        ],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "leads"
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone_number} ({self.status})"

    def mark_processed(self, status: str | None = None) -> None:
        """Mark the lead as processed (or supplied status) and update timestamps."""
        self.status = status or self.Status.PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at", "updated_at"])
