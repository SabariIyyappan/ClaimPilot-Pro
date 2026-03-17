import os
import uuid
from typing import Dict, Tuple

import boto3
from botocore.config import Config


class StorageConfigError(RuntimeError):
    pass


def _s3_client():
    region = os.environ.get("AWS_REGION", "us-east-1")
    # Retry mode "adaptive" is better under bursty/high traffic.
    cfg = Config(retries={"max_attempts": 10, "mode": "adaptive"})
    return boto3.client("s3", region_name=region, config=cfg)


def get_upload_bucket() -> str:
    bucket = os.environ.get("S3_UPLOAD_BUCKET", "").strip()
    if not bucket:
        raise StorageConfigError("S3_UPLOAD_BUCKET is not configured")
    return bucket


def _sanitize_filename(filename: str) -> str:
    safe = "".join(ch for ch in filename if ch.isalnum() or ch in ("-", "_", ".", " "))
    safe = safe.strip().replace(" ", "_")
    return safe or "upload.bin"


def build_upload_key(filename: str) -> str:
    prefix = os.environ.get("S3_UPLOAD_PREFIX", "uploads").strip().strip("/")
    ext = os.path.splitext(filename)[1].lower()
    token = uuid.uuid4().hex
    safe_name = _sanitize_filename(filename)
    return f"{prefix}/{token}-{safe_name}{'' if ext in safe_name else ext}"


def create_presigned_upload(filename: str, content_type: str, expires_in: int = 900) -> Tuple[str, str, Dict[str, str]]:
    bucket = get_upload_bucket()
    key = build_upload_key(filename)
    s3 = _s3_client()
    headers = {"Content-Type": content_type}
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
            "ServerSideEncryption": "aws:kms" if os.environ.get("S3_KMS_KEY_ID") else "AES256",
            **({"SSEKMSKeyId": os.environ.get("S3_KMS_KEY_ID")} if os.environ.get("S3_KMS_KEY_ID") else {}),
        },
        ExpiresIn=expires_in,
    )
    return url, key, headers


def download_object_bytes(key: str) -> bytes:
    bucket = get_upload_bucket()
    s3 = _s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()
