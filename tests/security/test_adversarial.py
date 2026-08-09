import pytest
import os
import requests
from pathlib import Path
from orix.core.toolbox import WorkspaceToolbox
from orix.core.ai_providers import get_provider

def test_adversarial_sandbox_escape(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    toolbox = WorkspaceToolbox(str(root))

    # Attempt to write or read outside sandbox
    escapes = [
        "../outside.py",
        "/etc/passwd",
        "../../etc/hosts"
    ]
    for esc in escapes:
        res = toolbox.execute_tool("read_file", {"filepath": esc})
        assert res["success"] is False
        assert "traversal" in res["error"]["message"].lower()
        assert "target path violates the absolute workspace sandboxed boundaries" in res["error"]["why"]

def test_api_provider_failures_and_timeouts():
    # 1. API key auth failure
    provider = get_provider({"provider": "mock", "mock_failure": "auth"})
    with pytest.raises(ValueError, match="Mock API invalid key"):
        provider.generate([{"role": "user", "content": "hello"}])

    # 2. Timeout handling
    provider_timeout = get_provider({"provider": "mock", "mock_failure": "timeout"})
    with pytest.raises(requests.exceptions.Timeout, match="timed out"):
        provider_timeout.generate([{"role": "user", "content": "hello"}])

    # 3. Rate limiting
    provider_rate = get_provider({"provider": "mock", "mock_failure": "rate_limit"})
    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        provider_rate.generate([{"role": "user", "content": "hello"}])
