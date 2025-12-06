# Video Upload API Documentation

## Overview
This API provides endpoints for generating Azure Blob Storage SAS (Shared Access Signature) URLs that allow frontend applications to upload videos directly to Azure Storage without routing through the backend server.

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Generate Upload URL

**Endpoint:** `GET /api/video-upload/generate-upload-url`

**Description:** Generates a unique SAS URL for uploading a video file directly to Azure Blob Storage.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_extension` | string | No | `mp4` | File extension for the video (e.g., mp4, mov, avi) |
| `expiry_hours` | integer | No | `1` | Number of hours the SAS token is valid (1-24) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/video-upload/generate-upload-url?file_extension=mp4&expiry_hours=2"
```

**Example Response:**
```json
{
  "blob_name": "videos/20251206_211453_538ec946.mp4",
  "sas_url": "https://learningqueues.blob.core.windows.net/raw-videos/videos/20251206_211453_538ec946.mp4?se=2025-12-06T23%3A14%3A53Z&sp=cw&sv=2023-11-03&sr=b&sig=...",
  "container_name": "raw-videos",
  "expiry_time": "2025-12-06T23:14:53.129738",
  "blob_url": "https://learningqueues.blob.core.windows.net/raw-videos/videos/20251206_211453_538ec946.mp4",
  "message": "Use the 'sas_url' to upload your video file directly to Azure Blob Storage. Make a PUT request with 'x-ms-blob-type: BlockBlob' header and the video file as body."
}
```

**Response Fields:**
- `blob_name`: Unique name assigned to the blob in Azure Storage
- `sas_url`: Complete URL with SAS token for uploading the video
- `container_name`: Azure Storage container name
- `expiry_time`: ISO format timestamp when the SAS token expires
- `blob_url`: Permanent URL of the blob (without SAS token)
- `message`: Instructions for using the SAS URL

---

### 2. Verify Upload

**Endpoint:** `GET /api/video-upload/verify-upload/{blob_name}`

**Description:** Verifies if a video has been successfully uploaded to Azure Blob Storage.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `blob_name` | string | Yes | Name of the blob to verify |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/video-upload/verify-upload/videos/20251206_211453_538ec946.mp4"
```

**Example Response (Success):**
```json
{
  "exists": true,
  "blob_name": "videos/20251206_211453_538ec946.mp4",
  "message": "Video uploaded successfully"
}
```

**Example Response (Not Found):**
```json
{
  "exists": false,
  "blob_name": "videos/20251206_211453_538ec946.mp4",
  "message": "Video not found or upload incomplete"
}
```

---

## Frontend Integration Guide

### Step 1: Get SAS URL
```javascript
const response = await fetch('http://localhost:8000/api/video-upload/generate-upload-url?file_extension=mp4&expiry_hours=1');
const data = await response.json();
const { sas_url, blob_name, blob_url } = data;
```

### Step 2: Upload Video to Azure
```javascript
// Upload the video file using the SAS URL
const uploadResponse = await fetch(sas_url, {
  method: 'PUT',
  headers: {
    'x-ms-blob-type': 'BlockBlob',
    'Content-Type': 'video/mp4'
  },
  body: videoFile // File object from input
});

if (uploadResponse.ok) {
  console.log('Upload successful!');
  console.log('Video URL:', blob_url);
}
```

### Step 3: Verify Upload (Optional)
```javascript
const verifyResponse = await fetch(`http://localhost:8000/api/video-upload/verify-upload/${blob_name}`);
const verifyData = await verifyResponse.json();

if (verifyData.exists) {
  console.log('Video verified successfully!');
}
```

### Complete React Example
```jsx
import React, { useState } from 'react';

function VideoUploader() {
  const [uploading, setUploading] = useState(false);
  const [videoUrl, setVideoUrl] = useState('');

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);

    try {
      // Step 1: Get SAS URL
      const response = await fetch(
        'http://localhost:8000/api/video-upload/generate-upload-url?file_extension=mp4'
      );
      const { sas_url, blob_url } = await response.json();

      // Step 2: Upload to Azure
      const uploadResponse = await fetch(sas_url, {
        method: 'PUT',
        headers: {
          'x-ms-blob-type': 'BlockBlob',
          'Content-Type': file.type
        },
        body: file
      });

      if (uploadResponse.ok) {
        setVideoUrl(blob_url);
        alert('Upload successful!');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        accept="video/*" 
        onChange={handleUpload}
        disabled={uploading}
      />
      {uploading && <p>Uploading...</p>}
      {videoUrl && <p>Video URL: {videoUrl}</p>}
    </div>
  );
}

export default VideoUploader;
```

---

## Error Handling

### Common Error Responses

**500 Internal Server Error:**
```json
{
  "detail": "Failed to generate upload URL: <error_message>"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["query", "expiry_hours"],
      "msg": "ensure this value is less than or equal to 24",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## API Documentation (Swagger)

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Environment Variables

Required environment variables in `.env`:
```env
# Azure Storage Configuration
AZURE_STORAGE_ACCOUNT_NAME=learningqueues
AZURE_STORAGE_ACCOUNT_KEY=<your-account-key>
AZURE_STORAGE_CONTAINER_NAME=raw-videos
```

---

## Security Notes

1. **SAS Token Expiry:** Tokens expire after the specified time (1-24 hours)
2. **Write-Only Access:** Generated SAS tokens only allow write/create operations
3. **Unique Blob Names:** Each upload gets a unique blob name with timestamp and UUID
4. **CORS:** Ensure Azure Storage CORS is configured to allow requests from your frontend domain

---

## Testing with cURL

### Generate SAS URL:
```bash
curl -X GET "http://localhost:8000/api/video-upload/generate-upload-url?file_extension=mp4&expiry_hours=2"
```

### Upload a video:
```bash
# First, get the SAS URL
SAS_URL=$(curl -s "http://localhost:8000/api/video-upload/generate-upload-url" | jq -r '.sas_url')

# Then upload the video
curl -X PUT "$SAS_URL" \
  -H "x-ms-blob-type: BlockBlob" \
  -H "Content-Type: video/mp4" \
  --data-binary "@/path/to/your/video.mp4"
```

### Verify upload:
```bash
curl -X GET "http://localhost:8000/api/video-upload/verify-upload/videos/20251206_211453_538ec946.mp4"
```
