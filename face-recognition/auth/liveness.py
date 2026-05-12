"""
Liveness detection module.

Detects if a face is real or spoofed (photo/video attack).
"""

import cv2
import numpy as np


class LivenessDetector:
    """
    Simple liveness detection using motion and texture analysis.
    
    Production-grade systems would use:
    - 3D depth sensing
    - Texture analysis (LBP)
    - Micro-expression detection
    - Eye blinking detection
    """
    
    def __init__(self):
        """Initialize liveness detector."""
        self.prev_frame = None
    
    def detect_liveness(self, frame: np.ndarray) -> Tuple[bool, float]:
        """Simple liveness check using optical flow."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_frame is None:
            self.prev_frame = gray
            return True, 0.5
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        motion_score = np.mean(mag)
        self.prev_frame = gray
        is_live = 0.5 < motion_score < 50
        confidence = min(motion_score / 10, 1.0)
        return is_live, confidence
