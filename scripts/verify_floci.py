"""Verifica conectividad con Floci: S3, SQS, DynamoDB."""

from __future__ import annotations

import os
import sys
import uuid

import boto3

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
CREDS = {"aws_access_key_id": "test", "aws_secret_access_key": "test"}


def client(service: str):
    return boto3.client(
        service, endpoint_url=ENDPOINT, region_name=REGION, **CREDS
    )


def main() -> int:
    print(f"Verificando Floci en {ENDPOINT}\n")
    ok = True

    # S3
    s3 = client("s3")
    test_key = f"verify/{uuid.uuid4().hex}.txt"
    try:
        s3.put_object(
            Bucket="placas-proyecto-input",
            Key=test_key,
            Body=b"floci-ok",
        )
        obj = s3.get_object(Bucket="placas-proyecto-input", Key=test_key)
        assert obj["Body"].read() == b"floci-ok"
        s3.delete_object(Bucket="placas-proyecto-input", Key=test_key)
        print("[OK] S3 read/write")
    except Exception as e:
        print(f"[FAIL] S3: {e}")
        ok = False

    # SQS
    sqs = client("sqs")
    try:
        url = sqs.get_queue_url(QueueName="placas-jobs")["QueueUrl"]
        sqs.send_message(QueueUrl=url, MessageBody='{"placa":"TEST123"}')
        msgs = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
        assert "Messages" in msgs
        sqs.delete_message(
            QueueUrl=url,
            ReceiptHandle=msgs["Messages"][0]["ReceiptHandle"],
        )
        print("[OK] SQS send/receive")
    except Exception as e:
        print(f"[FAIL] SQS: {e}")
        ok = False

    # DynamoDB
    dynamodb = client("dynamodb")
    try:
        job_id = f"verify-{uuid.uuid4().hex[:8]}"
        dynamodb.put_item(
            TableName="placas-jobs",
            Item={
                "job_id": {"S": job_id},
                "status": {"S": "VERIFY"},
            },
        )
        item = dynamodb.get_item(
            TableName="placas-jobs", Key={"job_id": {"S": job_id}}
        )
        assert item["Item"]["status"]["S"] == "VERIFY"
        dynamodb.delete_item(
            TableName="placas-jobs", Key={"job_id": {"S": job_id}}
        )
        print("[OK] DynamoDB read/write")
    except Exception as e:
        print(f"[FAIL] DynamoDB: {e}")
        ok = False

    print()
    if ok:
        print("Todas las verificaciones pasaron.")
        return 0
    print("Algunas verificaciones fallaron. Ejecuta bootstrap primero.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
