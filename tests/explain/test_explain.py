import pytest
import os
from orix.core.explain import Explainer

def test_explain_valid_file(tmp_path):
    code_file = tmp_path / "app.py"
    code_file.write_text("""
import sys

def process_data(value):
    return value + 1
""", encoding="utf-8")

    exp = Explainer(str(tmp_path))
    res = exp.explain_path("app.py")

    assert "Python module" in res["purpose"]
    assert "sys" in res["dependencies"]
    assert "Function: def process_data()" in res["important_functions"]
    assert "execution_flow" in res

def test_explain_missing_file(tmp_path):
    exp = Explainer(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        exp.explain_path("missing.py")

def test_explain_binary_file(tmp_path):
    binary_file = tmp_path / "asset.bin"
    # Write some non-unicode binary content
    with open(binary_file, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    exp = Explainer(str(tmp_path))
    res = exp.explain_path("asset.bin")

    assert "Binary" in res["purpose"]
    assert not res["dependencies"]

def test_explain_large_file(tmp_path):
    large_file = tmp_path / "dump.log"
    # Write > 1MB of text
    with open(large_file, "w") as f:
        f.write("A" * (1 * 1024 * 1024 + 10))

    exp = Explainer(str(tmp_path))
    res = exp.explain_path("dump.log")

    assert "Large" in res["purpose"]
    assert "exceeds 1MB limit" in res["execution_flow"]
