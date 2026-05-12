import time
from typing import Tuple, List
from auth.face_detector import FaceDetector
from auth.embedding_matcher import EmbeddingMatcher
from database.embeddings_store import EmbeddingStore


class AuthenticationTerminal:    
    def __init__(self, similarity_threshold: float = 0.6):
        self.detector = FaceDetector()
        self.matcher = EmbeddingMatcher(similarity_threshold=similarity_threshold)
        self.store = EmbeddingStore()
        self.auth_queue: List[str] = []
        self.auth_timestamps: List[float] = []
        self.authorized_employees = self.store.get_all_embeddings()
        if not self.authorized_employees:
            print("⚠️  WARNING: No employees enrolled!")
        else:
            print(f"✅ Loaded {len(self.authorized_employees)} authorized employees")
    
    def authenticate_face(self, face_image) -> Tuple[bool, str, float]:
        embedding = self.matcher.extract_embedding(face_image)
        if embedding is None:
            return False, "UNKNOWN", 0.0
        person_id, score = self.matcher.match_embedding(
            embedding,
            self.authorized_employees
        )
        return person_id is not None, person_id or "UNAUTHORIZED", score
    
    def add_authenticated_person(self, person_id: str) -> bool:
        if len(self.auth_queue) >= 2:
            print("⚠️  Queue already full (2 persons)")
            return False
        if person_id in self.auth_queue:
            print(f"❌ DUPLICATE AUTH ATTEMPT: {person_id} already authenticated!")
            print(f"   Need different person. Queue: {self.auth_queue}")
            return False
        self.auth_queue.append(person_id)
        self.auth_timestamps.append(time.time())
        print(f"✅ {person_id} authenticated ({len(self.auth_queue)}/2)")
        return len(self.auth_queue) == 2
    
    def get_queue_status(self) -> dict:
        return {
            'count': len(self.auth_queue),
            'persons': self.auth_queue.copy(),
            'is_complete': len(self.auth_queue) == 2,
            'waiting_for': 2 - len(self.auth_queue)
        }
    
    def clear_queue(self) -> None:
        self.auth_queue = []
        self.auth_timestamps = []
    
    def get_authorized_persons(self) -> List[str]:
        return self.auth_queue.copy()
    
    def get_expected_entry_count(self) -> int:
        if len(self.auth_queue) == 2:
            return 2
        return 0
