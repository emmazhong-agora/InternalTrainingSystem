from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=BotoConfig(signature_version="s3v4"),
        )
        self.bucket = settings.s3_bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        buckets = self.client.list_buckets()
        if any(bucket["Name"] == self.bucket for bucket in buckets.get("Buckets", [])):
            return
        self.client.create_bucket(Bucket=self.bucket)

    def upload_file(self, key: str, file_obj: BinaryIO, content_type: str) -> None:
        self.client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )

    def delete_prefix(self, prefix: str) -> None:
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]
        if objects:
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})

    def generate_presigned_url(self, key: str, expires: timedelta = timedelta(hours=2)) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=int(expires.total_seconds()),
        )

    def get_object_stream(self, key: str, range_header: str | None = None):
        extra_args: dict = {}
        if range_header:
            extra_args["Range"] = range_header
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key, **extra_args)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(key) from exc
            raise

        body = obj["Body"]
        content_type = obj.get("ContentType", "application/octet-stream")
        content_length = obj.get("ContentLength")
        content_range = obj.get("ContentRange")
        status_code = 206 if range_header else 200
        return body, content_type, content_length, content_range, status_code

    @staticmethod
    def build_object_key(user_id: int, path: str) -> str:
        return str(Path(str(user_id)) / path.lstrip("/"))
