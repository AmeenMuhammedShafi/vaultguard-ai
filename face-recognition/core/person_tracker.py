"""
Simple person tracker using centroid matching.

Tracks persons across frames to prevent duplicate counts.
"""

from typing import List, Dict, Tuple
import math


class PersonTracker:
    """
    Track persons across frames using centroid matching.
    
    Assigns persistent IDs to persons based on proximity between frames.
    """
    
    def __init__(self, max_distance: float = 200.0):
        """
        Initialize person tracker.
        
        Args:
            max_distance: Max pixels a person can move between frames
        """
        self.max_distance = max_distance
        self.next_id = 1
        self.tracked_persons: Dict[int, Tuple[float, float]] = {}  # {id: (x, y)}
        self.person_history: Dict[int, int] = {}  # {id: frame_count}
        self.max_frames_missing = 120  # Allow person to be missing up to 4 seconds (120 frames @ 30fps)
    
    def update(self, detections: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int, int, int]]:
        """Update tracker with new detections."""
        result = {}
        matched_detections = set()
        matched_tracked = set()
        for det_idx, (x1, y1, x2, y2) in enumerate(detections):
            det_centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            min_distance = self.max_distance
            closest_id = None
            for track_id, (tx, ty) in self.tracked_persons.items():
                if track_id in matched_tracked:
                    continue
                distance = math.sqrt((det_centroid[0] - tx)**2 + (det_centroid[1] - ty)**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_id = track_id
            if closest_id is not None:
                result[closest_id] = (x1, y1, x2, y2)
                self.tracked_persons[closest_id] = det_centroid
                self.person_history[closest_id] = 1
                matched_tracked.add(closest_id)
                matched_detections.add(det_idx)
        unmatched_count = 0
        for det_idx, (x1, y1, x2, y2) in enumerate(detections):
            if det_idx not in matched_detections:
                new_id = self.next_id
                self.next_id += 1
                centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                result[new_id] = (x1, y1, x2, y2)
                self.tracked_persons[new_id] = centroid
                self.person_history[new_id] = 1
                unmatched_count += 1
        if unmatched_count > 0:
            print(f"   [TRACKER] {unmatched_count} new person(s) detected simultaneously")
        for track_id in list(self.tracked_persons.keys()):
            if track_id not in result:
                self.person_history[track_id] -= 1
        lost_ids = [pid for pid, count in self.person_history.items() if count <= -self.max_frames_missing]
        for pid in lost_ids:
            del self.tracked_persons[pid]
            del self.person_history[pid]
        return result
    
    def get_active_ids(self) -> List[int]:
        """Get list of currently tracked person IDs."""
        return list(self.tracked_persons.keys())
    
    def reset(self) -> None:
        """Reset tracker for new window."""
        self.tracked_persons = {}
        self.person_history = {}
        self.next_id = 1
