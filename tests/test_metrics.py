"""The metrics endpoint and the middleware, on a real pachifast app."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

os.environ.setdefault("PACHIFAST_SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")

import pytest
from fastapi.testclient import TestClient
from pachifast import create_app
from pachifast.config import get_settings
from pachifast.presets import core_module
from prometheus_client.parser import text_string_to_metric_families

import pachifast_metrics
from pachifast_metrics import module as metrics_module
from pachifast_metrics.metrics import DURATION, IN_PROGRESS, REQUESTS


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    monkeypatch.setenv("PACHIFAST_AUTH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'db.sqlite3'}")
    monkeypatch.delenv("PACHIFAST_METRICS_TOKEN", raising=False)
    monkeypatch.delenv("PACHIFAST_METRICS_ENABLED", raising=False)
    get_settings.cache_clear()
    REQUESTS.clear()
    DURATION.clear()
    with TestClient(create_app((core_module, metrics_module))) as test_client:
        yield test_client
    get_settings.cache_clear()


def _samples(text: str) -> dict[tuple[str, tuple[tuple[str, str], ...]], float]:
    found = {}
    for family in text_string_to_metric_families(text):
        for sample in family.samples:
            found[(sample.name, tuple(sorted(sample.labels.items())))] = sample.value
    return found


def test_the_version_is_the_installed_one() -> None:
    from importlib.metadata import version

    assert pachifast_metrics.__version__ == version("pachifast-metrics")


def test_requests_are_counted_by_route_template_and_status(client: TestClient) -> None:
    for _ in range(3):
        assert client.get("/api/health/live").status_code == 200
    assert client.get("/api/auth/user").status_code == 401
    assert client.get("/api/no-such-route-1").status_code == 404
    assert client.get("/api/no-such-route-2").status_code == 404

    scraped = client.get("/metrics")
    assert scraped.status_code == 200
    assert scraped.headers["content-type"].startswith("text/plain")
    samples = _samples(scraped.text)
    key = ("pachifast_http_requests_total", (("method", "GET"), ("route", "/api/health/live"), ("status", "200")))
    assert samples[key] == 3
    unauthorized = (("method", "GET"), ("route", "/api/auth/user"), ("status", "401"))
    assert samples[("pachifast_http_requests_total", unauthorized)] == 1
    # two different unknown paths are one series: a scanner cannot make series
    unmatched = (("method", "GET"), ("route", "unmatched"), ("status", "404"))
    assert samples[("pachifast_http_requests_total", unmatched)] == 2
    count = ("pachifast_http_request_duration_seconds_count", (("method", "GET"), ("route", "/api/health/live")))
    assert samples[count] == 3


def test_the_scrape_itself_is_not_counted(client: TestClient) -> None:
    client.get("/metrics")
    client.get("/metrics")
    assert not any(
        "route" in dict(labels).keys() and dict(labels)["route"] == "/metrics"
        for _, labels in _samples(client.get("/metrics").text)
    )


def test_no_request_is_left_in_progress(client: TestClient) -> None:
    client.get("/api/health/live")
    assert IN_PROGRESS._value.get() == 0  # noqa: SLF001


def test_a_token_protects_the_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PACHIFAST_METRICS_TOKEN", "s3cret-token")
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Basic s3cret-token"}).status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer s3cret-token"}).status_code == 200


def test_the_endpoint_can_be_switched_off(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PACHIFAST_METRICS_ENABLED", "false")
    assert client.get("/metrics").status_code == 404


def test_the_module_declares_the_pachifast_versions_it_needs() -> None:
    assert metrics_module.requires_pachifast == ">=0.19.0,<0.20.0"
    assert metrics_module.setup_hooks == ("pachifast_metrics.middleware:install",)


def test_a_path_parameter_is_a_placeholder_in_the_label(client: TestClient) -> None:
    for key in ("theme", "language", "density"):
        assert client.put(f"/api/auth/user/settings/ui/{key}", json={"value": 1}).status_code == 401
    routes = {dict(labels)["route"] for _, labels in _samples(client.get("/metrics").text) if "route" in dict(labels)}
    assert "/api/auth/user/settings/{category}/{key}" in routes
    assert not any("theme" in route or "density" in route for route in routes)
