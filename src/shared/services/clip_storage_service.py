import os
from pathlib import Path
from typing import Optional

from azure.storage.blob import BlobServiceClient, ContentSettings

from src.shared.core.config import settings
from src.shared.core.logger import get_logger

logger = get_logger(__name__)


class ClipStorageService:
    """Handles uploading generated clips to Azure Blob Storage."""

    def __init__(self):
        self.account_name = settings.CLIPS_STORAGE_ACCOUNT_NAME or settings.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = settings.CLIPS_STORAGE_ACCOUNT_KEY or settings.AZURE_STORAGE_ACCOUNT_KEY
        self.container_name = settings.CLIPS_CONTAINER_NAME

        self._blob_service_client = BlobServiceClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            credential=self.account_key,
        )

    def upload_clip(
        self,
        local_path: str,
        user_id: str,
        video_id: str,
        clip_index: int,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a clip to Azure Blob Storage and return the public URL.
        """
        user_segment = user_id or "unknown"
        video_segment = video_id or "unknown"
        suffix = Path(local_path).suffix or ".mp4"
        blob_name = f"videos/{user_segment}/{video_segment}/clip{clip_index:03d}{suffix}"
        resolved_content_type = content_type or ("video/mp4" if suffix.lower() == ".mp4" else "application/octet-stream")

        blob_client = self._blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name,
        )

        with open(local_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=resolved_content_type),
            )

        blob_url = (
            f"https://{self.account_name}.blob.core.windows.net/"
            f"{self.container_name}/{blob_name}"
        )
        logger.info(f"Uploaded clip to {blob_url}")
        return blob_url


clip_storage_service = ClipStorageService()
