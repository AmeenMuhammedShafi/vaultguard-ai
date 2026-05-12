import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.face_detector import FaceDetector
from auth.embedding_matcher import EmbeddingMatcher
from database.embeddings_store import EmbeddingStore


def enroll_employee(employee_id: str, capture_count: int = 3) -> bool:
    print(f"\n{'='*60}")
    print(f"ENROLLING EMPLOYEE: {employee_id}")
    print(f"{'='*60}")
    print(f"Instructions:")
    print(f"1. Face the camera clearly")
    print(f"2. Press SPACE to capture each face")
    print(f"3. You need {capture_count} good captures")
    print(f"4. Press ESC to cancel")
    print(f"{'='*60}\n")
    detector = FaceDetector()
    matcher = EmbeddingMatcher()
    store = EmbeddingStore()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera!")
        return False
    embeddings = []
    captured = 0
    
    while captured < capture_count:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to read frame")
            break
        
        faces = detector.detect_faces(frame)
        
        frame_display = frame.copy()
        for x1, y1, x2, y2, conf in faces:
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_display, f"Conf: {conf:.2f}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.putText(frame_display, f"Captured: {captured}/{capture_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame_display, "SPACE=Capture | ESC=Cancel", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.imshow(f"Enrollment - {employee_id}", frame_display)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            print("\nEnrollment cancelled by user")
            cap.release()
            cv2.destroyAllWindows()
            return False
        elif key == 32:
            if len(faces) == 0:
                print("❌ No face detected! Try again.")
                continue
            if len(faces) > 1:
                print("❌ Multiple faces detected! Only one person please.")
                continue
            
            x1, y1, x2, y2, _ = faces[0]
            face_roi = detector.extract_face_roi(frame, x1, y1, x2, y2)
            
            embedding = matcher.extract_embedding(face_roi)
            if embedding is None:
                print("❌ Embedding extraction failed. Try again.")
                continue
            embeddings.append(embedding)
            captured += 1
            print(f"✅ Capture {captured}/{capture_count} successful")
    cap.release()
    cv2.destroyAllWindows()
    
    if len(embeddings) < capture_count:
        print(f"\n❌ Enrollment failed: Only captured {len(embeddings)}/{capture_count}")
        return False
    
    final_embedding = np.mean(embeddings, axis=0)
    
    store.store_embedding(employee_id, final_embedding)
    
    print(f"\n✅ ENROLLMENT SUCCESSFUL!")
    print(f"   Employee ID: {employee_id}")
    print(f"   Embedding stored in: {store.db_path}")
    print(f"   Status: Ready for authorization")
    
    return True


def main():
    while True:
        print("\n" + "="*60)
        print("FACE RECOGNITION - EMPLOYEE ENROLLMENT SYSTEM")
        print("="*60)
        print("1. Enroll new employee")
        print("2. List enrolled employees")
        print("3. Delete employee")
        print("4. Exit")
        print("="*60)
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            emp_id = input("Enter employee ID (e.g., EMP001): ").strip()
            if emp_id:
                enroll_employee(emp_id)
            else:
                print("❌ Invalid employee ID")
        
        elif choice == "2":
            store = EmbeddingStore()
            employees = store.list_employees()
            if employees:
                print(f"\nEnrolled employees ({len(employees)}):")
                for emp in employees:
                    print(f"  • {emp}")
            else:
                print("No employees enrolled yet")
        
        elif choice == "3":
            store = EmbeddingStore()
            emp_id = input("Enter employee ID to delete: ").strip()
            if store.delete_embedding(emp_id):
                print(f"✅ Deleted: {emp_id}")
            else:
                print(f"❌ Not found: {emp_id}")
        
        elif choice == "4":
            print("Goodbye!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
