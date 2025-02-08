from .base import StorageProvider
import boto3


class S3StorageProvider(StorageProvider):

    def __init__(
        self, bucket: str, access_key: str, secret_key: str, endpoint_url: str = None
    ) -> None:
        super().__init__()
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
        )

    def download_object(self, object_key: str, destination_path: str) -> str:
        # TODO: Add download file function
        try:
            self.client.download_file(self.bucket, object_key, destination_path)
        except Exception as e:
            raise e

    def upload_object(self, object_path: str, object_key: str) -> None:
        # TODO: Add upload file function
        try:
            self.client.upload_file(object_path, self.bucket, object_key)
        except Exception as e:
            raise e
