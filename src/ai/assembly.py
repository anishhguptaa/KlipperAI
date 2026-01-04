import assemblyai as aai
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

# Configure API key
aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

def transcribe_video(file_path: str) -> aai.Transcript:
    """
    Transcribe a video file using AssemblyAI with language detection.
    Returns the full transcript object which includes word-level timestamps.
    """
    logger.info(f"Starting transcription for file: {file_path}")
    
    config = aai.TranscriptionConfig(
        language_detection=True
    )
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)
    
    if transcript.status == aai.TranscriptStatus.error:
        logger.error(f"Transcription failed: {transcript.error}")
        raise Exception(f"Transcription failed: {transcript.error}")
        
    logger.info(f"Transcription completed. Detected language: {transcript.json_response.get('language_code')}")
    return transcript
