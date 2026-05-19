# Crea recursos AWS locales contra Floci (localhost:4566)
param(
    [string]$Endpoint = "http://localhost:4566",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = $Region

$aws = @("aws", "--endpoint-url", $Endpoint)

Write-Host "==> Verificando Floci en $Endpoint..."
try {
    & aws --endpoint-url $Endpoint s3 ls 2>$null
} catch {
    Write-Error "Floci no responde. Ejecuta: docker compose up -d"
}

Write-Host "==> Creando buckets S3..."
& @aws s3 mb "s3://placas-proyecto-input" 2>$null
& @aws s3 mb "s3://placas-proyecto-output" 2>$null
& @aws s3 mb "s3://placas-proyecto-ml" 2>$null

Write-Host "==> Creando cola DLQ..."
$dlqUrl = (& @aws sqs create-queue --queue-name placas-jobs-dlq --output text --query QueueUrl) 2>$null
if (-not $dlqUrl) {
    $dlqUrl = "http://localhost:4566/000000000000/placas-jobs-dlq"
}

$dlqArn = (& @aws sqs get-queue-attributes --queue-url $dlqUrl --attribute-names QueueArn --output text --query 'Attributes.QueueArn')

Write-Host "==> Creando cola principal con redrive a DLQ..."
$redrive = "{`"deadLetterTargetArn`":`"$dlqArn`",`"maxReceiveCount`":`"3`"}"
& @aws sqs create-queue --queue-name placas-jobs --attributes "RedrivePolicy=$redrive" 2>$null

Write-Host "==> Creando tablas DynamoDB..."
& @aws dynamodb create-table `
    --table-name placas-jobs `
    --attribute-definitions AttributeName=job_id,AttributeType=S `
    --key-schema AttributeName=job_id,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST 2>$null

& @aws dynamodb create-table `
    --table-name placas-results `
    --attribute-definitions AttributeName=job_id,AttributeType=S AttributeName=placa,AttributeType=S `
    --key-schema AttributeName=job_id,KeyType=HASH AttributeName=placa,KeyType=RANGE `
    --billing-mode PAY_PER_REQUEST 2>$null

Write-Host "==> Creando repositorio ECR..."
& @aws ecr create-repository --repository-name placas-worker 2>$null

Write-Host ""
Write-Host "Bootstrap completado."
Write-Host "  S3:  placas-proyecto-input, placas-proyecto-output, placas-proyecto-ml"
Write-Host "  SQS: placas-jobs (DLQ: placas-jobs-dlq)"
Write-Host "  DDB: placas-jobs, placas-results"
Write-Host "  ECR: placas-worker"
