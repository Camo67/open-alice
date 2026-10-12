"""Web dashboard for Alice (account, charts, positions, order ticket)."""

from open_alice.dashboard.app import create_dashboard_app
from open_alice.dashboard.charts import build_strategy, chart_payload

__all__ = ["create_dashboard_app", "build_strategy", "chart_payload"]
