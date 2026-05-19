# Demo end-to-end: Excel de prueba -> cola SQS -> (opcional) worker
param(
    [string]$JobId = "demo-001"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:AWS_ENDPOINT_URL = "http://localhost:4566"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"

Write-Host "==> Verificando Floci..."
docker compose ps

Write-Host "`n==> Bootstrap (idempotente)..."
python infrastructure\bootstrap\bootstrap.py

Write-Host "`n==> Excel de prueba..."
python scripts\create_sample_excel.py

$s3Key = "jobs/$JobId/placas.xlsx"
Write-Host "`n==> Encolando placas..."
python orchestrator\split_excel.py --job-id $JobId --s3-key $s3Key

Write-Host "`n==> Mensajes en cola:"
aws --endpoint-url http://localhost:4566 sqs get-queue-attributes `
    --queue-url "http://localhost:4566/000000000000/placas-jobs" `
    --attribute-names ApproximateNumberOfMessages

Write-Host @"

Demo listo. Para procesar con el worker (Playwright + TensorFlow):
  pip install -r worker/requirements.txt
  playwright install chromium
  Set-Location worker; python -m src.main

O con Docker:
  docker build -t placas-worker worker/
  docker run --rm -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 placas-worker
"@
