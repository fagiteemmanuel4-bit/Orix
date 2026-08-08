import os
import pytest
from pathlib import Path
from orix.core.config import ConfigManager, DEFAULT_CONFIG

def test_config_manager_load_defaults(tmp_path):
    # Set XDG_CONFIG_HOME to tmp_path to avoid modifying actual home directories
    os.environ["XDG_CONFIG_HOME"] = str(tmp_path)

    cfg = ConfigManager(str(tmp_path))
    assert cfg.get("context_window") == 128000
    assert cfg.get("vision_model") == "claude-3-5-sonnet"

def test_config_manager_save_and_reload(tmp_path):
    os.environ["XDG_CONFIG_HOME"] = str(tmp_path)

    cfg = ConfigManager(str(tmp_path))
    custom_data = {
        "context_window": 5000,
        "vision_model": "gpt-4-custom",
        "allowlist": ["https://custom-api.com"]
    }
    cfg.save(custom_data)

    # Verify file was written
    assert cfg.user_config.exists()

    # Reload config
    cfg2 = ConfigManager(str(tmp_path))
    assert cfg2.get("context_window") == 5000
    assert cfg2.get("vision_model") == "gpt-4-custom"
    assert cfg2.get("allowlist") == ["https://custom-api.com"]
