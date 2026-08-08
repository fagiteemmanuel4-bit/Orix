import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from orix.core.permissions import PermissionManager
from orix.core.toolbox import WorkspaceToolbox
from orix.core.agent import AgentSession

# --- Workspace Boundary & Invalid Path Tests ---

def test_workspace_boundary_valid_path(tmp_path):
    # Setup workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "file.txt").write_text("hello", encoding="utf-8")

    toolbox = WorkspaceToolbox(str(workspace))

    # Resolving a file inside the workspace should succeed
    resolved = toolbox.resolve_path("file.txt")
    assert resolved == (workspace / "file.txt").resolve()

def test_workspace_boundary_invalid_path_traversal(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    toolbox = WorkspaceToolbox(str(workspace))

    # Path traversal outside the workspace should raise ValueError
    with pytest.raises(ValueError, match="Path traversal detected"):
        toolbox.resolve_path("../outside.txt")

def test_workspace_boundary_absolute_outside_path(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    toolbox = WorkspaceToolbox(str(workspace))

    # Any absolute path pointing outside the workspace should raise ValueError
    with pytest.raises(ValueError, match="Path traversal detected"):
        toolbox.resolve_path("/etc/passwd")


# --- Permissions & Safety Tests ---

def test_permission_manager_is_allowed_domain():
    pm = PermissionManager({"allowlist": ["https://api.openai.com"]})
    assert pm.is_allowed_domain("https://api.openai.com/v1/models") is True
    assert pm.is_allowed_domain("https://malicious.com") is False

@patch("orix.core.permissions.console.input")
def test_permission_manager_request_allow(mock_input):
    mock_input.return_value = "yes"
    pm = PermissionManager({})

    allowed = pm.request("read_file", "AI wants to read sensitive file")
    assert allowed is True

@patch("orix.core.permissions.console.input")
def test_permission_manager_request_deny(mock_input):
    mock_input.return_value = "no"
    pm = PermissionManager({})

    allowed = pm.request("delete_file", "AI wants to delete everything")
    assert allowed is False

def test_permission_manager_force_mode():
    pm = PermissionManager({})
    # Force mode should auto-approve without asking
    allowed = pm.request("shell_command", "any", force=True)
    assert allowed is True

@patch("orix.core.permissions.console.input")
def test_permission_manager_verify_url(mock_input):
    # Allowed domain should bypass input prompt
    pm = PermissionManager({"allowlist": ["https://safe-domain.com"]})
    assert pm.verify_url("https://safe-domain.com/data") is True
    assert mock_input.call_count == 0

    # Unallowed domain should trigger input prompt
    mock_input.return_value = "no"
    assert pm.verify_url("https://unallowed-domain.com") is False
    assert mock_input.call_count == 1


# --- Agent Session Loop Tests ---

@patch("orix.core.agent.WorkspaceToolbox.call_tool")
def test_agent_session_success_loop(mock_call_tool, tmp_path):
    # Mock toolbox responses for the full execution loop
    mock_call_tool.side_effect = [
        {"success": True, "result": ["main.py"]}, # inspect_project
        {"success": True, "result": "print('hello')"}, # read_file
        {"success": True, "result": "Successfully wrote file"}, # write_file
        {"success": True, "result": {"exit_code": 0, "stdout": "Passed", "stderr": ""}}, # run_test (first attempt succeeds)
        {"success": True, "result": {"exit_code": 0, "stdout": "", "stderr": ""}} # run_linter
    ]

    session = AgentSession(str(tmp_path), mode="force", force=True)
    plan = session._plan("Modify main.py")
    res = session._execute_plan(plan)

    assert res["success"] is True
    assert mock_call_tool.call_count == 5

@patch("orix.core.agent.WorkspaceToolbox.call_tool")
def test_agent_session_failed_loop_exceeded(mock_call_tool, tmp_path):
    # Mock toolbox responses: test suite fails continually
    mock_call_tool.side_effect = [
        {"success": True, "result": ["main.py"]}, # inspect_project
        {"success": True, "result": "print('hello')"}, # read_file
        {"success": True, "result": "Successfully wrote file"}, # write_file
        {"success": True, "result": {"exit_code": 1, "stdout": "Fail", "stderr": "SyntaxError"}}, # run_test 1
        {"success": True, "result": "Successfully wrote file"}, # write_file (repair 1)
        {"success": True, "result": {"exit_code": 1, "stdout": "Fail", "stderr": "SyntaxError"}}, # run_test 2
        {"success": True, "result": "Successfully wrote file"}, # write_file (repair 2)
        {"success": True, "result": {"exit_code": 1, "stdout": "Fail", "stderr": "SyntaxError"}}, # run_test 3
        {"success": True, "result": "Successfully wrote file"}, # write_file (repair 3)
    ]

    session = AgentSession(str(tmp_path), mode="force", force=True, max_repair_attempts=2)
    plan = session._plan("Modify main.py")
    res = session._execute_plan(plan)

    # Since attempts exceeded max_repair_attempts (2), it should fail safely
    assert res["success"] is False
    assert "Auto-repair failed" in res["error"]
