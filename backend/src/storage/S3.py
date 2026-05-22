from __future__ import annotations

import logging
import time
from pathlib import Path

import boto3

from .base import StorageProvider

log = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    def __init__(
        self, bucket: str, access_key: str, secret_key: str, endpoint_url: str = None
    ) -> None:
        super().__init__(bucket)
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
        )

    def head_object(self, object_key: str) -> dict:
        return self.client.head_object(Bucket=self.bucket, Key=object_key)

    def download_object(self, object_key: str, destination_path: Path) -> int:
        """Download object; return expected ContentLength; raise if local size differs."""
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        head = self.head_object(object_key)
        expected = int(head["ContentLength"])
        log.debug(
            "S3 download start bucket=%s key=%s destination=%s expected_bytes=%s "
            "content_type=%s etag=%s",
            self.bucket,
            object_key,
            destination_path,
            expected,
            head.get("ContentType"),
            head.get("ETag"),
        )

        t0 = time.perf_counter()
        self.client.download_file(self.bucket, object_key, str(destination_path))
        elapsed_ms = (time.perf_counter() - t0) * 1000

        actual = destination_path.stat().st_size
        log.info(
            "S3 download done key=%s local_bytes=%s expected_bytes=%s elapsed_ms=%.0f",
            object_key,
            actual,
            expected,
            elapsed_ms,
        )
        if actual != expected:
            msg = (
                f"S3 download size mismatch for {object_key}: "
                f"expected={expected} local={actual}"
            )
            log.error(msg)
            raise ValueError(msg)

        return expected

    def upload_object(self, object_path: Path, object_key: str) -> None:
        object_path = Path(object_path)
        local_bytes = object_path.stat().st_size
        log.debug(
            "S3 upload start bucket=%s key=%s local_bytes=%s path=%s",
            self.bucket,
            object_key,
            local_bytes,
            object_path,
        )
        t0 = time.perf_counter()
        self.client.upload_file(
            str(object_path),
            self.bucket,
            object_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        log.info(
            "S3 upload done key=%s local_bytes=%s elapsed_ms=%.0f",
            object_key,
            local_bytes,
            elapsed_ms,
        )
