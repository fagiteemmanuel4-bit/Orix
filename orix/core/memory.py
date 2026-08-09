import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

class LocalMemoryStore:
    def __init__(self, workspace_root: Optional[str] = None):
        root = Path(workspace_root or os.getcwd()).resolve()
        orix_dir = root / ".orix"

        # Project-scoped memory location by default, with fallback to global user config
        if orix_dir.exists() or os.access(str(root), os.W_OK):
            orix_dir.mkdir(parents=True, exist_ok=True)
            self.memory_file = orix_dir / "memory.json"
        else:
            global_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "orix"
            global_dir.mkdir(parents=True, exist_ok=True)
            self.memory_file = global_dir / "memory.json"

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
            "prompt_cache": {}
        }

    def save(self) -> None:
        # Before saving, ensure no API keys or keys containing "api_key" or credentials are saved
        cleaned_data = self._clean_sensitive(self.data)
        self.memory_file.write_text(json.dumps(cleaned_data, indent=2), encoding="utf-8")

    def _clean_sensitive(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                if any(sec in k.lower() for sec in ["api_key", "password", "token", "secret", "credentials"]):
                    continue
                cleaned[k] = self._clean_sensitive(v)
            return cleaned
        elif isinstance(obj, list):
            return [self._clean_sensitive(x) for x in obj]
        return obj

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

    def get_all(self) -> Dict[str, Any]:
        return self.data

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

    def delete_key(self, main_key: str, sub_key: Optional[str] = None) -> bool:
        """Deletes a key or a nested sub-key from the memory store."""
        if main_key in self.data:
            if sub_key:
                if isinstance(self.data[main_key], dict) and sub_key in self.data[main_key]:
                    del self.data[main_key][sub_key]
                    self.save()
                    return True
                return False
            else:
                del self.data[main_key]
                self.save()
                return True
        return False
