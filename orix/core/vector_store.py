import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

class SimpleVectorStore:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or (Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "orix"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "vector_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                return {"chunks": []}
        return {"chunks": []}

    def save(self) -> None:
        self.index_file.write_text(json.dumps(self.index, indent=2), encoding="utf-8")

    def add_chunk(self, path: str, chunk_id: str, text: str, metadata: Dict[str, Any]) -> None:
        self.index.setdefault("chunks", []).append({
            "path": path,
            "chunk_id": chunk_id,
            "text": text,
            "metadata": metadata,
        })
        self.save()

    def query(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        lower = query_text.lower()
        results = [chunk for chunk in self.index.get("chunks", []) if lower in chunk["text"].lower() or lower in json.dumps(chunk["metadata"]).lower()]
        return results[:limit]

    def clear(self) -> None:
        self.index = {"chunks": []}
        self.save()
