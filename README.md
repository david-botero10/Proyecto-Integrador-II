# Proyecto Integrador II — Consulta RUNT + OCR (CRNN+CTC) en AWS local

Pipeline de consulta masiva de placas en el **RUNT Colombia** con **Playwright**, resolución de captcha con modelo **CRNN + CTC** (TensorFlow/Keras), e integración cloud emulada con [Floci](https://github.com/floci-io/floci).

## Requisitos

- Docker Desktop (WSL2)
- Python 3.11+ (3.12 recomendado para el worker)
- AWS CLI v2 (opcional, para scripts PowerShell)

## Inicio rápido

```powershell
cd "c:\Users\davbo\Documents\Maestria en Ciencias de los Datos y Analitica\Proyecto Integrador II"

# 1. Levantar Floci
docker compose up -d

# 2. Entorno Python (orquestador y scripts)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# 3. Crear recursos AWS locales
python infrastructure\bootstrap\bootstrap.py

# 4. Verificar
python scripts\verify_floci.py

# 5. Demo: Excel de muestra → SQS
python scripts\create_sample_excel.py
.\scripts\run-demo.ps1 -JobId demo-001
```

Variables de entorno: copiar `.env.example` a `.env`.

## Estructura

```
docker-compose.yml          # Floci local
Modelo/                     # Código y notebook originales (referencia)
infrastructure/bootstrap/   # S3, SQS, DynamoDB, ECR
orchestrator/split_excel.py # Excel RUNT → SQS (numero_placas, cod_id, id)
worker/
  models/captcha_model.keras
  src/scraper.py            # Playwright + RUNT
  src/ocr/                  # preproceso OpenCV + inferencia CTC
docs/arquitectura.md
docs/presentacion.html      # Diapositivas (tecla P = presentación)
```

## Worker (Playwright + OCR)

```powershell
cd worker
pip install -r requirements.txt
playwright install chromium
$env:AWS_ENDPOINT_URL = "http://localhost:4566"
python -m src.main
```

Imagen Docker:

```powershell
docker build -t placas-worker worker/
docker run --rm -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 placas-worker
```

El modelo se carga desde `CAPTCHA_MODEL_PATH` (por defecto `worker/models/captcha_model.keras`).

## Excel de entrada

| Columna        | Descripción              |
|----------------|--------------------------|
| `numero_placas`| Placa a consultar        |
| `cod_id`       | Tipo documento (1=CC, 2=NIT, …) |
| `id`           | Número de documento      |

Subir a `s3://placas-proyecto-input/jobs/{job_id}/placas.xlsx` y ejecutar:

```powershell
python orchestrator/split_excel.py --job-id demo-001 --s3-key jobs/demo-001/placas.xlsx
```

Ver [docs/arquitectura.md](docs/arquitectura.md) para el diagrama completo y justificación de servicios AWS.

**Presentación:** abre [docs/presentacion.html](docs/presentacion.html) en el navegador.
