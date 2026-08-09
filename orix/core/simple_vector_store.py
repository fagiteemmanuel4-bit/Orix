from typing import Optional, Dict, Any


class SimpleVectorStore:
    """
    Minimal in-memory vector store used for tests and simple indexing.
    Stores chunks under self.index["chunks"] as dicts containing:
      { "id": ..., "text": ..., "metadata": {...} }
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        self.index: Dict[str, Any] = {"chunks": []}

    def clear(self) -> None:
        self.index = {"chunks": []}

    def add_chunk(self, path: str, chunk_id: str, text: str, metadata: Dict[str, Any]) -> None:
        # keep minimal structure indexer expects
        self.index["chunks"].append({
            "id": chunk_id,
            "text": text,
            "metadata": metadata,
        })
