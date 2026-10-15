# pachifast-metrics

Prometheus metrics for [pachifast](https://pachifast.ilpachi.it/) ([source](https://github.com/ellethee/pachifast)) projects: an extension package. It adds a `GET /metrics` endpoint and a middleware that counts and times every request.

> **Status: alpha.** It follows pachifast 0.x: the minor versions of this package may break, and each release works with one minor of pachifast (`requires_pachifast`).

## Install

```bash
uv add pachifast-metrics
```

Then list the module in the `project_modules.py` of your project (see [extending pachifast](https://pachifast.ilpachi.it/guides/extending/)):

```python
from pachifast.presets import core_module
from pachifast_metrics import module as metrics_module

MODULES = (core_module, metrics_module, ...)
```

## What it exposes

`GET /metrics` (at the root, not under `/api`), in the Prometheus text format:

| Metric | Type | Labels |
| --- | --- | --- |
| `pachifast_http_requests_total` | counter | `method`, `route`, `status` |
| `pachifast_http_request_duration_seconds` | histogram | `method`, `route` |
| `pachifast_http_requests_in_progress` | gauge | |

`route` is the route **template** (`/api/users/{user_id}`), never the path with the real id, and a request that matches no route is `unmatched`: the number of series stays bounded whatever the clients send. The scrape of `/metrics` is not counted.

## Settings

Environment variables, read when the endpoint is called:

| Variable | Default | Effect |
| --- | --- | --- |
| `PACHIFAST_METRICS_TOKEN` | empty | When set, `/metrics` answers only to `Authorization: Bearer <token>` (`401` otherwise). Empty: open, so keep it off the public internet (a reverse proxy rule, or a network that only Prometheus reaches). |
| `PACHIFAST_METRICS_ENABLED` | `true` | `false` makes `/metrics` answer `404`. |

Prometheus:

```yaml
scrape_configs:
  - job_name: myproject
    authorization:
      credentials: <the token>
    static_configs:
      - targets: ["myproject:8000"]
```

With several workers each process keeps its own counters: scrape every worker (one per port or pod), or put `prometheus_client`'s multiprocess mode behind your server; this package does not do it for you.

## Develop

```bash
uv sync
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

## License

MIT, see [LICENSE](https://github.com/ellethee/pachifast-metrics/blob/main/LICENSE).

**Disclaimer.** pachifast-metrics is provided "as is", without warranty of any kind. It is alpha software: it can contain bugs and change incompatibly between minor releases. You are responsible for reviewing, testing and securing the applications you build with it before using them in production.
