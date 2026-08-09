import os
from pathlib import Path

def test_static_leakage_crawling():
    """Security audit: crawls all repository files and verify no hardcoded keys are committed."""
    root = Path(__file__).resolve().parent.parent.parent

    # Precise credential matchers
    for path in root.rglob("*"):
        if any(p in path.parts for p in [".venv", "venv", "env", "build", "dist", ".git", "__pycache__", "orix.egg-info", "tests"]):
            continue

        if path.is_file() and path.suffix in [".py", ".json", ".yaml", ".md", ".txt"]:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line_lower = line.lower()
                # Check for direct key assignments with string values
                if any(x in line_lower for x in ["api_key =", "password =", "token ="]):
                    # Ignore comment definitions, list patterns definitions, or placeholder example assignments
                    if any(p in line_lower for p in ["env", "os.get", "config", "default", "dummy", "none", "sk-proj-example", "key_patterns =", "key_patterns"]):
                        continue
                    if "[" in line or "]" in line:
                        continue
                    if '"' in line or "'" in line:
                        assert False, f"Potential hardcoded key/password detected in '{path.relative_to(root)}': {line.strip()}"
