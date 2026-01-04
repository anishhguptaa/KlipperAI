import os
import yt_dlp
from typing import List, Tuple
from src.shared.core.logger import get_logger

logger = get_logger(__name__)


def download_youtube_video(url: str) -> str:
    """
    Download a video from a URL using yt-dlp
    """
    logger.info(f"Starting download for URL: {url}")

    # Ensure downloads directory exists
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)

    # Configure yt-dlp options
    # We prefer mp4 format for compatibility
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "format_sort": ["lang:en"],
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(url, download=True)
            # Get the path of the downloaded file
            file_path = ydl.prepare_filename(info)

            logger.info(f"Video downloaded successfully: {file_path}")
            return file_path

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise


def generate_transcript(video_path: str) -> str:
    """
    Generate a transcript from a video
    """
    # TODO
    return "Transcript generated successfully"


def get_video_timestamps(transcript: str) -> List[Tuple[str, str]]:
    """
    Get the timestamp of a video
    """
    # TODO
    return [("00:00", "00:00")]


def cut_clips_from_video(
    video_path: str, timestamps: List[Tuple[str, str]]
) -> List[str]:
    """
    Cut clips from a video
    """
    # TODO
    return ["clip1.mp4", "clip2.mp4"]


def add_subtitles_to_videos(videos: List[str], subtitles: List[str]) -> str:
    """
    Add subtitles to a video
    """
    # TODO
    return "Subtitles added successfully!"
