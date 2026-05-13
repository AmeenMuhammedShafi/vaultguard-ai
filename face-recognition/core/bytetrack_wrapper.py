import numpy as np
from typing import List, Dict, Tuple, Optional
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment


class STrack:
    """Track object for ByteTrack"""
    shared_counter = 0
    
    def __init__(self, tlbr, conf, temp_feat=None):
        # tlbr: [x1, y1, x2, y2]
        self.tlbr = np.array(tlbr, dtype=np.float32)
        self.conf = conf
        self.temp_feat = temp_feat
        self.track_id = None
        
        self.time_since_update = 0
        self.state = "new"  # new, tracked, lost
        
        # Initialize Kalman filter
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.eye(7, 7)
        self.kf.F[0, 4] = 1.0
        self.kf.F[1, 5] = 1.0
        self.kf.F[2, 6] = 1.0
        
        self.kf.H = np.eye(4, 7)
        self.kf.R *= 10.0
        self.kf.P *= 1000.0
        self.kf.P[4:, 4:] *= 0.01
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        self.update_kf(self.tlbr)
    
    def update_kf(self, tlbr):
        """Update Kalman filter with detection"""
        self.kf.x[:4] = self.convert_tlbr_to_center(tlbr).reshape(4, 1)
        self.kf.predict()
    
    def predict(self):
        """Predict next state"""
        self.kf.predict()
        mean_state = self.kf.x[:4].flatten()
        self.tlbr = self.convert_center_to_tlbr(mean_state)
    
    @staticmethod
    def convert_tlbr_to_center(tlbr):
        """Convert tlbr to center format [cx, cy, w, h]"""
        cx = (tlbr[0] + tlbr[2]) / 2
        cy = (tlbr[1] + tlbr[3]) / 2
        w = tlbr[2] - tlbr[0]
        h = tlbr[3] - tlbr[1]
        return np.array([cx, cy, w, h])
    
    @staticmethod
    def convert_center_to_tlbr(center):
        """Convert center format [cx, cy, w, h] to tlbr"""
        cx, cy, w, h = center
        return np.array([cx - w/2, cy - h/2, cx + w/2, cy + h/2])
    
    def get_centroid(self):
        """Get centroid of the track"""
        return ((self.tlbr[0] + self.tlbr[2]) / 2, (self.tlbr[1] + self.tlbr[3]) / 2)


class ByteTrackTracker:
    """ByteTrack-based multi-object tracker"""
    
    def __init__(self, track_thresh=0.5, track_buffer=120, match_thresh=0.8):
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer  # frames to keep lost tracks
        self.match_thresh = match_thresh
        
        self.tracked_tracks: List[STrack] = []
        self.lost_tracks: List[STrack] = []
        self.removed_tracks: List[STrack] = []
        
        self.frame_id = 0
        self.next_track_id = 1
        
        self.track_history: Dict[int, Tuple[float, float]] = {}
        self.person_history: Dict[int, int] = {}
        
    def update(self, detections: List[Tuple[int, int, int, int, float]] = None) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Update tracker with detections
        detections: List of (x1, y1, x2, y2, conf) or (x1, y1, x2, y2) without conf
        """
        self.frame_id += 1
        
        if detections is None or len(detections) == 0:
            detections = []
        
        # Parse detections
        det_list = []
        for det in detections:
            if len(det) == 5:
                x1, y1, x2, y2, conf = det
            elif len(det) == 4:
                x1, y1, x2, y2 = det
                conf = 0.9
            else:
                continue
            det_list.append(STrack(tlbr=[x1, y1, x2, y2], conf=conf))
        
        # Predict locations
        for track in self.tracked_tracks:
            track.predict()
        
        # Associate detections to tracked tracks
        track_pool = self.tracked_tracks + self.lost_tracks
        self._match_detections(det_list, track_pool)
        
        # Create new tracks from unmatched detections
        for det in det_list:
            if det.track_id is None:
                new_id = self.next_track_id
                self.next_track_id += 1
                det.track_id = new_id
                det.state = "new"
                self.tracked_tracks.append(det)
        
        # Update track history for lost/removed tracks
        self.tracked_tracks = [t for t in self.tracked_tracks if t.state != "removed"]
        
        # Handle lost tracks
        lost_indices = []
        for i, track in enumerate(self.tracked_tracks):
            if track.time_since_update > 1:
                track.state = "lost"
                self.lost_tracks.append(track)
                lost_indices.append(i)
        
        for i in reversed(lost_indices):
            self.tracked_tracks.pop(i)
        
        # Remove tracks that have been lost for too long
        self.lost_tracks = [t for t in self.lost_tracks if t.time_since_update < self.track_buffer]
        
        # Build result
        result = {}
        for track in self.tracked_tracks:
            if track.state == "tracked":
                x1, y1, x2, y2 = track.tlbr
                result[track.track_id] = (int(x1), int(y1), int(x2), int(y2))
                centroid = track.get_centroid()
                self.track_history[track.track_id] = centroid
                self.person_history[track.track_id] = self.person_history.get(track.track_id, 0) + 1
        
        return result
    
    def _match_detections(self, detections, tracks):
        """Match detections to tracks using IoU-based Hungarian algorithm"""
        if len(tracks) == 0:
            for det in detections:
                det.track_id = None
            return
        
        if len(detections) == 0:
            for track in tracks:
                track.time_since_update += 1
            return
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(detections), len(tracks)))
        for i, det in enumerate(detections):
            for j, track in enumerate(tracks):
                iou_matrix[i, j] = self._iou(det.tlbr, track.tlbr)
        
        # Hungarian algorithm
        matched_indices = linear_sum_assignment(-iou_matrix)
        
        matched_det_indices = set()
        matched_track_indices = set()
        
        for det_idx, track_idx in zip(matched_indices[0], matched_indices[1]):
            if iou_matrix[det_idx, track_idx] > self.match_thresh:
                track = tracks[track_idx]
                det = detections[det_idx]
                
                track.update_kf(det.tlbr)
                track.tlbr = det.tlbr
                track.conf = det.conf
                track.time_since_update = 0
                if track.state == "new":
                    track.state = "tracked"
                
                det.track_id = track.track_id
                matched_det_indices.add(det_idx)
                matched_track_indices.add(track_idx)
        
        # Unmatched detections
        for i, det in enumerate(detections):
            if i not in matched_det_indices:
                det.track_id = None
        
        # Unmatched tracks
        for j, track in enumerate(tracks):
            if j not in matched_track_indices:
                track.time_since_update += 1
    
    @staticmethod
    def _iou(box1, box2):
        """Calculate IoU between two boxes [x1, y1, x2, y2]"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def reset(self):
        """Reset the tracker"""
        self.tracked_tracks = []
        self.lost_tracks = []
        self.removed_tracks = []
        self.frame_id = 0
        self.next_track_id = 1
        self.track_history.clear()
        self.person_history.clear()
