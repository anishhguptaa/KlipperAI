import json
from azure.storage.queue import QueueClient
from src.shared.core.config import settings
from src.shared.core.logger import get_logger

logger = get_logger(__name__)


class QueueService:
    """Service for interacting with Azure Queue Storage"""
    
    def __init__(self):
        """Initialize Queue Service with connection string"""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.queue_name = settings.AZURE_QUEUE_NAME
        
    def send_message(self, message_data: dict) -> bool:
        """
        Send a message to Azure Queue Storage
        
        Args:
            message_data: Dictionary containing the message data
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Create queue client
            queue_client = QueueClient.from_connection_string(
                self.connection_string,
                self.queue_name
            )
            
            # Convert message data to JSON string
            message_content = json.dumps(message_data)
            
            # Send message to queue
            queue_client.send_message(message_content)
            
            logger.info(f"Message sent to queue '{self.queue_name}': {message_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to queue: {str(e)}")
            return False
    
    def send_video_processing_message(
        self,
        video_id: int,
        blob_name: str,
        blob_url: str,
        user_id: int = None
    ) -> bool:
        """
        Send a video processing message to the queue
        
        Args:
            video_id: ID of the video record in database
            blob_name: Name of the blob in Azure Storage
            blob_url: Full URL of the blob
            user_id: Optional user ID who uploaded the video
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        message_data = {
            "video_id": video_id,
            "blob_name": blob_name,
            "blob_url": blob_url,
            "user_id": user_id,
            "action": "process_video"
        }
        
        return self.send_message(message_data)


# Create a singleton instance
queue_service = QueueService()
