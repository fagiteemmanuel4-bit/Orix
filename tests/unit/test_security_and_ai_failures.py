import pytest
import os
from pathlib import Path
from orix.core.toolbox import WorkspaceToolbox
from orix.core.ai_providers import AIProvider, OpenAIProvider

def test_toolbox_path_traversal_boundaries(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()

    # Fully resolved workspace boundary
    toolbox = WorkspaceToolbox(str(root))

    # Dot dot attempts should raise ValueError
    with pytest.raises(ValueError, match="Path traversal detected"):
        toolbox.resolve_path("../outside_file.txt")

    # Absolute paths outside workspace should raise ValueError
    with pytest.raises(ValueError, match="Path traversal detected"):
        toolbox.resolve_path("/etc/passwd")

def test_ai_provider_malformed_json_repair_failure():
    # Test that AIProvider generate_structured_output raises clean ValueError on malformed output
    provider = AIProvider({"provider": "openai", "api_key": "dummy"})

    # Mock generate_text to return totally malformed JSON that cannot be parsed
    provider.generate_text = lambda prompt: "This is not JSON at all!"

    schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }

    with pytest.raises(ValueError, match="Failed to parse structured JSON"):
        provider.generate_structured_output("Any prompt", schema)

def test_ai_provider_missing_required_schema_field():
    provider = AIProvider({"provider": "openai", "api_key": "dummy"})

    # Returns valid JSON but misses required field 'test'
    provider.generate_text = lambda prompt: '{"other_field": "val"}'

    schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }

    with pytest.raises(ValueError, match="missing required key 'test'"):
        provider.generate_structured_output("Any prompt", schema)
