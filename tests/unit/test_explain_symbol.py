import os
import tempfile
from pathlib import Path
from orix.core.explain import OrixExplain
from orix.core.indexer import WorkspaceIndexer

def test_explain_symbol_lookup():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock file with a class definition
        code_file = Path(tmp_dir) / "math_helper.py"
        code_file.write_text("""
class MathEngine:
    \"\"\"An advanced math computing engine.\"\"\"
    def add(self, a, b):
        return a + b
""", encoding="utf-8")

        # Index the directory
        indexer = WorkspaceIndexer(tmp_dir)
        files = indexer.list_files_to_index()
        indexer.index_workspace(files)

        # Run Explain
        explainer = OrixExplain(tmp_dir)
        report = explainer.explain_symbol("MathEngine")

        assert report["type"] == "symbol"
        assert report["name"] == "MathEngine"
        assert report["symbol_type"] == "class"
        assert "MathEngine" in report["text"]
