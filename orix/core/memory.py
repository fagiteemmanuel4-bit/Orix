import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

class LocalMemoryStore:
    def __init__(self):
        self.memory_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "orix"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "memory.json"
        self.data = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text(encoding="utf-8"))
            except Exception:
                return self._default_memory()
        return self._default_memory()

    def _default_memory(self) -> Dict[str, Any]:
        return {
            "preferences": {},
            "resolved_exceptions": [],
            "project_insights": {},
            "history": [],
        }

    def save(self) -> None:
        self.memory_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def record_preference(self, key: str, value: Any) -> None:
        self.data["preferences"][key] = value
        self.save()

    def record_exception(self, exception: str, resolution: str) -> None:
        self.data["resolved_exceptions"].append({"error": exception, "resolution": resolution})
        self.save()

    def record_insight(self, project_name: str, insight: str) -> None:
        self.data["project_insights"].setdefault(project_name, []).append(insight)
        self.save()

    def append_history(self, entry: str) -> None:
        self.data["history"].append(entry)
        self.save()

    def query(self, key: str) -> Optional[Any]:
        return self.data.get(key)

    # Prompt caching utilities for smart caching / cost control
    def get_cached_prompt(self, key: str) -> Optional[str]:
        cache = self.data.setdefault("prompt_cache", {})
        return cache.get(key)

    def set_cached_prompt(self, key: str, response: str) -> None:
        cache = self.data.setdefault("prompt_cache", {})
        cache[key] = response
        self.save()

    def clear_prompt_cache(self) -> None:
        self.data["prompt_cache"] = {}
        self.save()
