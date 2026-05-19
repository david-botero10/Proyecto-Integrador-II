"""Genera Excel de prueba con columnas RUNT y lo sube a S3 input."""

from __future__ import annotations

import io
import os
import sys

import boto3
from openpyxl import Workbook

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
JOB_ID = os.getenv("SAMPLE_JOB_ID", "demo-001")
S3_KEY = f"jobs/{JOB_ID}/placas.xlsx"


def main() -> int:
    wb = Workbook()
    ws = wb.active
    ws.title = "placas"
    ws.append(["numero_placas", "cod_id", "id"])
    samples = [
        ("ABC123", 2, "900123456"),
        ("XYZ789", 2, "800111222"),
        ("DEF456", 1, "123456"),
    ]
    for row in samples:
        ws.append(list(row))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    s3.put_object(
        Bucket="placas-proyecto-input",
        Key=S3_KEY,
        Body=buf.getvalue(),
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    print(f"Subido s3://placas-proyecto-input/{S3_KEY}")
    print(f"Ejecutar: python orchestrator/split_excel.py --job-id {JOB_ID} --s3-key {S3_KEY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
