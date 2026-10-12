"""Headway broker presets for MetaTrader 5."""

from __future__ import annotations

# Official Headway MT5 servers (from Headway support docs).
# Demo: Headway-Demo (mt5.demo.trade-hw.online)
# Real: Headway-Real (mt5.real.trade-hw.online)
HEADWAY_DEMO_SERVERS: tuple[str, ...] = (
    "Headway-Demo",
    "mt5.demo.trade-hw.online",
)

HEADWAY_REAL_SERVERS: tuple[str, ...] = (
    "Headway-Real",
    "mt5.real.trade-hw.online",
)

DEFAULT_DEMO_SERVER = "Headway-Demo"
DEFAULT_REAL_SERVER = "Headway-Real"


def list_headway_servers() -> dict[str, tuple[str, ...]]:
    """Return known Headway servers grouped by account type."""
    return {"demo": HEADWAY_DEMO_SERVERS, "real": HEADWAY_REAL_SERVERS}


def resolve_headway_server(server: str | None, demo: bool = False) -> str:
    """Resolve a user-supplied server value to a concrete Headway server name.

    Args:
        server: Raw server string, or None to use the default.
        demo: If True and server is None, return the demo server.

    Returns:
        Concrete server name to pass to MT5 login.
    """
    if server is None or not server.strip():
        return DEFAULT_DEMO_SERVER if demo else DEFAULT_REAL_SERVER

    cleaned = server.strip()
    lowered = cleaned.lower()

    # Accept shortcuts like "demo", "real", "headway-demo", "headway-real".
    if lowered in {"demo", "headway-demo", "headway demo"}:
        return DEFAULT_DEMO_SERVER
    if lowered in {"real", "headway-real", "headway real"}:
        return DEFAULT_REAL_SERVER

    return cleaned
