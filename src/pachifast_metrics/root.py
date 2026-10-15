"""``GET /metrics``: the metrics in the Prometheus text format, at the root of the server (not under ``/api``).

Set ``PACHIFAST_METRICS_TOKEN`` and the endpoint answers only to ``Authorization: Bearer <token>`` (``401``
otherwise), which is what a Prometheus ``authorization`` block sends. Without a token it is open: then keep it off
the public internet (reverse proxy rule, or a network that only Prometheus reaches). ``PACHIFAST_METRICS_ENABLED=false``
removes it (``404``).
"""

from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request, Response
from pachifast.routing.router_factory import get_router
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pachifast_metrics.metrics import registry

router = get_router(name="metrics", deps=["noauth"], include_in_schema=False)
router.pachifast_mount_prefix = ""  # type: ignore[attr-defined]


def _allowed(request: Request) -> bool:
    """``True`` when no token is configured or the request carries it."""
    token = os.environ.get("PACHIFAST_METRICS_TOKEN", "")
    if not token:
        return True
    scheme, _, given = request.headers.get("authorization", "").partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(given.encode(), token.encode())


@router.get("", skip_envelope=True)
async def scrape(request: Request) -> Response:
    """The current value of every metric."""
    if os.environ.get("PACHIFAST_METRICS_ENABLED", "true").lower() in ("0", "false", "no", "off"):
        raise HTTPException(status_code=404)
    if not _allowed(request):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
