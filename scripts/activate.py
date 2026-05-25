"""License key generator - run this on YOUR machine (seller side).

Usage:
    python scripts/activate.py <MACHINE_CODE>
    python scripts/activate.py                    # prompt interactively

Never share this script with buyers — it contains the signing secret.
"""

from __future__ import annotations

import hmac
import hashlib
import sys

_SECRET_KEY = b"ta_license_v1_7f3a9c1e4b2d8f6a0c5e9d3b7f1a4c8e"


def generate_activation(machine_code: str) -> str:
    digest = hmac.digest(_SECRET_KEY, machine_code.encode(), "sha256")
    return digest.hex()[:20].upper()


def main() -> None:
    if len(sys.argv) > 1:
        mc = sys.argv[1].strip()
    else:
        mc = input("Enter buyer's machine code: ").strip()

    if not mc or len(mc) < 8:
        print("Error: invalid machine code")
        sys.exit(1)

    activation = generate_activation(mc)
    print(f"\nMachine code : {mc}")
    print(f"Activation   : {activation}")
    print(f"\nSend the activation code above to the buyer.")


if __name__ == "__main__":
    main()
