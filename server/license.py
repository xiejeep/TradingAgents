from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import uuid
from pathlib import Path

_SECRET_KEY = b"ta_license_v1_7f3a9c1e4b2d8f6a0c5e9d3b7f1a4c8e"
_LICENSE_DIR = Path.home() / ".tradingagents" / "license"
_LICENSE_FILE = _LICENSE_DIR / "activation.dat"


def get_machine_code() -> str:
    parts = [_mac_address()]
    mbd = _motherboard_serial()
    if mbd:
        parts.append(mbd)
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16].upper()


def _mac_address() -> str:
    node = uuid.getnode()
    return format(node, "x").zfill(12)


def _motherboard_serial() -> str:
    try:
        if os.name == "nt":
            out = subprocess.check_output(
                ["wmic", "baseboard", "get", "serialnumber"],
                shell=True,
                timeout=5,
            )
            lines = out.decode("utf-8", errors="ignore").strip().splitlines()
            for line in lines:
                s = line.strip()
                if s and s.lower() != "serialnumber":
                    return s
        else:
            out = subprocess.check_output(
                ["dmidecode", "-s", "baseboard-serial-number"],
                timeout=5,
            )
            s = out.decode("utf-8", errors="ignore").strip()
            if s and s.lower() != "not specified":
                return s
    except Exception:
        pass
    return ""


def generate_activation(machine_code: str) -> str:
    digest = hmac.digest(_SECRET_KEY, machine_code.encode(), "sha256")
    return digest.hex()[:20].upper()


def verify_activation(machine_code: str, activation_code: str) -> bool:
    expected = generate_activation(machine_code)
    return hmac.compare_digest(expected, activation_code.upper().strip())


def is_activated() -> bool:
    code = _load_stored()
    if not code:
        return False
    return verify_activation(get_machine_code(), code)


def save_activation(activation_code: str) -> bool:
    mc = get_machine_code()
    if not verify_activation(mc, activation_code):
        return False
    _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    _LICENSE_FILE.write_text(activation_code.upper().strip(), encoding="utf-8")
    return True


def _load_stored() -> str:
    try:
        return _LICENSE_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
