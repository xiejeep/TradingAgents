"""API key settings — read/write .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from tradingagents.llm_clients.api_key_env import PROVIDER_API_KEY_ENV

EXTRA_KEYS: Dict[str, Optional[str]] = {
    "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
}


def _env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def get_key_status() -> Dict[str, Dict[str, Optional[str]]]:
    result: Dict[str, Dict[str, Optional[str]]] = {
        "llm": {},
        "data": {},
    }

    for provider, env_var in PROVIDER_API_KEY_ENV.items():
        if not env_var:
            continue
        value = os.getenv(env_var, "")
        result["llm"][provider] = {
            "env_var": env_var,
            "masked": _mask_key(value) if value else None,
            "is_set": bool(value),
        }

    for vendor, env_var in EXTRA_KEYS.items():
        if not env_var:
            continue
        value = os.getenv(env_var, "")
        result["data"][vendor] = {
            "env_var": env_var,
            "masked": _mask_key(value) if value else None,
            "is_set": bool(value),
        }

    return result


def save_keys(keys: Dict[str, str]) -> None:
    env_file = _env_path()
    lines: list[str] = []
    seen: set[str] = set()

    if env_file.exists():
        existing = env_file.read_text(encoding="utf-8")
        for line in existing.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if "=" in stripped:
                    key_name = stripped.split("=", 1)[0].strip()
                    if key_name in keys:
                        lines.append(f"{key_name}={keys[key_name]}")
                        seen.add(key_name)
                        continue
            lines.append(line)

    for key_name, value in keys.items():
        if key_name not in seen:
            lines.append(f"{key_name}={value}")

    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for key_name, value in keys.items():
        os.environ[key_name] = value


def _mask_key(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]
