from __future__ import annotations

import json
from io import BytesIO

from fcf.core.config import settings


class S3Store:
    def __init__(self):
        import boto3

        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_key,
            aws_secret_access_key=settings.s3_secret,
        )
        self.bucket = settings.s3_bucket

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self.bucket}/{key}"

    async def put_json(self, key: str, obj: dict) -> str:
        return await self.put(key, json.dumps(obj).encode(), "application/json")

    async def get(self, uri: str) -> bytes:
        bucket, key = _parse(uri)
        return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()

    async def exists(self, uri: str) -> bool:
        try:
            bucket, key = _parse(uri)
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    async def presign_public(self, uri: str, ttl_s: int = 3600) -> str:
        bucket, key = _parse(uri)
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl_s
        )


def _parse(uri: str) -> tuple[str, str]:
    rest = uri.removeprefix("s3://")
    bucket, _, key = rest.partition("/")
    return bucket, key
