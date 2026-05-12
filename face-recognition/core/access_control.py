import cv2
import numpy as np
from typing import Optional, Tuple
from datetime import datetime
from core.authentication_terminal import AuthenticationTerminal
from core.entry_window import EntryWindowManager
from core.body_counter import BodyCounter
from core.person_tracker import PersonTracker
from auth.face_detector import FaceDetector

class DualPersonAccessControl:
    def __init__(self):
        print("\n" + "="*70)
        print("DUAL-PERSON ACCESS CONTROL SYSTEM - INITIALIZING")
        print("="*70)
        self.auth_terminal = AuthenticationTerminal()
        self.entry_window = EntryWindowManager(window_duration=120.0)
        self.body_counter = BodyCounter()
        self.face_detector = FaceDetector()
        self.person_tracker = PersonTracker()
        self.state = "WAITING_AUTH"
        self.alerts = []
        self._prev_person_count = 0
        self._crossed_persons: set = set()
        print("✅ System ready")
        print("="*70)
        print("\nWORKFLOW:")
        print("1. Person A: Face authentication at terminal")
        print("2. Person B: Face authentication at terminal")
        print("3. Both auth'd? → Door unlocks for 10 minutes")
        print("4. Camera counts persons crossing")
        print("5. Verify count vs expected")
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
        """Try to authenticate person at terminal (call when user presses SPACE)."""
        return False
    def unlock_door(self) -> bool:
        """Unlock door (called when both persons authenticated)."""
        expected_count = self.auth_terminal.get_expected_entry_count()
        if expected_count < 2:
            print("❌ Cannot unlock - not both persons authenticated")
            return False
        self.state = "DOOR_UNLOCKED"
        self.entry_window.open_entry_window(expected_count=expected_count)
        self.body_counter.reset()
        self.person_tracker.reset()
        self._crossed_persons = set()
        return True

    def process_entry_frame(self, frame: np.ndarray, yolo_detections: list = None) -> Tuple[np.ndarray, Optional[dict]]:
        """Process frame during entry window (count persons crossing)."""
        frame_display = frame.copy()
        h, w = frame.shape[:2]
        if not self.entry_window.is_window_open():
            entry_result = self.entry_window.close_entry_window()
            self._log_entry_result(entry_result)
            self.state = "WINDOW_CLOSED"
            self.auth_terminal.clear_queue()
            self.person_tracker.reset()
            return frame_display, entry_result

        detections_boxes = []
        if yolo_detections:
            detections_boxes = yolo_detections
        else:
            faces = self.face_detector.detect_faces(frame)
            confident_faces = [f for f in faces if f[4] >= 0.4]
            detections_boxes = [(x1, y1, x2, y2) for x1, y1, x2, y2, _ in confident_faces]

        tracked_persons = self.person_tracker.update(detections_boxes)

        new_crossings = 0
        for person_id in tracked_persons.keys():
            if person_id not in self._crossed_persons:
                self._crossed_persons.add(person_id)
                self.entry_window.record_person_crossing()
                new_crossings += 1

        if new_crossings > 1:
            print(f"🚨 MULTIPLE SIMULTANEOUS ENTRIES: {new_crossings} persons entered together!")
        elif new_crossings == 1:
            print(f"   ✓ 1 person crossed (Total: {self.entry_window.actual_count})")

        window_status = self.entry_window.get_window_status()
        color = (0, 255, 0) if window_status['active'] else (0, 0, 255)
        status_text = f"ENTRY WINDOW ACTIVE | {window_status['remaining']:.1f}s remaining"
        cv2.putText(frame_display, status_text, (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        currently_visible = len(tracked_persons)
        detection_method = 'YOLO' if yolo_detections else 'Face'
        detection_text = f"Detection: {detection_method} | Currently visible: {currently_visible} persons"
        vis_color = (0, 0, 255) if currently_visible > 1 else (0, 165, 255)
        cv2.putText(frame_display, detection_text, (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, vis_color, 1)

        expected_text = f"Expected total: {window_status['expected']} persons"
        actual_text = f"Total counted: {window_status['actual']} unique crossings"
        cv2.putText(frame_display, expected_text, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)
        cv2.putText(frame_display, actual_text, (10, 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)

        for person_id, (x1, y1, x2, y2) in tracked_persons.items():
            box_color = (0, 255, 0)
            label = f"P#{person_id}"
            if person_id in self._crossed_persons:
                label += " ✓"
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(frame_display, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame_display, timestamp, (w-300, h-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        return frame_display, None

    def _log_entry_result(self, result: dict) -> None:
        """Log entry verification result."""
        print(f"\nENTRY VERIFICATION RESULT:")
        print(f"  Expected: {result['expected']}")
        print(f"  Actual: {result['actual']}")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Tailgating: {result['tailgating']}")
        print(f"  Message: {result['message']}")
        if result['tailgating']:
            self.alerts.append({
                'type': 'TAILGATING',
                'unauthorized_count': result['actual'] - result['expected'],
                'timestamp': datetime.now()
            })

    def get_system_state(self) -> dict:
        """Get current system state."""
        return {
            'state': self.state,
            'auth_queue': self.auth_terminal.get_queue_status(),
            'entry_window': self.entry_window.get_window_status(),
            'body_count': self.body_counter.get_count(),
            'alerts': self.alerts
        }

    def reset_system(self) -> None:
        """Reset system to initial state."""
        self.state = "WAITING_AUTH"
        self.auth_terminal.clear_queue()
        self.body_counter.reset()
        self.alerts = []
