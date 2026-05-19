"""Preprocesamiento OpenCV del captcha (mismo pipeline que Extraer_info_sufi)."""

from __future__ import annotations

import cv2
import numpy as np

IMG_WIDTH = 280
IMG_HEIGHT = 80


def preprocess_captcha_image(img: np.ndarray) -> np.ndarray:
    if img is None:
        raise ValueError("Imagen de captcha vacia")

    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img = cv2.bilateralFilter(img, d=15, sigmaColor=100, sigmaSpace=100)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    img = clahe.apply(img)
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    binarizada = cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=89,
        C=10,
    )
    img = cv2.medianBlur(binarizada, 3)
    return cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_AREA)
