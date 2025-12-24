"""Azure Blob Storage service for audio file management."""
import os
import uuid
from datetime import datetime
from typing import Optional

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential
from api.config import get_settings

settings = get_settings()


class BlobStorageService:
    """Service for managing audio files in Azure Blob Storage."""
    
    def __init__(self):
        """Initialize the blob storage client."""
        if not settings.AZURE_STORAGE_ACCOUNT_NAME:
            raise ValueError("Azure Storage is not configured. Check AZURE_STORAGE_ACCOUNT_NAME.")
        
        # Try key-based auth first, fall back to DefaultAzureCredential
        account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
        
        if settings.AZURE_STORAGE_ACCOUNT_KEY:
            # Use connection string with account key
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={settings.AZURE_STORAGE_ACCOUNT_NAME};"
                f"AccountKey={settings.AZURE_STORAGE_ACCOUNT_KEY};"
                f"EndpointSuffix=core.windows.net"
            )
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                # Test connection
                container_client = self.blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)
                container_client.exists()
            except Exception:
                # Fall back to DefaultAzureCredential if key auth fails
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        else:
            # Use DefaultAzureCredential (managed identity or Azure CLI)
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self._ensure_container_exists()
    
    def _ensure_container_exists(self) -> None:
        """Ensure the blob container exists, create if not."""
        container_client = self.blob_service_client.get_container_client(self.container_name)
        if not container_client.exists():
            container_client.create_container()
    
    def upload_audio(self, audio_data: bytes, username: str, original_filename: str) -> str:
        """
        Upload an audio file to Azure Blob Storage.
        
        Args:
            audio_data: The audio file bytes
            username: The username of the uploader
            original_filename: Original filename for extension detection
            
        Returns:
            The blob URL of the uploaded file
        """
        # Generate filename with username and timestamp
        file_ext = os.path.splitext(original_filename)[1] or ".wav"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        blob_name = f"{username}/{timestamp}_{unique_id}{file_ext}"
        
        # Determine content type
        content_type = self._get_content_type(file_ext)
        
        # Upload to blob storage
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        blob_client.upload_blob(
            audio_data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        return blob_client.url
    
    def download_audio(self, blob_url: str) -> bytes:
        """
        Download an audio file from Azure Blob Storage.
        
        Args:
            blob_url: The full URL of the blob
            
        Returns:
            The audio file bytes
        """
        # Extract blob name from URL
        blob_name = self._extract_blob_name(blob_url)
        
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        download_stream = blob_client.download_blob()
        return download_stream.readall()
    
    def delete_audio(self, blob_url: str) -> bool:
        """
        Delete an audio file from Azure Blob Storage.
        
        Args:
            blob_url: The full URL of the blob
            
        Returns:
            True if deletion was successful
        """
        try:
            blob_name = self._extract_blob_name(blob_url)
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            return True
        except Exception:
            return False
    
    def _extract_blob_name(self, blob_url: str) -> str:
        """Extract blob name from a full blob URL."""
        # URL format: https://<account>.blob.core.windows.net/<container>/<blob_name>
        parts = blob_url.split(f"/{self.container_name}/")
        if len(parts) > 1:
            return parts[1]
        raise ValueError(f"Invalid blob URL: {blob_url}")
    
    def _get_content_type(self, file_ext: str) -> str:
        """Get MIME type for file extension."""
        content_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac"
        }
        return content_types.get(file_ext.lower(), "application/octet-stream")


# Singleton instance
_storage_service: Optional[BlobStorageService] = None


def get_storage_service() -> BlobStorageService:
    """Get or create the blob storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = BlobStorageService()
    return _storage_service
