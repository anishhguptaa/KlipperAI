from typing import List, Dict, Any
import numpy as np
import easyocr
import os

from src.worker.services.smart_crop.detectors.base_detector import BaseDetector
from src.shared.core.logger import get_logger

logger = get_logger(__name__)

# Path to the directory where EasyOCR models are stored
MODELS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    "../../models/easyocr"
))

class TextDetector(BaseDetector):
    """
    Text detector using EasyOCR.
    """

    def __init__(self, languages: List[str] = None, confidence: float = 0.3, use_gpu: bool = True):
        if languages is None:
            languages = ['en']
        self.languages = languages
        self.confidence = confidence
        
        logger.info(f"Initializing TextDetector with models from: {MODELS_DIR}")
        
        # Ensure directory exists, though we expect models to be pre-downloaded
        if not os.path.exists(MODELS_DIR):
            logger.warning(f"EasyOCR model directory not found at {MODELS_DIR}. Attempting to create it.")
            os.makedirs(MODELS_DIR, exist_ok=True)

        try:
            self.reader = easyocr.Reader(
                self.languages, 
                gpu=use_gpu, 
                verbose=False,
                model_storage_directory=MODELS_DIR,
                download_enabled=False
            )
            logger.info(f"TextDetector initialized for languages: {self.languages}")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            # Fallback to default behavior if local loading fails, though it might fail due to network
            logger.info("Retrying EasyOCR initialization with default settings (may trigger download)...")
            self.reader = easyocr.Reader(self.languages, gpu=use_gpu, verbose=False)

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        try:
            # EasyOCR expects RGB (or BGR, but we can pass it directly)
            # readtext returns a list of (bbox, text, prob)
            results = self.reader.readtext(frame)
            
            detections = []
            for bbox_points, text, prob in results:
                if prob < self.confidence:
                    continue

                # bbox_points is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                # Extract min/max to form a bounding box [x1, y1, x2, y2]
                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                
                x1 = int(min(xs))
                y1 = int(min(ys))
                x2 = int(max(xs))
                y2 = int(max(ys))

                detections.append({
                    "type": "text",
                    "bbox": [x1, y1, x2, y2],
                    "weight": 4.0
                })
            
            return detections

        except Exception as e:
            logger.error(f"Error during text detection: {str(e)}")
            return []
