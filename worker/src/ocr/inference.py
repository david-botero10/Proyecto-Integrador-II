"""Inferencia CRNN + CTC para captcha RUNT."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from .ctc_layer import CTCLayer
from .preprocess import IMG_HEIGHT, IMG_WIDTH, preprocess_captcha_image

CHARACTERS = list(
    "23456789ABCDEFGHJKMNPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)

_DEFAULT_MODEL = (
    Path(__file__).resolve().parent.parent.parent / "models" / "captcha_model.keras"
)


@lru_cache(maxsize=1)
def _prediction_model():
    model_path = os.getenv("CAPTCHA_MODEL_PATH", str(_DEFAULT_MODEL))
    if not Path(model_path).exists():
        alt = Path(__file__).resolve().parents[3] / "Modelo" / "OCR_captcha_model_V2_EX4 4.keras"
        if alt.exists():
            model_path = str(alt)
        else:
            raise FileNotFoundError(f"No se encontro modelo OCR en {model_path}")

    runt = keras.models.load_model(
        model_path, custom_objects={"CTCLayer": CTCLayer}, compile=False
    )
    return keras.models.Model(
        inputs=runt.inputs[0], outputs=runt.get_layer("dense2").output
    )


def _encode_for_model(img: np.ndarray) -> np.ndarray:
    img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
    img = img.astype(np.float32) / 255.0
    if len(img.shape) == 2:
        img = np.expand_dims(img, axis=-1)
    return np.transpose(img, (1, 0, 2))


def _decode_predictions(pred: np.ndarray, max_length: int = 6) -> list[str]:
    char_to_num = layers.StringLookup(vocabulary=CHARACTERS, mask_token=None)
    num_to_char = layers.StringLookup(
        vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True
    )
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
        :, :max_length
    ]
    texts: list[str] = []
    for res in results:
        indices = res.numpy()
        indices = indices[indices > 0]  # CTC blank shares index 0 with StringLookup OOV
        if len(indices) == 0:
            texts.append("")
        else:
            text = tf.strings.reduce_join(num_to_char(indices)).numpy().decode("utf-8")
            texts.append(text)
    return texts


def predict_captcha(image_gray: np.ndarray) -> str:
    """Predice texto del captcha desde imagen en escala de grises."""
    processed = preprocess_captcha_image(image_gray)
    batch = np.expand_dims(_encode_for_model(processed), axis=0)
    model = _prediction_model()
    preds = model.predict(batch, verbose=0)
    return _decode_predictions(preds)[0].strip()
