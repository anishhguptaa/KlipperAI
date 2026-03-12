from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from src.shared.core.logger import get_logger

logger = get_logger(__name__)

class CropOptimizer:
    """
    Calculates and smoothes crop positions based on detections.
    """

    def __init__(self, target_aspect_ratio: float = 9/16, smoothing_window: int = 5):
        self.target_aspect_ratio = target_aspect_ratio
        self.smoothing_window = smoothing_window

    def calculate_crop_x(self, detections: List[Dict[str, Any]], frame_width: int, frame_height: int) -> int:
        """
        Calculate the optimal x-coordinate for the left edge of the crop window.
        """
        target_width = int(frame_height * self.target_aspect_ratio)
        center_crop_x = (frame_width - target_width) // 2

        if not detections:
            return center_crop_x

        weighted_center_sum = 0.0
        total_weight = 0.0

        for d in detections:
            bbox = d["bbox"] # [x1, y1, x2, y2]
            weight = d["weight"]
            
            # Calculate center of the bounding box
            bbox_center_x = (bbox[0] + bbox[2]) / 2.0
            
            weighted_center_sum += bbox_center_x * weight
            total_weight += weight

        if total_weight == 0:
            return center_crop_x

        optimal_center_x = weighted_center_sum / total_weight
        
        # Convert center position to left edge position
        crop_x = int(optimal_center_x - target_width / 2)
        
        # Clamp within video bounds
        crop_x = max(0, min(frame_width - target_width, crop_x))
        
        return crop_x

    def smooth_positions(self, positions: List[Tuple[float, int]]) -> List[Tuple[float, int]]:
        """
        Apply moving average smoothing to crop positions.
        Args:
            positions: List of (timestamp, crop_x) tuples.
        """
        if len(positions) <= 1:
            return positions

        crop_values = [x for _, x in positions]
        smoothed_values: List[int] = []

        half = self.smoothing_window // 2
        for i in range(len(crop_values)):
            start = max(0, i - half)
            end = min(len(crop_values), i + half + 1)
            # Use simple average
            avg = int(sum(crop_values[start:end]) / (end - start))
            smoothed_values.append(avg)

        smoothed = [
            (positions[i][0], smoothed_values[i])
            for i in range(len(positions))
        ]
        
        return smoothed
