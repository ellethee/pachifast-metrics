"""The metrics and their registry (one per process, separate from the global one of ``prometheus_client``)."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

#: seconds; the default buckets of ``prometheus_client`` stop at 10 s, which suits an API
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

registry = CollectorRegistry(auto_describe=True)

REQUESTS = Counter(
    "pachifast_http_requests_total",
    "HTTP requests handled, by method, route template and status code.",
    ["method", "route", "status"],
    registry=registry,
)
DURATION = Histogram(
    "pachifast_http_request_duration_seconds",
    "Time to produce the response, by method and route template.",
    ["method", "route"],
    buckets=BUCKETS,
    registry=registry,
)
IN_PROGRESS = Gauge(
    "pachifast_http_requests_in_progress",
    "HTTP requests being handled right now.",
    registry=registry,
)
