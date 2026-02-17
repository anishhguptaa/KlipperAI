"""
Video Processor Handler
Handles video processing jobs from the queue
"""
import importlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Iterable, List

from moviepy.video.io.VideoFileClip import VideoFileClip
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.shared.core.database import SessionLocal
from src.shared.core.logger import get_logger
from src.shared.enums import ProcessingStatus
from src.shared.models import Clip, ProcessingJob, Video
from src.shared.models.enums import GenerateThumbnailProcess
from src.shared.services.clip_storage_service import clip_storage_service
from src.shared.services.progress_service import update_job_progress
from src.shared.services.thumbnail_queue_service import thumbnail_queue_service

logger = get_logger(__name__)


class VideoProcessor:
    """Handles video processing tasks"""
    
    def process_video(
        self,
        video_id: int,
        blob_name: str,
        blob_url: str,
        user_id: int = None
    ):
        """
        Process a video job
        
        Args:
            video_id: Database ID of the video
            blob_name: Azure blob name
            blob_url: Full blob URL
            user_id: Optional user ID
        """
        db: Session = SessionLocal()
        
        try:
            logger.info(f"Starting video processing for video_id={video_id}")

            # Idempotent processing lock: try to acquire exclusive RUNNING status
            job = self._acquire_processing_lock(db, video_id, user_id)
            if job is None:
                logger.warning(
                    f"Could not acquire processing lock for video_id={video_id}. "
                    "Another active job is running. Exiting gracefully."
                )
                return

            job_id = job.id
            update_job_progress(job_id, step="queued", progress=10.00)

            ai_service = importlib.import_module("src.ai.service")
            user_str = str(user_id) if user_id is not None else "unknown"
            video_str = str(video_id)

            def require_callable(name: str):
                func = getattr(ai_service, name, None)
                if not callable(func):
                    raise AttributeError(f"{name} is not available in src.ai.service")
                return func

            # 1. Ensure raw video is present locally
            require_callable("download_video_from_azure")(user_str, video_str, blob_url)

            # 2. Audio + transcript generation
            update_job_progress(job_id, step="transcription", progress=40.00)
            audio_path = require_callable("get_audio_from_video")(user_str, video_str)
            transcript_path = require_callable("generate_transcript")(user_str, video_str)

            if not audio_path or not transcript_path:
                raise RuntimeError("Failed to generate audio/transcript artifacts")

            # 3. LLM + clip discovery
            update_job_progress(job_id, step="llm", progress=55.00)
            clips_payload = require_callable("get_clips_from_transcript")(
                user_str, video_str
            )
            if not clips_payload:
                raise RuntimeError("No clips returned from transcript analysis")

            timestamps = require_callable("get_timestamps_from_clips")(user_str, video_str)
            if not timestamps:
                raise RuntimeError("No timestamps generated for clips")

            # 4. Clip cutting
            update_job_progress(job_id, step="cutting", progress=85.00)
            clips = require_callable("cut_clips_from_video")(
                user_str, video_str, timestamps
            )

            # 5. Optional subtitles
            subtitles_enabled = getattr(ai_service, "subtitles_enabled", lambda: True)
            if subtitles_enabled():
                add_subtitles = require_callable("add_subtitles_to_clips")
                add_subtitles(user_str, video_str)
                update_job_progress(job_id, step="subtitles", progress=90.00)

            # 6. Upload generated clips + persist metadata
            clip_records = self._upload_and_record_clips(
                clips=clips,
                user_id=user_str,
                video_id=video_str,
                job_id=job_id,
                db=db,
            )
            logger.info(f"Uploaded {len(clip_records)} clips for video_id={video_id}")

            # 7. Cleanup local workspace
            self._cleanup_downloads(user_str, video_str)

            update_job_progress(job_id, step="done", progress=100.00)
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Video processing completed for video_id={video_id}, job_id={job_id}")

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}", exc_info=True)
            try:
                if 'job' in locals() and job.id:
                    update_job_progress(job.id, step="error", error_message=str(e))
                    job.status = ProcessingStatus.FAILED
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                pass
            raise
            
        finally:
            db.close()

    def _acquire_processing_lock(
        self, db: Session, video_id: int, user_id: int
    ) -> ProcessingJob:
        """
        Atomically acquire a processing lock by inserting a RUNNING job.
        If insertion fails, check if the existing RUNNING job is stale (>30 min).
        If stale, mark it FAILED and retry insertion.
        If not stale, return None to signal the caller to exit gracefully.
        """
        STALE_THRESHOLD_MINUTES = 30

        for attempt in range(2):
            try:
                job = ProcessingJob(
                    video_id=video_id,
                    user_id=user_id,
                    status=ProcessingStatus.RUNNING,
                    current_step="queued",
                    progress_percentage=10.00,
                    created_at=datetime.utcnow(),
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                logger.info(
                    f"Acquired processing lock for video_id={video_id}, job_id={job.id}"
                )
                return job

            except IntegrityError:
                db.rollback()
                logger.warning(
                    f"Failed to acquire lock for video_id={video_id} on attempt {attempt + 1}. "
                    "Checking for stale jobs..."
                )

                existing_job = (
                    db.query(ProcessingJob)
                    .filter(
                        ProcessingJob.video_id == video_id,
                        ProcessingJob.status == ProcessingStatus.RUNNING,
                    )
                    .order_by(ProcessingJob.created_at.desc())
                    .first()
                )

                if existing_job:
                    age = datetime.utcnow() - existing_job.created_at
                    if age > timedelta(minutes=STALE_THRESHOLD_MINUTES):
                        logger.warning(
                            f"Found stale job {existing_job.id} for video_id={video_id} "
                            f"(age: {age}). Marking as FAILED."
                        )
                        existing_job.status = ProcessingStatus.FAILED
                        existing_job.error_message = (
                            f"Job marked as stale after {STALE_THRESHOLD_MINUTES} minutes"
                        )
                        existing_job.completed_at = datetime.utcnow()
                        db.commit()
                        continue
                    else:
                        logger.info(
                            f"Job {existing_job.id} for video_id={video_id} is still active "
                            f"(age: {age}). Cannot acquire lock."
                        )
                        return None
                else:
                    logger.error(
                        f"IntegrityError but no RUNNING job found for video_id={video_id}. "
                        "This should not happen."
                    )
                    return None

        logger.error(
            f"Failed to acquire processing lock for video_id={video_id} after retries."
        )
        return None

    @staticmethod
    def _upload_and_record_clips(
        clips: Iterable[str],
        user_id: str,
        video_id: str,
        job_id: int,
        db: Session,
    ) -> List[Clip]:
        uploaded_clips: List[Clip] = []

        for idx, clip_path in enumerate(clips, start=1):
            blob_url = clip_storage_service.upload_clip(
                local_path=clip_path,
                user_id=user_id,
                video_id=video_id,
                clip_index=idx,
            )

            clip_record = Clip(
                job_id=job_id,
                video_id=int(video_id) if video_id.isdigit() else None,
                clip_url=blob_url,
            )
            db.add(clip_record)
            uploaded_clips.append(clip_record)

            thumbnail_queue_service.send_thumbnail_generation_message(
                entity_id=clip_record.id,
                process_type=GenerateThumbnailProcess.CLIP_THUMBNAIL,
            )

        db.commit()
        return uploaded_clips

    @staticmethod
    def _cleanup_downloads(user_id: str, video_id: str) -> None:
        download_dir = Path("downloads") / user_id / video_id
        if download_dir.exists():
            shutil.rmtree(download_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary directory: {download_dir}")
