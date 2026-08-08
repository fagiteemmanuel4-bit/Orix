import os
import pytest
from orix.core.toolbox import WorkspaceToolbox

def test_toolbox_execute_read_write_file(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))

    # Write a new file
    write_res = toolbox.execute_tool("write_file", {
        "filepath": "source.py",
        "content": "print('hello')"
    })
    assert write_res["success"] is True
    assert os.path.exists(tmp_path / "source.py")

    # Read the file
    read_res = toolbox.execute_tool("read_file", {"filepath": "source.py"})
    assert read_res["success"] is True
    assert read_res["result"] == "print('hello')"

def test_toolbox_execute_edit_file(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))
    (tmp_path / "source.py").write_text("def run():\n    print('old')", encoding="utf-8")

    edit_res = toolbox.execute_tool("edit_file", {
        "filepath": "source.py",
        "old_content": "print('old')",
        "new_content": "print('new')"
    })
    assert edit_res["success"] is True
    assert "print('new')" in (tmp_path / "source.py").read_text()

def test_toolbox_execute_find_symbol_references(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))
    (tmp_path / "app.py").write_text("class DatabaseConnector:\n    pass\n", encoding="utf-8")

    # find_symbol check
    symbol_res = toolbox.execute_tool("find_symbol", {"symbol": "DatabaseConnector"})
    assert symbol_res["success"] is True
    assert len(symbol_res["result"]) == 1
    assert symbol_res["result"][0]["name"] == "DatabaseConnector"

def test_toolbox_execute_path_traversal(tmp_path):
    toolbox = WorkspaceToolbox(str(tmp_path))

    # Path traversal should return structured error with why and next_action
    res = toolbox.execute_tool("read_file", {"filepath": "../outside_sandbox.txt"})
    assert res["success"] is False
    assert "traversal" in res["error"]["message"].lower()
    assert "boundaries" in res["error"]["why"]
