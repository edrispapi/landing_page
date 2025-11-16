from __future__ import annotations

from typing import Optional


def get_client_ip(request) -> Optional[str]:
    """Best-effort client IP extraction supporting proxies."""
    if request is None:
        return None

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
