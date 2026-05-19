"""Validacion de formato de placas colombianas."""

from __future__ import annotations

import re

PLATE_PATTERNS = {
    "carro": r"^[A-Z]{3}[0-9]{3}$",
    "moto": r"^[A-Z]{3}[0-9]{2}[A-Z]{1}$",
    "motocarro": r"^[0-9]{3}[A-Z]{3}$",
}


def is_valid_plate(placa: str) -> bool:
    placa = str(placa).strip().upper()
    return any(re.match(pat, placa) for pat in PLATE_PATTERNS.values())
