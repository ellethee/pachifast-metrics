# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). While the major version is 0, a minor release may break; each release works with one minor of pachifast.

## [0.1.4] - 2026-10-20

### Changed

- Works with pachifast `>=0.19,<0.20` (`requires_pachifast`).

## [0.1.3] - 2026-10-20

### Changed

- Works with pachifast `>=0.18,<0.19` (`requires_pachifast`).

## [0.1.2] - 2026-10-20

### Changed

- Works with pachifast `>=0.17,<0.18` (`requires_pachifast`).

## [0.1.1] - 2026-10-15

### Changed

- Works with pachifast `>=0.16,<0.17` (`requires_pachifast`).

## [0.1.0] - 2026-10-15

First public release.

### Added

- `GET /metrics` in the Prometheus text format, with `PACHIFAST_METRICS_TOKEN` (bearer token) and `PACHIFAST_METRICS_ENABLED`.
- A middleware, installed with a pachifast setup hook, that counts requests by method, route template and status, times them and tracks the requests in progress.
- Works with pachifast `>=0.15,<0.16` (`requires_pachifast`).
