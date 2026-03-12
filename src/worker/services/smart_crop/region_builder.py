from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class RegionBuilder:
    """
    Responsible for computing the important region from a list of detections.
    """

    def build_union_region(self, detections: List[Dict[str, Any]]) -> Optional[Tuple[int, int, int, int]]:
        """
        Computes the union bounding box of all detections.

        Args:
            detections: List of dicts with 'bbox' key [x1, y1, x2, y2].

        Returns:
            Tuple (x1, y1, x2, y2) representing the union region, or None if no detections.
        """
        if not detections:
            return None

        # Initialize with the first detection
        min_x, min_y, max_x, max_y = detections[0]['bbox']

        for det in detections[1:]:
            bbox = det['bbox']
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

        return int(min_x), int(min_y), int(max_x), int(max_y)
