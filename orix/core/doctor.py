import os
from pathlib import Path
from typing import Dict, Any, List

class OrixDoctor:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()

    def run_diagnostics(self) -> Dict[str, Any]:
        security_score = 100
        testing_score = 100
        dependencies_score = 100
        architecture_score = 100

        security_issues: List[str] = []
        testing_issues: List[str] = []
        dependencies_issues: List[str] = []
        architecture_issues: List[str] = []

        # 1. SECURITY BASICS
        # Git existence check
        git_dir = self.root / ".git"
        if not git_dir.exists():
            security_score -= 20
            security_issues.append("No active Git repository (.git directory is missing).")

        # Code-level static security checks
        dangerous_patterns = ["eval(", "exec(", "subprocess.Popen(..., shell=True)"]
        key_patterns = ["api_key =", "password =", "secret =", "token ="]

        found_danger = False
        found_keys = False
        for path in self.root.rglob("*.py"):
            # skip site-packages, build, dist, or virtual environments
            if any(p in path.parts for p in [".venv", "venv", "env", "build", "dist", ".git", "__pycache__"]):
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for pat in dangerous_patterns:
                    if pat in content:
                        found_danger = True
                for kpat in key_patterns:
                    if kpat in content:
                        # Simple heuristic: only trigger if followed by a hardcoded string
                        line = [line for line in content.splitlines() if kpat in line]
                        if any('"' in l or "'" in l for l in line):
                            found_keys = True
            except Exception:
                pass

        if found_danger:
            security_score -= 15
            security_issues.append("Detected potential dangerous function calls (e.g. eval, exec, or unsafe shell executions).")
        if found_keys:
            security_score -= 15
            security_issues.append("Detected possible hardcoded secrets or credentials (e.g. raw api_key or token strings).")

        security_score = max(0, security_score)

        # 2. TESTING CONFIGURATION
        test_dir = self.root / "tests"
        if not test_dir.exists():
            testing_score -= 50
            testing_issues.append("No 'tests' directory found in the project root.")
        else:
            # Check for actual test files
            test_files = list(test_dir.rglob("test_*.py")) + list(test_dir.rglob("*_test.py"))
            if not test_files:
                testing_score -= 25
                testing_issues.append("The 'tests' directory exists but contains no Python test files (test_*.py).")

        # Test configuration existence
        has_test_config = any((self.root / f).exists() for f in ["pytest.ini", "pyproject.toml", "setup.cfg", "jest.config.js"])
        if not has_test_config:
            testing_score -= 20
            testing_issues.append("Missing explicit testing configuration file (pytest.ini, pyproject.toml, or jest.config.js).")

        testing_score = max(0, testing_score)

        # 3. DEPENDENCIES
        package_files = ["requirements.txt", "pyproject.toml", "package.json", "setup.py"]
        has_package_file = any((self.root / f).exists() for f in package_files)
        if not has_package_file:
            dependencies_score -= 40
            dependencies_issues.append("No standard dependency descriptor file found (requirements.txt, pyproject.toml, or package.json).")
        else:
            # Check for lock files if package descriptors exist
            lock_files = ["package-lock.json", "poetry.lock", "yarn.lock", "Pipfile.lock"]
            has_lock_file = any((self.root / f).exists() for f in lock_files)
            if not has_lock_file:
                dependencies_score -= 20
                dependencies_issues.append("Dependency lock file is missing (e.g., package-lock.json, poetry.lock).")

        dependencies_score = max(0, dependencies_score)

        # 4. ARCHITECTURE & DESIGN
        # Check if project files are all sitting in the root directory (poor modularity)
        root_py_files = list(self.root.glob("*.py"))
        subfolder_py_files = list(self.root.glob("**/core/*.py")) + list(self.root.glob("**/app/*.py"))
        if len(root_py_files) > 5 and len(subfolder_py_files) == 0:
            architecture_score -= 30
            architecture_issues.append("Monolithic layout: flat root directory contains many python files without clear folder separation.")

        # Check for .orix specs/config
        orix_dir = self.root / ".orix"
        if not orix_dir.exists():
            architecture_score -= 20
            architecture_issues.append("No Orix design workspace (.orix folder) detected.")

        architecture_score = max(0, architecture_score)

        # Average Overall Score
        overall_score = round((security_score + testing_score + dependencies_score + architecture_score) / 4)

        return {
            "scores": {
                "Security": security_score,
                "Testing": testing_score,
                "Dependencies": dependencies_score,
                "Architecture": architecture_score,
                "Overall": overall_score
            },
            "issues": {
                "Security": security_issues,
                "Testing": testing_issues,
                "Dependencies": dependencies_issues,
                "Architecture": architecture_issues
            },
            "scoring_model": (
                "Scoring Model Documentation:\n"
                "  - Security Score (100pt): -20 if no .git; -15 for dangerous functions (eval, exec); -15 for hardcoded secrets.\n"
                "  - Testing Score (100pt): -50 if no tests/ folder; -25 if folder is empty; -20 if no test config.\n"
                "  - Dependencies Score (100pt): -40 if no pyproject/requirements file; -20 if no dependency lock file.\n"
                "  - Architecture Score (100pt): -30 for monolithic layout; -20 if .orix specifications directory is missing.\n"
                "  - Overall Score: Unweighted mathematical mean of the above four indices."
            )
        }
