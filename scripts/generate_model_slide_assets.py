"""Genera imágenes y métricas para la diapositiva 09 del modelo."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worker.src.ocr.inference import predict_captcha
from worker.src.ocr.preprocess import preprocess_captcha_image

DATA_DIR = ROOT / "Modelo" / "Imagenes Modelo V2 Limpias"
OUT_DIR = ROOT / "docs" / "assets"
METRICS_FILE = OUT_DIR / "modelo-metrics.json"


def _intermediate_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.bilateralFilter(img, d=15, sigmaColor=100, sigmaSpace=100)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    return clahe.apply(img)


def build_preprocess_figure(samples: list[Path]) -> Path:
    fig, axes = plt.subplots(len(samples), 3, figsize=(9, 1.8 * len(samples)))
    if len(samples) == 1:
        axes = np.array([axes])

    titles = ("Entrada (captura)", "Filtro + CLAHE", "Binarizado 280×80")
    for row, path in enumerate(samples):
        raw = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        mid = _intermediate_gray(raw)
        final = preprocess_captcha_image(raw)

        for col, img in enumerate((raw, mid, final)):
            axes[row, col].imshow(img, cmap="gray", aspect="auto")
            axes[row, col].axis("off")
            if row == 0:
                axes[row, col].set_title(titles[col], fontsize=10, pad=6)
            if col == 0:
                axes[row, col].set_ylabel(path.stem, fontsize=8, rotation=0, labelpad=36, va="center")

    plt.tight_layout()
    out = OUT_DIR / "modelo-preproceso.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def evaluate_accuracy(max_samples: int | None = None) -> dict:
    files = sorted(DATA_DIR.glob("*.png"))
    if not files:
        raise FileNotFoundError(f"No hay PNG en {DATA_DIR}")

    if max_samples:
        random.seed(42)
        files = random.sample(files, min(max_samples, len(files)))

    correct = 0
    total = 0
    for path in files:
        label = path.stem  # filename = ground truth
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        processed = preprocess_captcha_image(img)
        pred = predict_captcha(processed).strip()
        if pred == label:
            correct += 1
        total += 1

    acc = correct / total if total else 0.0
    return {
        "accuracy": round(acc, 4),
        "accuracy_pct": round(acc * 100, 2),
        "correct": correct,
        "total": total,
        "dataset_dir": str(DATA_DIR),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = sorted(DATA_DIR.glob("*.png"))[:3]
    if len(samples) < 3:
        print("Se necesitan al menos 3 imágenes en el dataset.")
        return 1

    fig_path = build_preprocess_figure(samples)
    print(f"Figura preproceso: {fig_path}")

    metrics = evaluate_accuracy()
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Accuracy: {metrics['accuracy_pct']}% ({metrics['correct']}/{metrics['total']})")
    print(f"Métricas: {METRICS_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
