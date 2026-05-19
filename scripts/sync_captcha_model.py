"""Copia el .keras del folder Modelo/ al worker si falta."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modelo" / "OCR_captcha_model_V2_EX4 4.keras"
DST = ROOT / "worker" / "models" / "captcha_model.keras"


def main() -> int:
    if not SRC.exists():
        print(f"No se encontro: {SRC}")
        return 1
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DST)
    print(f"Copiado a {DST} ({DST.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
