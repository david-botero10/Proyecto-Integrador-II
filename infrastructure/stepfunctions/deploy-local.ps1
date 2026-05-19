# Registra state machine en Floci (requiere Floci levantado)
param(
    [string]$Endpoint = "http://localhost:4566",
    [string]$Name = "placas-pipeline"
)

$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"

$definition = Get-Content -Raw "$PSScriptRoot\placas-pipeline.asl.json"

Write-Host "Creando state machine $Name..."
aws --endpoint-url $Endpoint stepfunctions create-state-machine `
    --name $Name `
    --definition $definition `
    --role-arn "arn:aws:iam::000000000000:role/floci-stepfunctions" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Si ya existe, puedes iniciar una ejecución con:"
}
Write-Host @"

Ejemplo de ejecución:
aws --endpoint-url $Endpoint stepfunctions start-execution `
    --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:$Name `
    --input '{\"job_id\":\"demo-001\",\"s3_key\":\"jobs/demo-001/placas.xlsx\"}'
"@
