from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, file: BinaryIO, filename: str) -> str:
        """Uploads a file and returns the storage path/key."""
        pass

    @abstractmethod
    async def get_url(self, file_path: str) -> str:
        """Returns the URL or local path for accessibility."""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """Deletes a file from storage."""
        pass
