"""Worker: consume SQS, consulta RUNT, persiste resultados."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

from .aws_client import bucket_output, client, queue_name
from .scraper import scrape_plate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MAX_MESSAGES = int(os.getenv("WORKER_MAX_MESSAGES", "10"))
WAIT_SECONDS = int(os.getenv("WORKER_WAIT_SECONDS", "5"))
IDLE_ROUNDS = int(os.getenv("WORKER_IDLE_ROUNDS", "3"))


def process_message(body: dict) -> None:
    job_id = body["job_id"]
    placa = body["placa"]
    cod_id = int(body.get("cod_id", 1))
    documento_id = body.get("documento_id") or body.get("id", "")

    log.info("Procesando job=%s placa=%s cod_id=%s", job_id, placa, cod_id)

    result = scrape_plate(cod_id=cod_id, documento_id=documento_id, placa=placa)
    s3 = client("s3")
    dynamodb = client("dynamodb")

    out_key = f"jobs/{job_id}/results/{placa}.json"
    payload = {
        "job_id": job_id,
        "placa": placa,
        "cod_id": cod_id,
        "documento_id": str(documento_id),
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "elapsed_seconds": result.elapsed_seconds,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    s3.put_object(
        Bucket=bucket_output(),
        Key=out_key,
        Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )

    status = "SUCCESS" if result.success else "FAILED"
    dynamodb.put_item(
        TableName=os.getenv("DYNAMODB_TABLE_PLACAS", "placas-results"),
        Item={
            "job_id": {"S": job_id},
            "placa": {"S": placa},
            "status": {"S": status},
            "s3_key": {"S": out_key},
        },
    )
    log.info("Resultado %s -> s3://%s/%s", status, bucket_output(), out_key)


def run_once(sqs, queue_url: str) -> int:
    resp = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=min(MAX_MESSAGES, 10),
        WaitTimeSeconds=WAIT_SECONDS,
    )
    messages = resp.get("Messages", [])
    for msg in messages:
        body = json.loads(msg["Body"])
        try:
            process_message(body)
        finally:
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=msg["ReceiptHandle"],
            )
    return len(messages)


def main() -> int:
    sqs = client("sqs")
    queue_url = sqs.get_queue_url(QueueName=queue_name())["QueueUrl"]
    log.info("Worker RUNT iniciado. Cola: %s", queue_url)

    idle = 0
    while idle < IDLE_ROUNDS:
        n = run_once(sqs, queue_url)
        if n == 0:
            idle += 1
            time.sleep(1)
        else:
            idle = 0

    log.info("Sin mensajes tras %s rondas. Saliendo.", IDLE_ROUNDS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
