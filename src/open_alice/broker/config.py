"""Local storage for MT5 / Headway credentials (file-based, chmod 600)."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


def get_config_dir() -> Path:
    """Return the per-user config directory for open-alice."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "open-alice"


def get_credentials_path() -> Path:
    """Return the path of the saved MT5 credentials file."""
    return get_config_dir() / "mt5.env"


def save_credentials(login: int, password: str, server: str) -> Path:
    """Save MT5 credentials to a user-only readable file.

    Args:
        login: MT5 account number.
        password: MT5 password (trade password, not investor-only if trading).
        server: MT5 server name (e.g. Headway-Demo).

    Returns:
        Path of the written file.
    """
    path = get_credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Minimal .env format without extra dependencies.
    content = f'MT5_LOGIN={login}\nMT5_PASSWORD={password}\nMT5_SERVER={server}\n'
    path.write_text(content, encoding="utf-8")
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)
    return path


def load_credentials() -> dict[str, str] | None:
    """Load saved MT5 credentials, checking file then environment.

    Returns:
        Dict with login/password/server, or None when nothing is stored.
    """
    path = get_credentials_path()
    data: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"').strip("'")

    # Environment variables act as fallback / override when file is absent.
    login = data.get("MT5_LOGIN") or os.environ.get("MT5_LOGIN", "")
    password = data.get("MT5_PASSWORD") or os.environ.get("MT5_PASSWORD", "")
    server = data.get("MT5_SERVER") or os.environ.get("MT5_SERVER", "")
    if not login or not password or not server:
        return None
    return {"login": login, "password": password, "server": server}


def clear_credentials() -> bool:
    """Delete the saved credentials file. Returns True if something was removed."""
    path = get_credentials_path()
    if path.is_file():
        path.unlink()
        return True
    return False
