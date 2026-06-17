from .base import StorageBackend


class AzureBlobStorage(StorageBackend):
    def __init__(self, container: str, connection_string: str):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise RuntimeError(
                "azure-storage-blob is required for Azure backend. "
                "Install it: pip install azure-storage-blob"
            )
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container = container

    def _blob(self, key: str):
        return self._client.get_blob_client(container=self._container, blob=key)

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        from azure.storage.blob import ContentSettings
        blob = self._blob(key)
        blob.upload_blob(data, overwrite=True,
                         content_settings=ContentSettings(content_type=content_type))
        return key

    def download(self, key: str) -> bytes:
        return self._blob(key).download_blob().readall()

    def delete(self, key: str) -> None:
        self._blob(key).delete_blob()

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        from datetime import datetime, timedelta, timezone
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        account = self._client.account_name
        account_key = self._client.credential.account_key
        sas = generate_blob_sas(
            account_name=account,
            container_name=self._container,
            blob_name=key,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        )
        return f"https://{account}.blob.core.windows.net/{self._container}/{key}?{sas}"
