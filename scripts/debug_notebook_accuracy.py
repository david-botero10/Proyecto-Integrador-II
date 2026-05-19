"""Diagnostico accuracy 0% — replica logica del notebook."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Modelo" / "Imagenes Modelo V2 Limpias"
MODEL_PATH = ROOT / "worker" / "models" / "captcha_model.keras"
if not MODEL_PATH.exists():
    MODEL_PATH = ROOT / "Modelo" / "OCR_captcha_model_V2_EX4 4.keras"


class CTCLayer(keras.layers.Layer):
    def __init__(self, trainable=True, name=None, dtype=None, **kwargs):
        super().__init__(trainable=trainable, name=name, dtype=dtype, **kwargs)
        self.loss_fn = keras.backend.ctc_batch_cost

    def call(self, y_true, y_pred):
        return y_pred

    def get_config(self):
        return super().get_config()

    @classmethod
    def from_config(cls, config):
        return cls(**config)


def main() -> None:
    images = sorted(map(str, DATA_DIR.glob("**/*.png")))
    labels = [p.split(os.path.sep)[-1].split(".png")[0] for p in images]
    characters = sorted({c for lb in labels for c in lb})
    max_length = max(len(lb) for lb in labels)
    # Debe coincidir con el modelo guardado (notebook actual: 210x60; .keras antiguo: 280x80)
    img_width, img_height = 280, 80
    batch_size = 16

    char_to_num = layers.StringLookup(vocabulary=list(characters), mask_token=None)
    num_to_char = layers.StringLookup(
        vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True
    )

    def encode_single_sample(img_path, label):
        img = tf.io.read_file(img_path)
        img = tf.io.decode_png(img, channels=1)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.image.resize(img, [img_height, img_width])
        img = tf.transpose(img, perm=[1, 0, 2])
        label_enc = char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
        return {"image": img, "label": label_enc}

    def label_to_text(label):
        label = label[label != 0]
        return tf.strings.reduce_join(num_to_char(label)).numpy().decode("utf-8")

    def decode_batch_predictions(pred):
        input_len = np.ones(pred.shape[0]) * pred.shape[1]
        results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
            :, :max_length
        ]
        out = []
        for res in results:
            indices = res.numpy()
            indices = indices[indices > 0]
            if len(indices) == 0:
                out.append("")
            else:
                text = tf.strings.reduce_join(num_to_char(indices)).numpy().decode("utf-8")
                out.append(text)
        return out

    # split 90/10
    n = len(images)
    idx = np.arange(n)
    np.random.seed(42)
    np.random.shuffle(idx)
    train_n = int(n * 0.9)
    x_valid = np.array(images)[idx[train_n:]]
    y_valid = np.array(labels)[idx[train_n:]]

    val_ds = (
        tf.data.Dataset.from_tensor_slices((x_valid, y_valid))
        .map(encode_single_sample, num_parallel_calls=tf.data.AUTOTUNE)
        .padded_batch(
            batch_size,
            padded_shapes={"image": [img_width, img_height, 1], "label": [max_length]},
            padding_values={"image": 0.0, "label": tf.constant(0, dtype=tf.int64)},
        )
    )

    print("Loading", MODEL_PATH)
    full = keras.models.load_model(str(MODEL_PATH), custom_objects={"CTCLayer": CTCLayer}, compile=False)
    pred_model = keras.models.Model(
        inputs=full.inputs[0],
        outputs=full.get_layer("dense2").output,
    )

    y_true, y_pred = [], []
    for batch in val_ds:
        preds = pred_model.predict(batch["image"], verbose=0)
        y_pred.extend(decode_batch_predictions(preds))
        for label in batch["label"]:
            y_true.append(label_to_text(label))

    correct = sum(t == p for t, p in zip(y_true, y_pred))
    print(f"valid: {len(y_true)}, correct: {correct}, acc: {correct/len(y_true):.2%}")
    print("\nFirst 10 comparisons:")
    for i in range(10):
        match = "OK" if y_true[i] == y_pred[i] else "X"
        print(f"  {match} true={y_true[i]!r} pred={y_pred[i]!r}")

    # Check if preds are all empty
    empty_pred = sum(1 for p in y_pred if not p)
    print(f"\nEmpty predictions: {empty_pred}/{len(y_pred)}")


if __name__ == "__main__":
    main()
