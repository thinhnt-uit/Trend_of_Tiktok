"""
MinIO / S3 helper functions for uploading and downloading raw JSON.
"""

import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()


def _get_s3_client():
    kwargs = {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        "region_name": os.getenv("AWS_REGION", "us-east-1"),
    }
    endpoint = os.getenv("S3_ENDPOINT_URL")
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.client("s3", **kwargs)


def _bucket():
    return os.getenv("S3_BUCKET_NAME", "tiktok-explore-raw")


def upload_json_to_s3(s3_key: str, data: dict):
    """Upload a Python dict as JSON to S3 / MinIO."""
    client = _get_s3_client()
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        Bucket=_bucket(), Key=s3_key, Body=body, ContentType="application/json"
    )
    print(f"[S3] Uploaded -> s3://{_bucket()}/{s3_key}")


def read_json_from_s3(s3_key: str) -> dict:
    """Download and parse a JSON file from S3 / MinIO."""
    client = _get_s3_client()
    response = client.get_object(Bucket=_bucket(), Key=s3_key)
    return json.loads(response["Body"].read().decode("utf-8"))
