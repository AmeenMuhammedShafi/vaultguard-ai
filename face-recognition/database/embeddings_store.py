import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Optional


class EmbeddingStore:
    def __init__(self, db_path: str = None):
        # Use absolute path based on module location (not working directory)
        if db_path is None:
            db_path = str(Path(__file__).parent / "embeddings.pkl")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embeddings: Dict[str, np.ndarray] = self._load()
    
    def _load(self) -> Dict[str, np.ndarray]:
        if self.db_path.exists():
            with open(self.db_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save(self) -> None:
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.embeddings, f)
    
    def store_embedding(self, employee_id: str, embedding: np.ndarray) -> None:
        self.embeddings[employee_id] = embedding
        self._save()
    
    def get_embedding(self, employee_id: str) -> Optional[np.ndarray]:
        return self.embeddings.get(employee_id)
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        return self.embeddings.copy()
    
    def delete_embedding(self, employee_id: str) -> bool:
        if employee_id in self.embeddings:
            del self.embeddings[employee_id]
            self._save()
            return True
        return False
    
    def list_employees(self) -> list:
        return list(self.embeddings.keys())
