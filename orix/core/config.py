import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pathlib import Path
from typing import Any, Dict
import stat
import tomli_w

DEFAULT_CONFIG: Dict[str, Any] = {
    "context_window": 128000,
    "vision_model": "claude-3-5-sonnet",
    "sandbox": "host",
    "allowlist": ["https://api.openai.com", "https://openrouter.ai"],
    "auto_refresh_seconds": 3,
}

class ConfigManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.user_config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "orix"
        self.project_config = self.project_root / "config.toml"
        self.user_config = self.user_config_dir / "config.toml"
        self.source = self.project_config if self.project_config.exists() else self.user_config
        self._mtime = None
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        if self.source and self.source.exists():
            try:
                with open(self.source, "rb") as f:
                    data = tomllib.load(f)
                self._mtime = self.source.stat().st_mtime
                merged = {**DEFAULT_CONFIG, **data}
                return merged
            except Exception as e:
                # If there's a syntax error or decoding error, raise descriptive error
                raise ValueError(
                    f"Configuration file at '{self.source}' is corrupted or has invalid TOML syntax.\n"
                    f"Details: {str(e)}\n"
                    "What to do next: Verify the file syntax, fix invalid keys/values, or delete the file to restore defaults."
                )
        return DEFAULT_CONFIG.copy()

    def reload_if_needed(self) -> Dict[str, Any]:
        if self.source and self.source.exists():
            mtime = self.source.stat().st_mtime
            if self._mtime is None or mtime > self._mtime:
                self.config = self.load()
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, DEFAULT_CONFIG.get(key, default))

    def get_all(self) -> Dict[str, Any]:
        return self.config

    def save(self, data: Dict[str, Any]) -> None:
        """Write the given config dict to the user config file (TOML).

        Ensures the config directory exists and applies restrictive file permissions.
        """
        try:
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.user_config, "wb") as f:
                f.write(tomli_w.dumps(data).encode("utf-8"))
            # Restrict permissions to user only (POSIX)
            try:
                os.chmod(self.user_config, 0o600)
            except Exception:
                # On Windows, os.chmod may be limited; ignore failures
                pass
            # Reload
            self.source = self.user_config
            self.config = self.load()
        except Exception:
            raise
