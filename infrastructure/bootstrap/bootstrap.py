"""Crea recursos AWS locales contra Floci. Uso: python bootstrap.py"""

from __future__ import annotations

import json
import os
import sys

import boto3
from botocore.exceptions import ClientError

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
CREDS = {"aws_access_key_id": "test", "aws_secret_access_key": "test"}


def client(service: str):
    return boto3.client(
        service,
        endpoint_url=ENDPOINT,
        region_name=REGION,
        **CREDS,
    )


def ensure_bucket(s3, name: str) -> None:
    try:
        s3.head_bucket(Bucket=name)
        print(f"  S3 bucket exists: {name}")
    except ClientError:
        s3.create_bucket(Bucket=name)
        print(f"  S3 bucket created: {name}")


def ensure_queue(sqs, name: str, attributes: dict | None = None) -> str:
    try:
        url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
        print(f"  SQS queue exists: {name}")
    except ClientError:
        kwargs = {"QueueName": name}
        if attributes:
            kwargs["Attributes"] = attributes
        url = sqs.create_queue(**kwargs)["QueueUrl"]
        print(f"  SQS queue created: {name}")
    return url


def ensure_table(dynamodb, name: str, key_schema: list, attr_defs: list) -> None:
    existing = dynamodb.list_tables().get("TableNames", [])
    if name in existing:
        print(f"  DynamoDB table exists: {name}")
        return
    dynamodb.create_table(
        TableName=name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"  DynamoDB table created: {name}")


def main() -> int:
    print(f"==> Bootstrap against {ENDPOINT}")

    s3 = client("s3")
    sqs = client("sqs")
    dynamodb = client("dynamodb")
    ecr = client("ecr")

    for bucket in (
        "placas-proyecto-input",
        "placas-proyecto-output",
        "placas-proyecto-ml",
    ):
        ensure_bucket(s3, bucket)

    dlq_url = ensure_queue(sqs, "placas-jobs-dlq")
    dlq_arn = sqs.get_queue_attributes(
        QueueUrl=dlq_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]

    redrive = json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"})
    ensure_queue(sqs, "placas-jobs", {"RedrivePolicy": redrive})

    ensure_table(
        dynamodb,
        "placas-jobs",
        [{"AttributeName": "job_id", "KeyType": "HASH"}],
        [{"AttributeName": "job_id", "AttributeType": "S"}],
    )
    ensure_table(
        dynamodb,
        "placas-results",
        [
            {"AttributeName": "job_id", "KeyType": "HASH"},
            {"AttributeName": "placa", "KeyType": "RANGE"},
        ],
        [
            {"AttributeName": "job_id", "AttributeType": "S"},
            {"AttributeName": "placa", "AttributeType": "S"},
        ],
    )

    try:
        ecr.create_repository(repositoryName="placas-worker")
        print("  ECR repository created: placas-worker")
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryAlreadyExistsException":
            print("  ECR repository exists: placas-worker")
        else:
            raise

    print("\nBootstrap completado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
