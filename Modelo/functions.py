import cv2
import numpy as np
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow as tf
import os
import pandas as pd


# CARGAR MODELO
class CTCLayer(layers.Layer):
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


# CARGAR MODELO ENTRENADO
model_path = r'C:\Auditoria\Usados\Prueba portal RUNT\Modelo\OCR_captcha_model_V2_EX4.keras'
runt = keras.models.load_model(model_path, custom_objects={'CTCLayer': CTCLayer})

# CREACION DE MODELO MAS LIGERO AL EXTRAER LA PARTE DEL MODELO DENSE2
prediction_model = keras.models.Model(inputs=runt.inputs[0], outputs=runt.get_layer("dense2").output)

# DICCIONARIO DE CARACTERES
characters = ['2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
char_to_num = layers.StringLookup(vocabulary=list(characters), mask_token=None)
num_to_char = layers.StringLookup(vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True)


# REDIMENCIÓN, NORMALIZACIÓN, ESCALA DE GRISES Y TRANSPOCISIÓN DE LA IMAGEN POR SI EL MODELO ESPERA (width, height, channels)
def encode_single_sample2(img):
    img_width = 280
    img_height = 80
    img = cv2.resize(img, (img_width, img_height))
    img = img.astype(np.float32) / 255.0
    if len(img.shape) == 2:
        img = np.expand_dims(img, axis=-1)
    img = np.transpose(img, (1, 0, 2))
    return {"image": img}


# DECODIFICACIÓN
def decode_batch_predictions(pred, max_length=6):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
        :, :max_length
    ]
    output_text = []
    for res in results:
        indices = res.numpy()
        indices = indices[indices > 0]
        if len(indices) == 0:
            output_text.append("")
        else:
            text = tf.strings.reduce_join(num_to_char(indices)).numpy().decode("utf-8")
            output_text.append(text)
    return output_text




# REALIZA LA PREDICCION
def prediction(img):

    preprocessed = encode_single_sample2(img)
    batch_img = np.expand_dims(preprocessed["image"], axis=0)
    preds = prediction_model.predict(batch_img)
    decoded = decode_batch_predictions(preds)
    
    
    return decoded


################################### PATHS ##############################################################

placa_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[1]/div[2]/div/div/div[1]/div[2]'
marca_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[1]/div[2]'
modelo_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[2]/div[2]'
chasis_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[4]/div[2]'
cilindraje_xpath ='/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[5]/div[2]'
tipo_combustible_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[6]/div[2]'
linea_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[1]/div[4]'
color_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[2]/div[4]'
motor_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[3]/div[4]'
vin_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[4]/div[4]'
fecha_matricula_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[6]/div[4]'
autoridad_xpath = '/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[2]/cyrconsultavehiculo-info-vehiculo-detallada/div/div[2]/div/div[2]/div[1]/div[7]/div[2]'

################################### PATHS ##############################################################
