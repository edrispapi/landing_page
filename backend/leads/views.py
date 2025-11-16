from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from celery import current_app as celery_app
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.template import loader
try:
    from django_ratelimit.decorators import ratelimit as _ratelimit  # type: ignore
except Exception:  # pragma: no cover - optional dependency in local mode
    _ratelimit = None  # type: ignore

def ratelimit(*args, **kwargs):
    """
    No-op wrapper when rate limiting is disabled or django_ratelimit is unavailable.
    """
    if getattr(settings, "RATELIMIT_ENABLE", False) and _ratelimit:
        return _ratelimit(*args, **kwargs)

    def _decorator(view_func):
        return view_func

    return _decorator

from .logging import get_mongo_client
from .tasks import process_lead_submission
from .utils import get_client_ip
from .validators import validate_phone_number

logger = logging.getLogger(__name__)


class LandingPageView(View):
    """Serve the cached landing HTML / React entry point."""

    template_name = "landing/index.html"
    cache_key = "landing_page_html"
    cache_ttl = 300

    def get(self, request, *args, **kwargs) -> HttpResponse:
        cached_html = cache.get(self.cache_key)
        if cached_html:
            return HttpResponse(cached_html)

        dist_dir: Path = Path(getattr(settings, "FRONTEND_DIST_DIR", ""))
        index_file = dist_dir / "index.html"

        if dist_dir.exists() and index_file.exists():
            html = index_file.read_text(encoding="utf-8")
        else:
            template = loader.get_template(self.template_name)
            html = template.render({})

        cache.set(self.cache_key, html, self.cache_ttl)
        return HttpResponse(html)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(
    ratelimit(key="ip", rate="10/m", method=["POST"], block=True),
    name="dispatch",
)
class SubmitLeadView(View):
    """Accept phone numbers and enqueue Celery processing."""

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        phone_number = (payload.get("phone") or "").strip()

        try:
            validate_phone_number(phone_number)
        except ValidationError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        metadata = self._build_metadata(request)

        try:
            async_result = process_lead_submission.delay(
                phone_number=phone_number,
                metadata=metadata,
            )
            task_id = async_result.id
        except Exception as exc:  # Broker unavailable or enqueue failure
            logger.warning("Failed to enqueue Celery task: %s", exc)
            task_id = None

        return JsonResponse(
            {
                "success": True,
                "message": "Your number has been registered successfully!",
                "task_id": task_id,
            },
            status=202,
        )

    def _build_metadata(self, request) -> Dict[str, Any]:
        return {
            "ip": get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "path": request.path,
            "method": request.method,
        }


@require_GET
def health_check(request):
    """Composite health check for infra dependencies."""
    status = {}
    overall_ok = True

    # Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["database"] = "ok"
    except Exception as exc:  # pragma: no cover - operational safeguard
        status["database"] = str(exc)
        overall_ok = False

    # Cache / Redis
    try:
        cache.set("health_ping", "pong", 5)
        cache_value = cache.get("health_ping")
        status["cache"] = "ok" if cache_value == "pong" else "degraded"
        overall_ok &= cache_value == "pong"
    except Exception as exc:  # pragma: no cover
        status["cache"] = str(exc)
        overall_ok = False

    # MongoDB
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        status["mongo"] = "ok"
    except Exception as exc:  # pragma: no cover
        status["mongo"] = str(exc)
        overall_ok = False

    # Celery
    try:
        ping_response = celery_app.control.ping(timeout=0.5)
        status["celery"] = "ok" if ping_response else "no workers"
        overall_ok &= bool(ping_response)
    except Exception as exc:  # pragma: no cover
        status["celery"] = str(exc)
        overall_ok = False

    payload = {
        "status": "healthy" if overall_ok else "degraded",
        **status,
        "timestamp": timezone.now().isoformat(),
    }
    return JsonResponse(payload, status=200 if overall_ok else 503)
