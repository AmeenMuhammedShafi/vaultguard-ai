"""
Face detection module using OpenCV DNN.

Detects faces in frames for enrollment and runtime verification.
"""

import cv2
import numpy as np
from typing import List, Tuple
from pathlib import Path


class FaceDetector:
    def __init__(self,
                 prototxt_path: str = "deploy.prototxt",
                 model_path: str = "res10_300x300_ssd_iter_140000.caffemodel",
                 confidence_threshold: float = 0.6):
        prototxt_path = self._find_model_file(prototxt_path)
        model_path = self._find_model_file(model_path)
        self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        self.confidence_threshold = confidence_threshold
    
    def _find_model_file(self, filename: str) -> str:
        current = Path.cwd()
        while current != current.parent:
            candidate = current / filename
            if candidate.exists():
                return str(candidate)
            current = current.parent
        return filename
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        h, w = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * [w, h, w, h]
                (x1, y1, x2, y2) = box.astype("int")
                
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                faces.append((x1, y1, x2, y2, float(confidence)))
        
        return faces
    
    def extract_face_roi(self, frame: np.ndarray, 
                        x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        return frame[y1:y2, x1:x2]
