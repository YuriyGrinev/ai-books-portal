from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from uuid import UUID

from pydantic import HttpUrl


class StorageService(ABC):
    """Storage service interface for file operations"""
    
    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        content_type: str,
        entity_type: str,
        entity_id: UUID
    ) -> HttpUrl:
        """Upload file to storage and return public URL"""
        pass
    
    @abstractmethod
    async def delete_file(self, url: HttpUrl) -> bool:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    async def get_download_url(self, url: HttpUrl, expires_in: int = 3600) -> Optional[HttpUrl]:
        """Get temporary download URL for file"""
        pass 