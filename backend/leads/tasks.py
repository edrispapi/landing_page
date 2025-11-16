from __future__ import annotations

import logging

from celery import shared_task
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .logging import log_request_event
from .models import Lead
from .validators import validate_phone_number

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_lead_submission(self, phone_number: str, metadata: dict[str, str] | None = None):
    """Validate and persist the lead asynchronously."""
    metadata = metadata or {}

    try:
        validate_phone_number(phone_number)

        with transaction.atomic():
            lead, created = Lead.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    "status": Lead.Status.PROCESSED,
                    "processed_at": timezone.now(),
                },
            )

            if not created and lead.status != Lead.Status.DUPLICATE:
                lead.status = Lead.Status.DUPLICATE
                lead.save(update_fields=["status", "updated_at"])

        log_request_event(
            phone_number,
            {**metadata, "created": created},
            success=True,
        )

        return {
            "phone_number": phone_number,
            "created": created,
        }

    except ValidationError as exc:
        message = str(exc)
        logger.info("Validation failed for %s: %s", phone_number, message)
        log_request_event(
            phone_number,
            {**(metadata or {}), "reason": "validation_error"},
            success=False,
            error=message,
        )
        return {"error": message, "phone_number": phone_number}

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Celery task failed for %s", phone_number)
        log_request_event(
            phone_number,
            metadata,
            success=False,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=min(60 * (self.request.retries + 1), 300))
