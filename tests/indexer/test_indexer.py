import os
import pytest
from orix.core.indexer import WorkspaceIndexer

def test_indexer_symbol_and_dependents(tmp_path):
    # Setup files with dependencies
    (tmp_path / "module_a.py").write_text("class CoreService:\n    def execute(self):\n        pass\n", encoding="utf-8")
    (tmp_path / "module_b.py").write_text("from module_a import CoreService\n", encoding="utf-8")

    indexer = WorkspaceIndexer(str(tmp_path), storage_dir=str(tmp_path))
    indexer.index_workspace()

    # Query symbol locations
    locs = indexer.find_symbol_locations("CoreService")
    assert len(locs) == 1
    assert "module_a.py" in locs[0]["path"]

    # Query dependents / import paths
    deps = indexer.get_dependents("module_a")
    assert len(deps) == 1
    assert "module_b.py" in deps[0]
