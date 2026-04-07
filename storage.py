import os
from typing import Optional


class StorageBackend:
    def put_object(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    def get_object(self, key: str) -> bytes:
        raise NotImplementedError

    def object_exists(self, key: str) -> bool:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def put_object(self, key: str, data: bytes) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def get_object(self, key: str) -> bytes:
        path = self._path(key)
        with open(path, "rb") as f:
            return f.read()

    def object_exists(self, key: str) -> bool:
        path = self._path(key)
        return os.path.exists(path)


try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:
    boto3 = None


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str, region_name: Optional[str] = None):
        if boto3 is None:
            raise RuntimeError(
                "boto3 is required for S3StorageBackend but is not installed"
            )
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region_name)

    def put_object(self, key: str, data: bytes) -> None:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get_object(self, key: str) -> bytes:
        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    def object_exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


def get_backend():
    provider = os.environ.get("CLOUD_PROVIDER", "local").lower()
    if provider == "aws":
        bucket = os.environ.get("AWS_S3_BUCKET")
        if not bucket:
            raise RuntimeError(
                "AWS_S3_BUCKET environment variable must be set for AWS provider"
            )
        return S3StorageBackend(bucket=bucket)
    # default to local filesystem
    data_dir = os.environ.get("LOCAL_STORAGE_DIR", os.path.join(os.getcwd(), "data"))
    return LocalStorageBackend(base_dir=data_dir)
