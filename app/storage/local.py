import os
from .base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir

    def _abs(self, key: str) -> str:
        path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        with open(self._abs(key), "wb") as f:
            f.write(data)
        return key

    def download(self, key: str) -> bytes:
        with open(self._abs(key), "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        path = os.path.join(self.base_dir, key)
        if os.path.exists(path):
            os.remove(path)

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        return os.path.join(self.base_dir, key)
