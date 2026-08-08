import pytest
from pathlib import Path
from orix.core.indexer import WorkspaceIndexer

def test_indexer_symbol_and_dependent_lookups(tmp_path):
    # Setup standard files in tmp workspace
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    auth_file = app_dir / "auth.py"
    auth_file.write_text("""
def login_user(username, password):
    return "token_value"
""", encoding="utf-8")

    main_file = app_dir / "main.py"
    main_file.write_text("""
from app.auth import login_user

def run_app():
    return login_user("admin", "secret")
""", encoding="utf-8")

    indexer = WorkspaceIndexer(str(tmp_path))
    indexer.index_workspace()

    # Verify identified files
    assert "app/auth.py" in indexer.file_symbols
    assert "app/main.py" in indexer.file_symbols

    # Query: Where is authentication implemented?
    auth_files = indexer.find_authentication_files()
    assert "app/auth.py" in auth_files

    # Query: What files depend on 'login_user'?
    dependents = indexer.find_dependents_of_symbol("login_user")
    assert "app/main.py" in dependents
