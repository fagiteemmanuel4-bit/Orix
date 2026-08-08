import os
import pytest
from unittest.mock import MagicMock, patch
from orix.core.agent import AgentSession

def test_agent_session_plan_mode(tmp_path):
    # Plan mode should display plan without writing or modifying files
    session = AgentSession(
        root_path=str(tmp_path),
        mode="plan",
        initial_prompt="Add simple function to test.py",
        force=False
    )

    with patch.object(session, "_display_thinking_panel") as mock_thinking:
        session.run()
        assert mock_thinking.call_count == 1
        assert session.sandbox_state == "idle"

@patch("orix.core.permissions.Console.input")
def test_agent_session_interactive_approval(mock_input, tmp_path):
    # Test file setup
    test_file = tmp_path / "test.py"
    test_file.write_text("def run():\n    pass\n", encoding="utf-8")

    # User denies action
    mock_input.return_value = "no"

    session = AgentSession(
        root_path=str(tmp_path),
        mode="interactive",
        initial_prompt="modify test.py",
        force=False
    )

    session.run()
    # verify file content was not mutated/appended with edits because permission was denied
    assert "Orix Agent" not in test_file.read_text()
