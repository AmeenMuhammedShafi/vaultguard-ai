"""
Embedding matcher for face recognition.

Compares live face embeddings against stored employee embeddings
using vector similarity metrics.
"""

import numpy as np
from typing import Dict, Tuple, Optional
from deepface import DeepFace


class EmbeddingMatcher:
    """Matches face embeddings using DeepFace and similarity metrics."""
    def __init__(self, model_name: str = "Facenet512",
                 similarity_threshold: float = 0.6,
                 metric: str = "cosine"):
        """Initialize embedding matcher."""
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.metric = metric
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face embedding from an image."""
        try:
            embedding = DeepFace.represent(
                face_image,
                model_name=self.model_name,
                enforce_detection=False
            )
            return np.array(embedding[0]['embedding'])
        except Exception as e:
            print(f"Embedding extraction failed: {e}")
            return None
    
    def compute_similarity(self, embedding1: np.ndarray,
                          embedding2: np.ndarray) -> float:
        """Compute similarity between two embeddings."""
        if self.metric == "cosine":
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            if norm1 > 0 and norm2 > 0:
                return np.dot(embedding1, embedding2) / (norm1 * norm2)
            return 0.0
        elif self.metric == "euclidean":
            distance = np.linalg.norm(embedding1 - embedding2)
            return 1.0 / (1.0 + distance)
        return 0.0
    
    def match_embedding(self, live_embedding: np.ndarray,
                       stored_embeddings: Dict[str, np.ndarray]) -> Tuple[Optional[str], float]:
        """Find best matching employee for live embedding."""
        best_match = None
        best_score = 0.0
        for emp_id, stored_emb in stored_embeddings.items():
            score = self.compute_similarity(live_embedding, stored_emb)
            if score > best_score:
                best_score = score
                if score >= self.similarity_threshold:
                    best_match = emp_id
        if best_score >= self.similarity_threshold:
            return best_match, best_score
        return None, best_score
