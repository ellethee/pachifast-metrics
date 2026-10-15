"""The :class:`~pachifast.AppModule` that a project lists in its ``project_modules.py``."""

from pachifast import AppModule

module = AppModule(
    name="metrics",
    kind="common",
    router_modules=("pachifast_metrics.root",),
    setup_hooks=("pachifast_metrics.middleware:install",),
    requires_pachifast=">=0.16.0,<0.17.0",
)
