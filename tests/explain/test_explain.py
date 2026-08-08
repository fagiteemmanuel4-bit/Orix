import os
import pytest
from orix.core.explain import OrixExplain

def test_explain_valid_file(tmp_path):
    explainer = OrixExplain(str(tmp_path))
    file_path = tmp_path / "app.py"
    file_path.write_text("import os\n\ndef main_runner():\n    pass\n", encoding="utf-8")

    report = explainer.explain_path("app.py")
    assert report["type"] == "file"
    assert "os" in report["dependencies"]
    assert "Function: main_runner()" in report["important_functions"]

def test_explain_missing_file(tmp_path):
    explainer = OrixExplain(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        explainer.explain_path("missing_file.py")

def test_explain_directory(tmp_path):
    explainer = OrixExplain(str(tmp_path))
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "core.py").write_text("pass", encoding="utf-8")

    report = explainer.explain_path("sub")
    assert report["type"] == "directory"
    assert "sub" in report["path"]
