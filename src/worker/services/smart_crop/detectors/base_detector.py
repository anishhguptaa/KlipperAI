from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import numpy as np

class BaseDetector(ABC):
    """
    Abstract base class for all visual detectors.
    """

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on a single frame.

        Args:
            frame: Numpy array representing the frame (RGB).

        Returns:
            List of detection dictionaries.
            Each dictionary must follow this format:
            {
                "type": str,          # "face", "text", "object", etc.
                "bbox": [x1, y1, x2, y2], # Pixel coordinates [left, top, right, bottom]
                "weight": float       # Importance weight of this detection
            }
        """
        pass
