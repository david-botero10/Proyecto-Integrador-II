"""Clientes boto3 configurados para Floci o AWS real."""

from __future__ import annotations

import os

import boto3


def _endpoint() -> str | None:
    # Vacío explícito = AWS real; sin variable = Floci local
    if "AWS_ENDPOINT_URL" in os.environ:
        return os.environ["AWS_ENDPOINT_URL"] or None
    return "http://localhost:4566"


def _creds() -> dict:
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "test"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    }


def client(service: str):
    return boto3.client(
        service,
        endpoint_url=_endpoint(),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        **_creds(),
    )


def bucket_input() -> str:
    return os.getenv("S3_BUCKET_INPUT", "placas-proyecto-input")


def bucket_output() -> str:
    return os.getenv("S3_BUCKET_OUTPUT", "placas-proyecto-output")


def bucket_ml() -> str:
    return os.getenv("S3_BUCKET_ML", "placas-proyecto-ml")


def queue_name() -> str:
    return os.getenv("SQS_QUEUE_NAME", "placas-jobs")
