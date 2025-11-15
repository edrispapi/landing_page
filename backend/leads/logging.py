from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict

from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


@lru_cache
def get_mongo_client() -> MongoClient:
    """Return a cached MongoDB client."""
    uri = getattr(settings, "MONGO_URI", None)
    if not uri:
        raise RuntimeError("MONGO_URI is not configured")
    return MongoClient(uri, serverSelectionTimeoutMS=3000, connect=False)


def log_request_event(
    phone_number: str,
    metadata: Dict[str, Any] | None = None,
    *,
    success: bool,
    error: str | None = None,
) -> None:
    """Persist structured request metadata to MongoDB."""
    metadata = metadata or {}

    mongo_db = getattr(settings, "MONGO_DB_NAME", None)
    if not mongo_db:
        logger.debug("MongoDB name not set; skipping log entry.")
        return

    try:
        collection = get_mongo_client()[mongo_db]["request_logs"]
        log_entry = {
            "phone_number": phone_number,
            "success": success,
            "error": error,
            "timestamp": timezone.now(),
            "metadata": metadata,
        }
        collection.insert_one(log_entry)
    except PyMongoError as exc:
        logger.warning("Unable to write log entry to MongoDB: %s", exc)
