"""ASGI middleware that counts and times the requests, labelled with the route *template*.

The template (``/api/users/{user_id}``) and not the path (``/api/users/42``) keeps the number of series bounded; a
request that matches no route is labelled ``unmatched``, so a scanner that tries random paths cannot create series.
"""

from __future__ import annotations

import time

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pachifast_metrics.metrics import DURATION, IN_PROGRESS, REQUESTS

UNMATCHED = "unmatched"


def _template(scope: Scope) -> str:
    """The route template of the request (``/api/users/{user_id}``), ``unmatched`` if no route took it.

    The router of a mounted ``APIRouter`` only knows its own part of the path (``/users/{user_id}``), so the part in
    front of it (``/api``) is recovered from the real path: the route path with its parameters filled in is the end
    of ``scope["path"]``, and what comes before is the prefix.
    """
    route = scope.get("route")
    template = getattr(route, "path", None)
    if not template:
        return UNMATCHED
    params = {key: str(value) for key, value in (scope.get("path_params") or {}).items()}
    try:
        tail = getattr(route, "path_format", template).format_map(params)
    except (KeyError, IndexError, ValueError):
        return template
    path: str = scope["path"]
    prefix = path[: len(path) - len(tail)] if tail and path.endswith(tail) else ""
    return f"{prefix}{template}"


class MetricsMiddleware:
    """Record ``pachifast_http_*`` for every HTTP request except the scrape of the metrics themselves."""

    def __init__(self, app: ASGIApp, skip_path: str = "/metrics") -> None:
        self.app = app
        self.skip_path = skip_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Count the request, time it until the response starts and label it once the route is known."""
        if scope["type"] != "http" or scope["path"] == self.skip_path:
            await self.app(scope, receive, send)
            return
        status_code = 500  # what a request that raises before a response counts as
        started = time.perf_counter()
        IN_PROGRESS.inc()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - started
            IN_PROGRESS.dec()
            route = _template(scope)
            REQUESTS.labels(scope["method"], route, str(status_code)).inc()
            DURATION.labels(scope["method"], route).observe(elapsed)


def install(app: FastAPI) -> None:
    """Setup hook of the module: add the middleware while the app is built."""
    app.add_middleware(MetricsMiddleware)
