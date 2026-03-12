from typing import List, Tuple, Dict, Any
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip

from src.worker.services.smart_crop.detectors.base_detector import BaseDetector
from src.worker.services.smart_crop.region_builder import RegionBuilder
from src.worker.services.smart_crop.layout_engine import LayoutEngine
from src.shared.core.logger import get_logger

logger = get_logger(__name__)

class SmartCropEngine:
    """
    Orchestrates the smart cropping process:
    1. Extracts frames at intervals.
    2. Runs multiple detectors (Face, Text, etc.).
    3. Builds important regions and determines layout (crop vs pad).
    4. Smoothes the camera movement.
    """

    def __init__(self, detectors: List[BaseDetector], frame_sample_interval: float = 0.5):
        self.detectors = detectors
        self.region_builder = RegionBuilder()
        self.layout_engine = LayoutEngine()
        self.frame_sample_interval = frame_sample_interval

    def process_video(self, clip: VideoFileClip) -> List[Tuple[float, Tuple[int, int, int, int]]]:
        """
        Analyze the video clip and return a list of smoothed crop boxes.

        Args:
            clip: MoviePy VideoFileClip instance.

        Returns:
            List of (timestamp, (x1, y1, x2, y2)) tuples.
        """
        w, h = clip.size
        logger.info(f"Starting smart crop analysis for video ({w}x{h})...")

        # 1. Extract frames
        frames = self._extract_frames(clip)
        logger.info(f"Extracted {len(frames)} frames for analysis.")

        raw_boxes = []

        # 2. Run detection & Layout
        for i, (timestamp, frame) in enumerate(frames):
            frame_detections = []
            
            for detector in self.detectors:
                try:
                    dets = detector.detect(frame)
                    frame_detections.extend(dets)
                except Exception as e:
                    logger.error(f"Detector {type(detector).__name__} failed on frame {i}: {e}")

            # 3. Build Region & Calculate Layout
            union_bbox = self.region_builder.build_union_region(frame_detections)
            
            if union_bbox:
                crop_box = self.layout_engine.calculate_crop_window(union_bbox, w, h)
            else:
                crop_box = self.layout_engine.get_fallback_crop(w, h)
                
            raw_boxes.append((timestamp, crop_box))

        # 4. Smooth boxes
        smoothed_boxes = self._smooth_boxes(raw_boxes)
        logger.info("Smart crop analysis complete.")
        
        return smoothed_boxes

    def _extract_frames(self, clip: VideoFileClip) -> List[Tuple[float, np.ndarray]]:
        """
        Sample frames from the clip at fixed intervals.
        """
        frames: List[Tuple[float, np.ndarray]] = []
        duration = clip.duration
        t = 0.0
        while t < duration:
            try:
                frame = clip.get_frame(t)
                frames.append((t, frame))
            except Exception as e:
                logger.warning(f"Failed to extract frame at {t:.2f}s: {e}")
            t += self.frame_sample_interval
        return frames

    def _smooth_boxes(self, boxes: List[Tuple[float, Tuple[int, int, int, int]]], window_size: int = 5) -> List[Tuple[float, Tuple[int, int, int, int]]]:
        """
        Apply moving average smoothing to crop boxes.
        """
        if len(boxes) <= 1:
            return boxes

        # Unzip
        timestamps = [b[0] for b in boxes]
        coords = np.array([b[1] for b in boxes]) # Shape (N, 4)

        smoothed_coords = []
        half = window_size // 2

        for i in range(len(coords)):
            start = max(0, i - half)
            end = min(len(coords), i + half + 1)
            
            # Average each component (x1, y1, x2, y2)
            avg = np.mean(coords[start:end], axis=0).astype(int)
            smoothed_coords.append(tuple(avg))

        return list(zip(timestamps, smoothed_coords))
