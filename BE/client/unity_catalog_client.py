"""Client for Databricks Unity Catalog Volume file operations."""

import io

from databricks.sdk import WorkspaceClient

from BE.settings import VOLUME_BASE_PATH, get_settings
from BE.utils.logger import get_logger

logger = get_logger(__name__)


class UnityCatalogClient:
    """Manages file storage in Databricks Unity Catalog Volumes."""

    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
        # Inside Databricks Apps, OAuth credentials are auto-injected.
        # Passing host+token would conflict with OAuth, so let the SDK
        # auto-configure from environment variables.
        self._workspace_client = WorkspaceClient()

    def _volume_base(self) -> str:
        """Return the resolved volume base path."""
        return VOLUME_BASE_PATH.format(
            catalog=self._settings.databricks_catalog,
            schema=self._settings.databricks_schema,
        )

    def upload_file(
        self,
        chat_id: str,
        document_id: str,
        ext: str,
        file_content: bytes,
    ) -> str:
        """Store *file_content* to the volume and return the storage path.

        Path: ``/Volumes/{catalog}/{schema}/docs/{chat_id}/{document_id}.{ext}``
        """
        storage_path = f"{self._volume_base()}/{chat_id}/{document_id}.{ext}"

        logger.info(
            "Uploading file to %s",
            storage_path,
            extra={"chat_id": chat_id, "document_id": document_id},
        )

        self._workspace_client.files.upload(
            file_path=storage_path,
            contents=io.BytesIO(file_content),
            overwrite=True,
        )

        return storage_path

    def read_file(self, storage_path: str) -> bytes:
        """Read and return file content from the volume *storage_path*."""
        response = self._workspace_client.files.download(file_path=storage_path)
        return response.contents.read()

    def delete_file(self, storage_path: str) -> None:
        """Delete the file at *storage_path* from the volume."""
        logger.info("Deleting file at %s", storage_path)
        self._workspace_client.files.delete(file_path=storage_path)

    def generate_presigned_url(
        self,
        chat_id: str,
        document_id: str,
    ) -> str:
        """Return the BE proxy URL for viewing a document inline."""
        return f"/api/v1/chats/{chat_id}/documents/{document_id}/content"

    def generate_download_url(
        self,
        chat_id: str,
        document_id: str,
    ) -> str:
        """Return the BE proxy URL for downloading a document."""
        return f"/api/v1/chats/{chat_id}/documents/{document_id}/content?download=true"
