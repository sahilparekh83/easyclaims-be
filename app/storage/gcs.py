from .base import StorageBackend


class GCSStorage(StorageBackend):
    def __init__(self, bucket: str, project: str = None, credentials_file: str = None):
        try:
            from google.cloud import storage as gcs
            from google.oauth2 import service_account
        except ImportError:
            raise RuntimeError(
                "google-cloud-storage is required for GCS backend. "
                "Install it: pip install google-cloud-storage"
            )
        if credentials_file:
            creds = service_account.Credentials.from_service_account_file(credentials_file)
            self._client = gcs.Client(project=project, credentials=creds)
        else:
            self._client = gcs.Client(project=project)
        self._bucket_name = bucket
        self._bucket = self._client.bucket(bucket)

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        blob = self._bucket.blob(key)
        blob.upload_from_string(data, content_type=content_type)
        return key

    def download(self, key: str) -> bytes:
        blob = self._bucket.blob(key)
        return blob.download_as_bytes()

    def delete(self, key: str) -> None:
        blob = self._bucket.blob(key)
        blob.delete()

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        from datetime import timedelta
        blob = self._bucket.blob(key)
        return blob.generate_signed_url(expiration=timedelta(seconds=expires_in), method="GET")
