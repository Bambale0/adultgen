"""S3-compatible object storage adapter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import boto3
from botocore.client import BaseClient

from adultgen.storage.ports import StoredObject


@dataclass(frozen=True, slots=True)
class S3ObjectStorageConfig:
    """Connection settings for S3-compatible storage."""

    endpoint_url: str
    access_key: str
    secret_key: str
    region_name: str = "us-east-1"


class S3ObjectStorage:
    """S3/MinIO-backed object storage.

    boto3 is sync-only here, so operations are dispatched through asyncio.to_thread.
    The rest of the application keeps using the async ObjectStorage protocol.
    """

    def __init__(self, config: S3ObjectStorageConfig) -> None:
        self.client: BaseClient = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region_name,
        )

    async def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
    ) -> None:
        """Persist an object into S3-compatible storage."""

        await asyncio.to_thread(
            self.client.put_object,
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    async def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        content_type: str,
    ) -> None:
        """Copy an object between S3 buckets/keys."""

        await asyncio.to_thread(
            self.client.copy_object,
            Bucket=target_bucket,
            Key=target_key,
            CopySource={"Bucket": source_bucket, "Key": source_key},
            ContentType=content_type,
            MetadataDirective="REPLACE",
        )

    async def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete an object if it exists."""

        await asyncio.to_thread(self.client.delete_object, Bucket=bucket, Key=key)

    async def get_object(self, *, bucket: str, key: str, content_type: str) -> StoredObject:
        """Read object bytes from S3-compatible storage."""

        response = await asyncio.to_thread(self.client.get_object, Bucket=bucket, Key=key)
        body = await asyncio.to_thread(response["Body"].read)
        resolved_content_type = response.get("ContentType") or content_type
        return StoredObject(body=body, content_type=resolved_content_type)
