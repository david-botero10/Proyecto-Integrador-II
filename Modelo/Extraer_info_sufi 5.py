# IMPORTACIÓN DE LIBRERIAS

import pandas as pd
import os
import glob
import sys
import time
import warnings
import logging
import win32com.client as win32
import random
import re

# IMPORTACIÓN DE FUNCIONES
from functions import *

# IMPORTACIÓN DE PLAYWRIGHT
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# CONFIGURACIÓN DEL PATH

base_path =  os.getcwd()
warnings.filterwarnings("ignore")


# CONFIGURACIÓN DE LOGGING
logging.basicConfig(filename = r"C:\Auditoria\Usados\Prueba portal RUNT\Modelo\Prueba Runtlogger.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# DEFINICION DE RUTAS
imagen_path     =   fr"{base_path}\Insumos ejecucion\Imagen Captcha\captcha.png"
driver_path     =   fr"{base_path}\Insumos ejecucion\Driver\msedgedriver.exe"
edge_path       =   fr"{base_path}\Insumos ejecucion\Edge\msedge.exe"
placas_path     =   fr"{base_path}\Insumos ejecucion\Informe V2\Placas.xlsx"
resultados_path =   fr"{base_path}\Resultados\Resultados_vehiculos_sufi.xlsx"
error_path      =   fr"{base_path}\Resultados\Errores_consulta_sufi.xlsx"


# DEFINICION DE USER AGENTS PARA SIMULAR DIFERENTES DISPOSIIVOS
user_agents = [
    # Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/115.0.1901.203 Safari/537.36",

    # macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

    # Android
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",

    # iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]


def verificacion_formato_placas(placa):

    formatos_placas = {
        "Formato_carro" : r"^[A-Z]{3}[0-9]{3}$",
        "Formato_moto" : r"^[A-Z]{3}[0-9]{2}[A-Z]{1}$",
        "Formato_motocarro" : r"^[0-9]{3}[A-Z]{3}$"
    }
    
    for formato, regex in formatos_placas.items():
        if re.match(regex, placa):
            return True
    
    return False

def espera_aleatoria(inferior, superior):
    time.sleep(random.uniform(inferior, superior))

def guardar_error(error_actual, df_error, error_path):
    df_total = pd.concat([df_error, error_actual], ignore_index=True)
    df_total.to_excel(error_path, index=False)


def transformar_df_error(lista):
    columns = ['Placa', 'NIT', 'Mensaje']
    df = pd.DataFrame(lista, columns=columns)
    return df


def transformar_df_ejecucion(lista):
    columns = [
        'Placa',
        'Marca',
        'Modelo',
        'Chasis',
        'Cilindraje',
        'Tipo Combustible',
        'Linea',
        'Color',
        'Motor',
        'VIN',
        'Fecha Matricula',
        'Autoridad',
        'identificacion Acreedor Garantia',
        'Acreedor Garantia',
        'Fecha de Inicio Garantia',
        'Patrimonio Autonomo Garantia',
        'Confecámaras Garantia'
    ]
    df = pd.DataFrame([lista],columns = columns)
    
    return df


def limpiar_imagen(img):

    # Suavizados sin perder bordes
    #  d = diametro del area del filtro (9 a 15 - mas alto, mas suavizado)
    #  sigmaColor = Sensibilidad al color (50 a 100 - mas alto, mezcla mas tonos)
    #  sigmaSpace = Sensibilidad a la distancia espacial (50 a 100 - mas alto, suaviza zonas mas grandes)

    img = cv2.bilateralFilter(img, d=15, sigmaColor=100, sigmaSpace=100)

    # Mejora del contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    img = clahe.apply(img)
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    # Binarización adaptativa sin invertir (letras negras sobre fondo blanco)
    binarizada = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=89,  # más grande para suavizar variaciones
        C=10       # más alto para evitar que se rompan trazos finos
    )

    # Suavizado con filtro mediana para eliminar ruido sin perder bordes
    img = cv2.medianBlur(binarizada, 3)
    img = cv2.resize(img, (280, 80), interpolation=cv2.INTER_AREA)
    cv2.imwrite(imagen_path, img)
    return img


def Validacion_atributos_runt(page, nombre_atributo, xpath, tiempo_espera=10):
    intentos = 0
    texto = ""
    global captcha_fallo

    while intentos < 2:
        try:
            # Espera hasta que el elemento esté visible
            elemento = page.locator(f"xpath={xpath}").wait_for(state="visible", timeout=tiempo_espera * 3000)

            # Scroll al elemento
            page.locator(f"xpath={xpath}").scroll_into_view_if_needed()

            # Extraer texto
            texto = page.locator(f"xpath={xpath}").inner_text().strip()
            data.append(texto)
            print(f"{nombre_atributo}: {texto}")
            return  # Salir si fue exitoso

        except PlaywrightTimeout:
            intentos += 1
            print(f"Intento {intentos}: No se encontró '{nombre_atributo}'")
            time.sleep(1)

        except Exception as e:
            print(f"Error al extraer '{nombre_atributo}': {e}")
            break

    # Si no se logró extraer
    print(f"No se encontró el atributo '{nombre_atributo}' después de 3 intentos.")
    captcha_fallo = True


def extraccion_garantia(page, data):

    try:
        # Scroll al bloque de datos técnicos
        page.locator('xpath=/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[16]/cyrconsultavehiculo-garantias/mat-accordion/mat-expansion-panel/mat-expansion-panel-header').scroll_into_view_if_needed()
        time.sleep(1)

        # Click en botón SOAT
        page.click('xpath=/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/mat-sidenav-content/div/ng-component/div/div/div[2]/div[16]/cyrconsultavehiculo-garantias/mat-accordion/mat-expansion-panel/mat-expansion-panel-header')
        time.sleep(1)

        tabla = page.get_by_role("region", name="Garantías a Favor De").get_by_role("table")
        tabla.wait_for(state="visible", timeout=10000)
        
        filas = tabla.locator(".mat-row").all()
        if not filas:
            return []

        primera_fila = filas[0]
        celdas = primera_fila.locator(".mat-cell").all()

        garantia = [celda.inner_text().strip() for celda in celdas]
        data.extend(garantia)
    except PlaywrightTimeout:
        garantia = [""] * 5
        data.extend(garantia)


def cerrar_recursos(page, context, browser):
    page.close()
    context.close()
    browser.close()


def registrar_error(placa, mensaje, nivel="error"):
    if nivel == "error":
        logging.error(f"La consulta para la placa {placa} ha fallado: {mensaje}")
    else:
        logging.info(f"La consulta para la placa {placa}: {mensaje}")


# LECTURA DE ARCHIVO V2
placas_pruebas = pd.read_excel(placas_path)
df_error = pd.read_excel(error_path)



# VERIFICACION DE FORMATOS VALIDOS PARA APLICACION DE PRUEBAS
placas_pruebas["Valida"] = placas_pruebas["numero_placas"].apply(verificacion_formato_placas)
df_validas = placas_pruebas[placas_pruebas["Valida"]].drop(columns=["Valida"])
df_invalidas = placas_pruebas[~placas_pruebas["Valida"]].drop(columns=["Valida"])


# GUARDADO DE PLACAS INVALIDAS EN ARCHIVO DE ERRORES
df_invalidas = list(zip(df_invalidas["numero_placas"], ["000000000"] * len(df_invalidas), ["Formato de placa especial - Requiere validación manual"] * len(df_invalidas)))
guardar_error(transformar_df_error(df_invalidas), df_error, error_path)


# CONVERSION A LISTA DE PLACAS VALIDAS PARA PRUEBAS
placas_pruebas_list = list(zip(df_validas["cod_id"] , df_validas["id"], df_validas["numero_placas"]))


# INICIO DE PRUEBAS

times = 0 

for cod_id, id, placa in placas_pruebas_list:

    times += 1
    logging.info(f"Iniciando prueba {times} - Placa: {placa} - identificación: {id}")

    df_resultados = pd.read_excel(resultados_path)
    df_error = pd.read_excel(error_path)
    captcha_fallo = True

    if times % 10 == 0:
        # agregar espera de 1 min
        print("Espera")

    
    while captcha_fallo:

        try:
            data = []
            data_2 = []
            user_agent = random.choice(user_agents)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=edge_path, headless=True)
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US")
                page = context.new_page()

                # ACCEDER A LA PAGINA
                page.goto("https://www.runt.gov.co/consultaCiudadana/#/consultaVehiculo", timeout=60000)
                time.sleep(random.uniform(4, 8))
                start_time = time.time()

                # REPORTE POR CONSOLA 
                print(f"Prueba {times} - Placa: {placa} - Documento: {id}")

                # INGRESO PLACA
                page.fill('xpath=//*[@id="mat-input-0"]', str(placa))
                espera_aleatoria(2, 4)

                # CLICK PARA EL SELECTOR DE DOCUMENTO
                page.click('id=mat-select-4')

                # ESPERA A QUE APAREZCAN LAS OPCIONES
                page.wait_for_selector('mat-option', timeout=20000)

                # SELECCIONA TIPO DE DOCUMENTO (segundo elemento)
                if cod_id == 1:

                    options = page.locator('mat-option').all()
                    options[1].click()

                elif cod_id == 2:
                    id = str(id)
                    if len(id) > 6:
                        id = re.sub(r'^30*', '', id)
                    options = page.locator('mat-option').all()
                    options[2].click()

                elif cod_id == 3:
                    options = page.locator('mat-option').all()
                    options[3].click()

                # INGRESA DOCUMENTO
                page.fill('xpath=//*[@id="mat-input-1"]', str(id))
                espera_aleatoria(2, 4)
                # time.sleep(3)

                # Esperar a que el CAPTCHA esté disponible
                page.wait_for_selector("//img[contains(@src,'base64')]",state="visible", timeout=120000)

                # Localizar el CAPTCHA
                captcha_element = page.locator("//img[contains(@src,'base64')]")
                captcha_element.scroll_into_view_if_needed()

                # Capturar imagen del CAPTCHA
                captcha_element.screenshot(path=imagen_path)

                # Procesar imagen con modelo
                img = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)
                img = limpiar_imagen(img)
                text_captcha = prediction(img)[0].strip()

                # time.sleep(5)
                print("Texto CAPTCHA:", text_captcha)

                # Enviar el texto resuelto
                page.fill('xpath=//*[@id="mat-input-2"]', text_captcha)
                # time.sleep(4)
                page.keyboard.press("Enter")
                # time.sleep(6)

                try:
                    # Esperar el contenedor del mensaje
                    mensaje_elemento = page.wait_for_selector("#swal2-html-container", state="visible", timeout=4000)
                    captcha_mensaje = mensaje_elemento.inner_text().strip()

                    # Limpieza del texto
                    captcha_mensaje = captcha_mensaje.replace('Resultado Consulta', '')
                    captcha_mensaje = captcha_mensaje.replace('Aceptar', '')
                    captcha_mensaje = captcha_mensaje.replace('×', '')
                    captcha_mensaje = captcha_mensaje.replace('\n', '')

                    print(f"Captcha fallido- Mensaje: {captcha_mensaje}")

                    # DICICOANRIO DE CASOS POSIBLES DE MENSAJES DE CAPTCHA FALLIDO
                    mensajes_captcha = {
                        "El captcha no es valido.": {
                            "Mensaje": "Captcha mal ingresado",
                            "log": "El captcha no es valido.",
                            "fallo": True,
                            "accion": "cerrar"
                        },

                        "La imagen no coincide con el valor ingresado, por favor verifiquela e intente nuevamente.": {
                            "Mensaje": "Captcha mal ingresado",
                            "log": "La imagen no coincide con el valor ingresado.",
                            "fallo": True,
                            "accion": "cerrar"
                        },

                        "Señor Usuario, para el vehículo consultado no hay información registrada en el sistema RUNT.": {
                            "Mensaje": "Captcha EXITOSO pero no hay datos en RUNT",
                            "log": "No hay información registrada en el sistema RUNT.",
                            "fallo": False,
                            "accion": "guardar_break"
                        },
                        "Los datos registrados no corresponden con los propietarios activos para el vehículo consultado.": {
                            "Mensaje": f"Captcha EXITOSO pero no hay datos con este documento: {id}",
                            "log": "Datos incorrectos. Probando con otro nit...",
                            "fallo": False,
                            "accion": "guardar_break"
                        },
                        "Señor Usuario: El vehículo consultado aún no ha sido registrado en el sistema RUNT por el organismo de tránsito donde se encuentra matriculado. Le sugerimos dirigirse al mismo a solicitar el envío de su información, de lo contrario no se podrá realizar trámite de tránsito sobre el automotor.": {
                            "Mensaje": "Captcha EXITOSO pero no hay datos en RUNT",
                            "log": "El vehículo no ha sido registrado en el sistema RUNT. Probando con otro nit...",
                            "fallo": False,
                            "accion": "guardar_break"
                        }
                    }

                    if captcha_mensaje in mensajes_captcha:

                        caso = mensajes_captcha[captcha_mensaje]

                        print("FALLOOO " ,caso["Mensaje"])

                        print(caso["fallo"])

                        registrar_error(placa, caso["log"], nivel="error" if "fallo" in caso and caso["fallo"] else "info")


                        if caso["accion"] == "cerrar":
                            cerrar_recursos(page, context, browser)

                        elif caso["accion"] == "guardar":
                            data_2.append([placa, id, caso["Mensaje"]])
                            guardar_error(transformar_df_error(data_2), df_error, error_path)
                            captcha_fallo = caso["fallo"]
                            cerrar_recursos(page, context, browser)
                            
                        elif caso["accion"] == "guardar_break":
                            data_2.append([placa, id, caso["Mensaje"]])
                            guardar_error(transformar_df_error(data_2), df_error, error_path)
                            captcha_fallo = caso["fallo"]
                            cerrar_recursos(page, context, browser)
                            

                except PlaywrightTimeout:
                    print("Captcha ingresado correctamente o mensaje no apareció.")
                    

                    # EXTRACCIÓN DE ATRIBUTOS DEL VEHÍCULO
                    Validacion_atributos_runt(page, 'placa', placa_xpath)
                    Validacion_atributos_runt(page, 'marca', marca_xpath)
                    Validacion_atributos_runt(page, 'modelo', modelo_xpath)
                    Validacion_atributos_runt(page, 'chasis', chasis_xpath)
                    Validacion_atributos_runt(page, 'cilindraje', cilindraje_xpath)
                    Validacion_atributos_runt(page, 'tipo_combustible', tipo_combustible_xpath)
                    Validacion_atributos_runt(page, 'linea', linea_xpath)
                    Validacion_atributos_runt(page, 'color', color_xpath)
                    Validacion_atributos_runt(page, 'motor', motor_xpath)
                    Validacion_atributos_runt(page, 'vin', vin_xpath)
                    Validacion_atributos_runt(page, 'fecha_matricula', fecha_matricula_xpath)
                    Validacion_atributos_runt(page, 'autoridad', autoridad_xpath)
    

                    # TRANSFORMAR LA LISTA EN UN DF CON LAS COLUMNAS DEFINIDAS, SE CONCATENA CON LA INFORMACIÓN ACTUAL DEL EXCEL
                    extraccion_garantia(page, data)

                    df = transformar_df_ejecucion(data)


                    df_total = pd.concat([df_resultados, df], ignore_index=True)
                    df_total.to_excel(resultados_path, index=False)

                    print("INSERTADO")

                    # FINALIZA BÚSQUEDA DE PLACA DE MANERA EXITOSA
                    captcha_fallo = False
                    elapsed_time = time.time() - start_time

                    cerrar_recursos(page, context, browser)

                    # REPORTE EN EL LOGGER DE LA CONSULTA DE LA PLACA
                    logging.info(f'Finalizó la búsqueda para la placa {placa}')
                    logging.info(f'Tiempo transcurrido: {elapsed_time} segundos')
                    print(f"Tiempo transcurrido: {elapsed_time} segundos")

        
        except PlaywrightTimeout:
            logging.error(f"Timeout al cargar la pagina para la placa {placa}")
            print("La pagina no respondio en el tiempo estipulado")
            time.sleep(30)
            captcha_fallo  = True
        
        except Exception as e:
            logging.error(f"Error inesperado durante la consulta de {placa}: {e}")
            if "ERR_CONNECTION_TIMED_OUT" in str(e):
                logging.error(f"Conexión bloqueada para placa {placa}: {e}")
                print("La página bloqueó la conexión, esperando 1 hora antes de continuar...")
                time.sleep(3600)   # espera de 1 hora
                captcha_fallo = True
            else:
                logging.error(f"Error inesperado durante la consulta de {placa}: {e}")
                print(f"Error inesperado, reiniciando ciclo... {e}" )
                captcha_fallo = True

        finally:
            try:
                page.close()
                context.close()
                browser.close()
            except Exception as cierre_error:
                logging.warning(f"No se pudo cerrar correctamente el navegador: {cierre_error}")