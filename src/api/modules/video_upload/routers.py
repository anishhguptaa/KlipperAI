from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from src.api.modules.video_upload.services import video_upload_service
from src.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/video-upload",
    tags=["Video Upload"]
)


class SASTokenResponse(BaseModel):
    """Response model for SAS token generation"""
    blob_name: str = Field(..., description="Unique name of the blob in Azure Storage")
    sas_url: str = Field(..., description="SAS URL for uploading the video")
    container_name: str = Field(..., description="Azure Storage container name")
    expiry_time: str = Field(..., description="Expiry time of the SAS token (ISO format)")
    blob_url: str = Field(..., description="Final blob URL (without SAS token)")
    message: str = Field(..., description="Success message with upload instructions")


@router.get("/generate-upload-url", response_model=SASTokenResponse)
async def generate_upload_url(
    file_extension: str = Query(
        default="mp4",
        description="File extension for the video (e.g., mp4, mov, avi)",
        regex="^[a-zA-Z0-9]+$"
    ),
    expiry_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Number of hours the SAS token is valid (1-24 hours)"
    )
):
    """
    Generate a SAS URL for uploading a video directly to Azure Blob Storage
    
    This endpoint creates a unique blob name and generates a Shared Access Signature (SAS) URL
    that allows the frontend to upload videos directly to Azure Blob Storage without going
    through the backend server.
    
    **Usage:**
    1. Call this endpoint to get a SAS URL
    2. Use the returned `sas_url` to upload the video file using HTTP PUT request
    3. Set Content-Type header to the appropriate video MIME type
    4. Upload the video binary data in the request body
    
    **Example upload (using fetch):**
    ```javascript
    const response = await fetch(sas_url, {
        method: 'PUT',
        headers: {
            'x-ms-blob-type': 'BlockBlob',
            'Content-Type': 'video/mp4'
        },
        body: videoFile
    });
    ```
    
    Args:
        file_extension: File extension for the video (default: mp4)
        expiry_hours: Number of hours the SAS token is valid (1-24 hours, default: 1)
        
    Returns:
        SASTokenResponse: Contains the SAS URL and related information
        
    Raises:
        HTTPException: If SAS URL generation fails
    """
    try:
        logger.info(f"Generating SAS URL for file extension: {file_extension}, expiry: {expiry_hours}h")
        
        result = video_upload_service.generate_upload_sas_url(
            file_extension=file_extension,
            expiry_hours=expiry_hours
        )
        
        return SASTokenResponse(
            blob_name=result["blob_name"],
            sas_url=result["sas_url"],
            container_name=result["container_name"],
            expiry_time=result["expiry_time"],
            blob_url=result["blob_url"],
            message=(
                "Use the 'sas_url' to upload your video file directly to Azure Blob Storage. "
                "Make a PUT request with 'x-ms-blob-type: BlockBlob' header and the video file as body."
            )
        )
        
    except Exception as e:
        logger.error(f"Failed to generate SAS URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.get("/verify-upload/{blob_name}")
async def verify_upload(blob_name: str):
    """
    Verify if a video has been successfully uploaded to Azure Blob Storage
    
    Args:
        blob_name: Name of the blob to verify
        
    Returns:
        dict: Contains verification status
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        logger.info(f"Verifying blob existence: {blob_name}")
        
        exists = video_upload_service.verify_blob_exists(blob_name)
        
        if exists:
            return {
                "exists": True,
                "blob_name": blob_name,
                "message": "Video uploaded successfully"
            }
        else:
            return {
                "exists": False,
                "blob_name": blob_name,
                "message": "Video not found or upload incomplete"
            }
            
    except Exception as e:
        logger.error(f"Failed to verify blob: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify upload: {str(e)}"
        )
