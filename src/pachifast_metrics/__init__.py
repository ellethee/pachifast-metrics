"""Prometheus metrics for pachifast projects: ``from pachifast_metrics import module``."""

from importlib.metadata import PackageNotFoundError, version

from pachifast_metrics.module import module

try:
    __version__ = version("pachifast-metrics")
except PackageNotFoundError:  # a source tree that is not installed
    __version__ = "0+unknown"

__all__ = ["__version__", "module"]
