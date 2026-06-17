from .base import StorageBackend
from .local import LocalStorage
from .gcs import GCSStorage
from .azure_blob import AzureBlobStorage

_instance: StorageBackend = None


def get_storage() -> StorageBackend:
    global _instance
    if _instance is not None:
        return _instance
    from ..configs.common import get_settings
    settings = get_settings()
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "gcs":
        _instance = GCSStorage(
            bucket=settings.STORAGE_BUCKET,
            project=settings.GCS_PROJECT,
            credentials_file=settings.GCS_CREDENTIALS_FILE,
        )
    elif backend == "azure":
        _instance = AzureBlobStorage(
            container=settings.AZURE_CONTAINER,
            connection_string=settings.AZURE_CONNECTION_STRING,
        )
    else:
        _instance = LocalStorage(base_dir=settings.UPLOAD_DIR)
    return _instance


__all__ = ["StorageBackend", "LocalStorage", "GCSStorage", "AzureBlobStorage", "get_storage"]
