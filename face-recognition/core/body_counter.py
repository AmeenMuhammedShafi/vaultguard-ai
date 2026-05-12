"""
Body counter module.

Counts persons crossing doorway during entry window using YOLO tracking.
"""

import numpy as np
from typing import List, Tuple


class BodyCounter:
    """
    Counts persons crossing doorway during entry window.
    
    Uses simple frame-to-frame person detection to count unique crossings.
    """
    
    def __init__(self, crossing_threshold: float = 0.7):
        """
        Initialize body counter.
        
        Args:
            crossing_threshold: Confidence threshold for person detection
        """
        self.crossing_threshold = crossing_threshold
        self.person_count = 0
        self.tracked_ids: set = set()
        self.last_detection_frame = None
    
    def count_from_detections(self, detections: List[dict]) -> int:
        """Count unique persons from YOLO detections."""
        for detection in detections:
            person_id = detection.get('id')
            confidence = detection.get('confidence', 0)
            if confidence >= self.crossing_threshold:
                if person_id not in self.tracked_ids:
                    self.tracked_ids.add(person_id)
                    self.person_count += 1
                    print(f"   [CROSSING] Person #{self.person_count} detected (ID: {person_id}, conf: {confidence:.2f})")
        return self.person_count
    
    def get_count(self) -> int:
        """Get current person count."""
        return self.person_count
    
    def reset(self) -> None:
        """Reset counter for next entry window."""
        self.person_count = 0
        self.tracked_ids = set()
        self.last_detection_frame = None
    
    def simple_count_from_frame(self, frame_persons: int, prev_frame_persons: int) -> int:
        """Simplified counting using frame-to-frame person count delta."""
        if frame_persons > prev_frame_persons:
            new_persons = frame_persons - prev_frame_persons
            self.person_count += new_persons
            print(f"   [CROSSING] {new_persons} person(s) detected (total: {self.person_count})")
        return self.person_count
