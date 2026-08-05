import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, List

try:
    from tree_sitter import Language  # type: ignore
    TREE_SITTER_PY_AVAILABLE = True
except Exception:
    TREE_SITTER_PY_AVAILABLE = False


DEFAULT_LANG_REPOS: Dict[str, str] = {
    "python": "https://github.com/tree-sitter/tree-sitter-python.git",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript.git",
    "typescript": "https://github.com/tree-sitter/tree-sitter-typescript.git",
    "rust": "https://github.com/tree-sitter/tree-sitter-rust.git",
    "go": "https://github.com/tree-sitter/tree-sitter-go.git",
    "java": "https://github.com/tree-sitter/tree-sitter-java.git",
}


def get_default_bundle_path() -> Path:
    p = Path.home() / ".orix"
    p.mkdir(parents=True, exist_ok=True)
    return p / "tree_sitter_langs.so"


def build_language_bundle(bundle_path: Optional[Path] = None, repos: Optional[Dict[str, str]] = None) -> Path:
    """Build a combined tree-sitter language shared library from grammar repos.

    This is best-effort: it requires system C toolchain and git. If any step fails
    a helpful exception is raised so the caller can fall back.
    """
    bundle_path = Path(bundle_path or get_default_bundle_path())
    repos = repos or DEFAULT_LANG_REPOS

    if not TREE_SITTER_PY_AVAILABLE:
        raise RuntimeError("tree_sitter Python package is not installed. Install via pip install tree_sitter")

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        local_dirs: List[str] = []
        for name, repo in repos.items():
            dest = td_path / name
            try:
                subprocess.run(["git", "clone", "--depth", "1", repo, str(dest)], check=True)
            except Exception as e:
                raise RuntimeError(f"Failed to clone {repo}: {e}")
            # Some repos (typescript) include multiple grammars under subdirs; point to repo root
            local_dirs.append(str(dest))

        try:
            Language.build_library(str(bundle_path), local_dirs)
        except Exception as e:
            raise RuntimeError(f"Failed to build tree-sitter language bundle: {e}")

    return bundle_path


def ensure_language_bundle(bundle_path: Optional[Path] = None, repos: Optional[Dict[str, str]] = None) -> Path:
    """Ensure a language bundle exists; build it if missing.

    Returns the bundle path if available; raises RuntimeError otherwise.
    """
    bundle = Path(bundle_path or get_default_bundle_path())
    if bundle.exists():
        return bundle
    return build_language_bundle(bundle, repos)
