"""Genera Documento Final RunAudit (Word) según plantilla MCDA 2026-1."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Documento_Final_RunAudit.docx"


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def add_para(doc: Document, text: str, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def build() -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Portada
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("Documento Final\n")
    r.bold = True
    r.font.size = Pt(18)
    r2 = title.add_run("RunAudit — Validación masiva de garantías vehiculares frente al RUNT\n")
    r2.font.size = Pt(14)
    r3 = title.add_run(
        "Proyecto Integrador II · Maestría en Ciencias de los Datos y Analítica · 2026-1\n\n"
        "David Botero · Jorge Giraldo · Samuel Padierna"
    )
    r3.font.size = Pt(12)
    doc.add_page_break()

    # 1. Introducción
    add_heading(doc, "1. Introducción", 1)
    add_heading(doc, "Contexto del problema", 2)
    add_para(
        doc,
        "Las entidades financieras que otorgan créditos con garantía vehicular deben auditar "
        "periódicamente su portafolio contra el Registro Único Nacional de Tránsito (RUNT), "
        "fuente oficial en Colombia de propietario, características técnicas y estado de "
        "garantías prendarias. El portal ciudadano del RUNT exige un CAPTCHA visual que "
        "impide la consulta programática; el proceso manual (placa por placa) no escala "
        "cuando el portafolio alcanza decenas de miles de vehículos, generando riesgo "
        "operativo, exposición crediticia no detectada y decisiones con información desactualizada.",
    )
    add_heading(doc, "Objetivo del proyecto", 2)
    add_para(
        doc,
        "Diseñar e implementar RunAudit: un sistema que combine reconocimiento óptico de "
        "caracteres (OCR) con aprendizaje profundo (CRNN + CTC) y web scraping (Playwright) "
        "para automatizar consultas masivas al RUNT, integrado en una arquitectura cloud "
        "(AWS) con prototipo local emulado (Floci). El objetivo es reducir el cuello de "
        "botella del CAPTCHA y entregar resultados estructurados por placa (JSON en S3, "
        "estado en DynamoDB) a partir de un Excel de entrada del banco.",
    )

    # 2. Marco teórico
    add_heading(doc, "2. Marco teórico", 1)
    add_heading(doc, "Fundamentos de los métodos utilizados", 2)
    add_para(
        doc,
        "Reconocimiento óptico de caracteres (OCR): tarea de extraer texto desde imágenes. "
        "En CAPTCHAs, las distorsiones y el ruido dificultan la segmentación clásica; se "
        "modela como reconocimiento de secuencias de longitud variable.",
    )
    add_para(
        doc,
        "Redes convolucionales (CNN): extraen características espaciales jerárquicas "
        "(bordes, trazos). En este proyecto, dos bloques Conv2D + MaxPooling reducen la "
        "resolución y alimentan la parte recurrente.",
    )
    add_para(
        doc,
        "BiLSTM: captura dependencias secuenciales en ambos sentidos, útil cuando un "
        "carácter es ambiguo sin contexto vecino.",
    )
    add_para(
        doc,
        "CTC (Connectionist Temporal Classification): permite entrenar sin alineación "
        "frame a carácter; la decodificación greedy colapsa repeticiones y blanks en la "
        "secuencia final (Graves et al., 2006).",
    )
    add_para(
        doc,
        "Web scraping con Playwright: automatización de navegador real para portales con "
        "JavaScript dinámico, formularios y controles anti-bot.",
    )
    add_para(
        doc,
        "Preprocesamiento OpenCV: filtro bilateral, CLAHE y umbral adaptativo para "
        "homogenizar captchas antes de la inferencia.",
    )
    add_heading(doc, "Referencias", 2)
    refs = [
        "Graves, A., Fernández, S., Gómez, F., & Schmidhuber, J. (2006). Connectionist temporal classification: labelling unsegmented sequence data with recurrent neural networks. ICML.",
        "Abadi, M., et al. (2016). TensorFlow: Large-scale machine learning on heterogeneous systems. tensorflow.org.",
        "Microsoft (2024). Playwright documentation. playwright.dev.",
        "Ministerio de Transporte de Colombia. Registro Único Nacional de Tránsito — Consulta ciudadana. runt.gov.co",
        "Amazon Web Services. Documentación de S3, SQS, Lambda, ECS, Step Functions, DynamoDB y SageMaker.",
        "Floci.io. Emulador local de servicios AWS para desarrollo.",
    ]
    for i, ref in enumerate(refs, 1):
        add_para(doc, f"[{i}] {ref}")

    # 3. Desarrollo metodológico
    add_heading(doc, "3. Desarrollo metodológico", 1)

    add_heading(doc, "3.1 Problema", 2)
    add_heading(doc, "Definición del problema (negocio, técnico o científico)", 3)
    add_para(
        doc,
        "Negocio: validar masivamente placas del portafolio contra el RUNT para detectar "
        "inconsistencias (cambio de propietario, gravámenes, bajas) sin operación manual.",
    )
    add_para(
        doc,
        "Técnico: superar el CAPTCHA del portal para habilitar scraping confiable y "
        "escalable; orquestar miles de consultas con reintentos y trazabilidad.",
    )
    add_heading(doc, "Hipótesis", 3)
    add_para(
        doc,
        "Un modelo CRNN+CTC entrenado con captchas etiquetados del mismo dominio visual "
        "del RUNT alcanza suficiente exactitud de secuencia (≥85 % en validación hold-out) "
        "para viabilizar la automatización del flujo end-to-end cuando se integra con "
        "Playwright y una cola de mensajes por placa.",
    )

    add_heading(doc, "3.2 Datos", 2)
    add_heading(doc, "Fuentes de datos", 3)
    add_bullets(
        doc,
        [
            "Imágenes captcha etiquetadas (~3.457 PNG): nombre de archivo = texto del captcha (entrenamiento OCR). Carpeta: Modelo/Imagenes Modelo V2 Limpias.",
            "Excel operativo del banco (batch): columnas numero_placas, cod_id, id — ingesta de jobs.",
            "Portal RUNT (salida no estructurada → JSON): datos del vehículo tras consulta exitosa.",
        ],
    )
    add_heading(doc, "Descripción y naturaleza", 3)
    add_para(
        doc,
        "Datos de entrenamiento: no estructurados (imágenes), etiqueta débil vía nombre de "
        "archivo, procesamiento offline en batch. Datos operativos: estructurados (Excel, "
        "JSON, DynamoDB). No se usa streaming en tiempo real; el flujo es por lotes (job_id) "
        "con cola SQS desacoplada.",
    )

    add_heading(doc, "3.3 Análisis Exploratorio de Datos (EDA)", 2)
    add_heading(doc, "Entendimiento de los datos", 3)
    add_para(
        doc,
        "El conjunto comprende 3.457 captchas con 56 caracteres alfabéticos distintos "
        "(sin 0/O/1/I/L para reducir ambigüedad). Longitud máxima de etiqueta: 6 caracteres. "
        "Split 90 % entrenamiento / 10 % validación (346 captchas).",
    )
    add_heading(doc, "Preparación y limpieza", 3)
    add_para(
        doc,
        "Pipeline OpenCV: escala de grises → filtro bilateral → CLAHE → umbral adaptativo "
        "→ operaciones morfológicas → redimensionado (280×80 px en worker; 210×60 en notebook "
        "de entrenamiento). Etiquetado: StringLookup de TensorFlow (índice 0 reservado; "
        "caracteres desde índice 1).",
    )
    add_heading(doc, "Análisis descriptivo", 3)
    add_para(
        doc,
        "Distribución de caracteres y longitudes de captcha revisada en el notebook "
        "Modelo Experimental.ipynb. Se observan pares visualmente confundibles (p. ej. "
        "o/a, m/n) que explican parte de los errores residuales del modelo.",
    )
    add_heading(doc, "Identificación de patrones relevantes", 3)
    add_para(
        doc,
        "La calidad del preprocesamiento correlaciona con legibilidad del texto en la "
        "imagen binarizada; no implica causalidad directa sobre accuracy sin control "
        "experimental. Los errores del OCR se concentran en caracteres similares, no "
        "en fallos aleatorios uniformes.",
    )

    add_heading(doc, "3.4 Modelado", 2)
    add_heading(doc, "Métodos Estadísticos (si aplica)", 3)
    add_para(
        doc,
        "No se emplearon modelos estadísticos clásicos (regresión, series) para la "
        "predicción del captcha; el problema se abordó con aprendizaje profundo.",
    )
    add_heading(doc, "Aprendizaje Profundo", 3)
    add_heading(doc, "Arquitecturas utilizadas", 4)
    add_para(
        doc,
        "CRNN: entrada (ancho × alto × 1) → Conv2D(32) + MaxPool → Conv2D(64) + MaxPool → "
        "Reshape → Dense(64) → Dropout → BiLSTM(128) → BiLSTM(64) → Dense(softmax) por "
        "timestep → capa CTC. Salida: secuencia de hasta 6 caracteres.",
    )
    add_heading(doc, "Función de pérdida, optimización", 4)
    add_para(
        doc,
        "Pérdida CTC (ctc_batch_cost) integrada en capa personalizada CTCLayer. "
        "Optimizador: Adam (lr inicial 1e-3).",
    )
    add_heading(doc, "Estrategia de entrenamiento", 4)
    add_para(
        doc,
        "Entrenamiento hasta 300 épocas con EarlyStopping (patience 10, monitor val_loss). "
        "En ejecución documentada, el entrenamiento detuvo ~época 159; val_loss descendió "
        "de ~346 a ~118. Batch size 16; tf.data con padding de etiquetas.",
    )
    add_heading(doc, "Evaluación", 3)
    add_heading(doc, "Métricas seleccionadas", 4)
    add_para(
        doc,
        "Acierto exacto de secuencia (exact match): porcentaje de captchas cuya predicción "
        "coincide íntegramente con la etiqueta. Métrica alineada al uso en RUNT (texto "
        "completo correcto). val_loss CTC como métrica de entrenamiento.",
    )
    add_heading(doc, "Estrategia de validación", 4)
    add_para(
        doc,
        "Hold-out 10 % (346 imágenes), sin fugas entre train y valid. Decodificación CTC "
        "greedy filtrando índice 0 (blank/UNK) antes de mapear a caracteres.",
    )
    add_heading(doc, "Comparación de enfoques", 4)
    add_para(
        doc,
        "Se descartó segmentación carácter a carácter por costo de etiquetado. CTC "
        "permite fin-a-fin. Inferencia en el mismo contenedor ECS que Playwright (vs. "
        "SageMaker Endpoint) por latencia y tamaño del modelo (~7.5 MB).",
    )
    add_para(doc, "Resultado principal: 87.7 % de acierto exacto en validación (303/346).", bold=True)

    # 4. MLOps
    add_heading(doc, "4. Tecnología — Sistemas de Aprendizaje Automático (MLOps)", 1)
    add_heading(doc, "4.1 Datos", 2)
    add_para(
        doc,
        "Ingesta batch: Excel a S3 (placas-proyecto-input), validación con Lambda (diseño), "
        "registro de job en DynamoDB. Mensajes SQS por placa (orchestrator/split_excel.py).",
    )
    add_heading(doc, "4.2 Procesamiento", 2)
    add_para(
        doc,
        "Entrenamiento: tf.data.Dataset, encode_single_sample, padded_batch. Operación: "
        "OpenCV en worker/src/ocr/preprocess.py. Herramientas: TensorFlow/Keras, OpenCV, "
        "pandas (Excel), boto3.",
    )
    add_heading(doc, "4.3 Entrenamiento", 2)
    add_para(
        doc,
        "Local: CPU/GPU según hardware del desarrollador (notebook). Producción diseñada: "
        "SageMaker Training Job para reentrenamiento con captchas fallidos en S3 ML. "
        "Pipeline: notebook → export .keras → scripts/sync_captcha_model.py.",
    )
    add_heading(doc, "4.4 Almacenamiento", 2)
    add_bullets(
        doc,
        [
            "S3 input: Excel por job.",
            "S3 output: JSON por placa consultada.",
            "S3 ML: captchas fallidos y datasets de reentrenamiento.",
            "DynamoDB: estado de jobs y resultados.",
            "ECR: imagen Docker del worker.",
            "Artefacto: worker/models/captcha_model.keras.",
        ],
    )
    add_heading(doc, "4.5 Despliegue", 2)
    add_para(
        doc,
        "Producción (diseño AWS): API Gateway → Lambda → Step Functions → SQS → ECS "
        "Fargate (Playwright + TensorFlow). DLQ para reintentos. Escalabilidad horizontal "
        "de workers según profundidad de cola. Latencia dominada por navegación RUNT, no "
        "solo por OCR.",
    )
    add_para(
        doc,
        "Prototipo local: Floci (localhost:4566) emula S3, SQS, DynamoDB, ECR; demo con "
        "run-demo.ps1.",
    )
    add_heading(doc, "4.6 Aplicación", 2)
    add_para(
        doc,
        "Consumo: archivos JSON en S3 y consulta de estado en DynamoDB; integración "
        "bancaria vía tablero o downstream ETL (fuera de alcance del MVP). Sin UI "
        "final de usuario; foco en pipeline automatizado.",
    )

    # 5. Resultados
    add_heading(doc, "5. Resultados", 1)
    add_heading(doc, "Análisis de desempeño", 2)
    add_para(
        doc,
        "OCR: 87.7 % exactitud en validación (346 captchas). val_loss CTC ~118 al final "
        "del entrenamiento. Pipeline E2E: Excel → SQS → worker implementado con demo "
        "reproducible en Floci.",
    )
    add_heading(doc, "Interpretación de resultados", 2)
    add_para(
        doc,
        "El modelo resuelve la mayoría de captchas del dominio entrenado; los errores "
        "restantes limitan la tasa de consultas exitosas al RUNT y requieren reintento "
        "o reentrenamiento con nuevas muestras. El impacto operativo esperado (propuesta "
        "inicial): reducción de semanas a horas frente a proceso manual.",
    )
    add_heading(doc, "Limitaciones", 2)
    add_bullets(
        doc,
        [
            "Dependencia del estilo actual del CAPTCHA RUNT; cambios visuales exigen reentrenamiento.",
            "Uso académico; respeto a términos del portal y límites de concurrencia.",
            "Desalineación temporal entre dimensiones de entrenamiento (notebook) y artefacto desplegado (280×80) si no se sincroniza el .keras.",
            "No se midió aún tasa de éxito end-to-end en producción con miles de placas reales.",
        ],
    )

    # 6. Conclusiones
    add_heading(doc, "6. Conclusiones", 1)
    add_heading(doc, "Aportes del proyecto", 2)
    add_bullets(
        doc,
        [
            "Sistema RunAudit: OCR CRNN+CTC + scraping Playwright + arquitectura AWS documentada.",
            "Dataset etiquetado de 3.457 captchas y modelo con 87.7 % en validación.",
            "Prototipo local reproducible (Floci) y documentación técnica (arquitectura.md).",
        ],
    )
    add_heading(doc, "Posibles mejoras", 2)
    add_bullets(
        doc,
        [
            "Unificar dimensiones entrenamiento/despliegue y versionar modelos en SageMaker Registry.",
            "Métricas por carácter (CER) y análisis de confusiones.",
            "Aumento de datos y hardening del scraper ante cambios del portal.",
        ],
    )
    add_heading(doc, "Trabajo futuro", 2)
    add_bullets(
        doc,
        [
            "Despliegue en AWS real con Step Functions y monitoreo CloudWatch.",
            "Loop de retroalimentación: captchas fallidos → S3 ML → reentrenamiento automático.",
            "Dashboard de auditoría para analistas de riesgo del banco.",
        ],
    )

    # 7. Referencias
    add_heading(doc, "7. Referencias", 1)
    for i, ref in enumerate(refs, 1):
        add_para(doc, f"[{i}] {ref}")

    # Márgenes
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2.5)

    return doc


def main() -> None:
    doc = build()
    doc.save(OUT)
    print(f"Generado: {OUT}")


if __name__ == "__main__":
    main()
