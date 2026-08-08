import pytest
import os
from orix.core.toolbox import WorkspaceToolbox

def test_toolbox_read_write_valid(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))

    # Write file tool
    res = toolbox.call_tool("write_file", {"relative_path": "sub/code.py", "content": "print('ok')"})
    assert res["success"] is True
    assert "Successfully wrote" in res["result"]
    assert os.path.exists(tmp_path / "sub" / "code.py")

    # Read file tool
    res2 = toolbox.call_tool("read_file", {"relative_path": "sub/code.py"})
    assert res2["success"] is True
    assert res2["result"] == "print('ok')"

def test_toolbox_boundary_error(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))
    res = toolbox.call_tool("read_file", {"relative_path": "../outside.txt"})
    assert res["success"] is False
    assert "Workspace boundary check failed" in res["error"]

def test_toolbox_argument_validation(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))
    res = toolbox.call_tool("write_file", {"relative_path": "code.py"}) # missing 'content'
    assert res["success"] is False
    assert "Missing required parameter" in res["error"]
