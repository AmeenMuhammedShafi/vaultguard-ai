import cv2
import numpy as np
from typing import Optional, Tuple, List
from datetime import datetime
from ultralytics import YOLO
from pathlib import Path
from core.authentication_terminal import AuthenticationTerminal
from auth.face_detector import FaceDetector

class DualPersonAccessControl:
    def __init__(self):
        print("\n" + "="*70)
        print("DUAL-PERSON ACCESS CONTROL SYSTEM - INITIALIZING")
        print("="*70)
        self.auth_terminal = AuthenticationTerminal()
        self.face_detector = FaceDetector()
        
        yolo_model_path = Path(__file__).parent.parent.parent / "strong-room-ai" / "yolov8m.pt"
        if not yolo_model_path.exists():
            yolo_model_path = "yolov8m.pt"
        print(f"Loading YOLO model from: {yolo_model_path}")
        self.yolo_model = YOLO(str(yolo_model_path))
        print("✅ YOLO model loaded for person detection")
        
        self.state = "WAITING_AUTH"
        self.alerts = []
        self._frame_count = 0
        print("✅ System ready")
        print("="*70)
        print("\nWORKFLOW:")
        print("1. Person A: Face authentication at terminal")
        print("2. Person B: Face authentication at terminal")
        print("3. Both auth'd? → Door unlocks")
        print("4. Corner camera monitors with continuous tracking")
        print("="*70 + "\n")

    def authenticate_face_from_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[str], float]:
        faces = self.face_detector.detect_faces(frame)
        if not faces:
            return False, None, 0.0
        if len(faces) > 1:
            print("❌ Multiple faces detected - only one person at a time")
            return False, None, 0.0
        x1, y1, x2, y2, det_conf = faces[0]
        face_roi = self.face_detector.extract_face_roi(frame, x1, y1, x2, y2)
        is_auth, person_id, face_conf = self.auth_terminal.authenticate_face(face_roi)
        return is_auth, person_id, face_conf

    def process_authentication_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        frame_display = frame.copy()
        h, w = frame.shape[:2]
        is_authorized, person_id, confidence = self.authenticate_face_from_frame(frame)
        faces = self.face_detector.detect_faces(frame)
        for x1, y1, x2, y2, det_conf in faces:
            if is_authorized:
                color = (0, 255, 0)
                label = f"{person_id} (Auth)"
            else:
                color = (0, 0, 255)
                label = "Unauthorized"
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame_display, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame_display, f"Conf: {confidence:.2f}", (x1, y2+25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        queue_status = self.auth_terminal.get_queue_status()
        status_text = f"Authentication Queue: {queue_status['count']}/2"
        cv2.putText(frame_display, status_text, (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if queue_status['persons']:
            persons_text = f"Authenticated: {', '.join(queue_status['persons'])}"
            cv2.putText(frame_display, persons_text, (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)
        waiting_text = f"Waiting for: {queue_status['waiting_for']} more"
        cv2.putText(frame_display, waiting_text, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 1)
        if queue_status['count'] < 2:
            cv2.putText(frame_display, "Press SPACE to authenticate", (10, h-20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame_display, queue_status['is_complete']

    def try_authenticate(self) -> bool:
        return False

    def reset_system(self) -> None:
        self.state = "WAITING_AUTH"
        self.auth_terminal.clear_queue()
        self.alerts = []
