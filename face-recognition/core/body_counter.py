import numpy as np
from typing import List, Tuple

class BodyCounter:
    def __init__(self, crossing_threshold: float = 0.7):
        self.crossing_threshold = crossing_threshold
        self.person_count = 0
        self.tracked_ids: set = set()
        self.last_detection_frame = None
    
    def count_from_detections(self, detections: List[dict]) -> int:
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
        return self.person_count
    
    def reset(self) -> None:
        self.person_count = 0
        self.tracked_ids = set()
        self.last_detection_frame = None
    
    def simple_count_from_frame(self, frame_persons: int, prev_frame_persons: int) -> int:
        if frame_persons > prev_frame_persons:
            new_persons = frame_persons - prev_frame_persons
            self.person_count += new_persons
            print(f"   [CROSSING] {new_persons} person(s) detected (total: {self.person_count})")
        return self.person_count
