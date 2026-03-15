from pathlib import Path
from typing import BinaryIO

import aiofiles

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: BinaryIO, filename: str) -> str:
        file_path = self.base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Reset file pointer to beginning
        file.seek(0)
        
        # Increased chunk size to 8MB (8 * 1024 * 1024) for optimized OS page cache / SSD IO
        chunk_size = 8 * 1024 * 1024

        import asyncio
        loop = asyncio.get_event_loop()

        async with aiofiles.open(file_path, "wb") as out_file:
            while True:
                # Read chunk in a thread pool to avoid blocking Event Loop
                content = await loop.run_in_executor(None, file.read, chunk_size)
                if not content:
                    break
                await out_file.write(content)

        return str(file_path)

    async def get_url(self, file_path: str) -> str:
        return file_path

    async def delete(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()
