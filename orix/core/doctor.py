import os
from pathlib import Path
from typing import Dict, Any, List

class OrixDoctor:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()

    def run_diagnostics(self) -> Dict[str, Any]:
        findings: List[Dict[str, str]] = []

        # 1. Check for missing Git repo (Severity: HIGH)
        if not (self.root / ".git").exists():
            findings.append({
                "severity": "HIGH",
                "category": "Security",
                "message": "Missing active Git repository (.git directory not found). Ensure changes are tracked under version control."
            })

        # 2. Check for hardcoded API keys/secrets (Severity: CRITICAL)
        found_keys = False
        found_danger = False
        key_patterns = ["api_key =", "password =", "secret =", "token ="]
        dangerous_patterns = ["eval(", "exec(", "subprocess.Popen(..., shell=True)"]

        for path in self.root.rglob("*.py"):
            if any(p in path.parts for p in [".venv", "venv", "env", "build", "dist", ".git", "__pycache__"]):
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for kpat in key_patterns:
                    if kpat in content:
                        lines = [l for l in content.splitlines() if kpat in l]
                        if any('"' in l or "'" in l for l in lines):
                            found_keys = True
                for dpat in dangerous_patterns:
                    if dpat in content:
                        found_danger = True
            except Exception:
                pass

        if found_keys:
            findings.append({
                "severity": "CRITICAL",
                "category": "Security",
                "message": "Potential hardcoded credentials or API keys detected in source code files. Migrate to environment variables."
            })

        # 3. Check for dangerous execution commands (Severity: HIGH)
        if found_danger:
            findings.append({
                "severity": "HIGH",
                "category": "Security",
                "message": "Unsafe python code patterns detected (eval, exec, or shell=True executions), highly vulnerable to injection."
            })

        # 4. Check for tests folder (Severity: HIGH)
        test_dir = self.root / "tests"
        if not test_dir.exists():
            findings.append({
                "severity": "HIGH",
                "category": "Testing",
                "message": "Missing 'tests/' folder. Automated testing is fundamental for code quality and continuous integration."
            })
        else:
            test_files = list(test_dir.rglob("test_*.py")) + list(test_dir.rglob("*_test.py"))
            if not test_files:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "Testing",
                    "message": "The 'tests/' folder exists but contains no Python test suite files."
                })

        # 5. Check for test config (Severity: MEDIUM)
        has_test_config = any((self.root / f).exists() for f in ["pytest.ini", "pyproject.toml", "setup.cfg", "jest.config.js"])
        if not has_test_config:
            findings.append({
                "severity": "MEDIUM",
                "category": "Testing",
                "message": "No test configuration file detected (pytest.ini or pyproject.toml)."
            })

        # 6. Check for dependency descriptors (Severity: HIGH)
        package_files = ["requirements.txt", "pyproject.toml", "package.json", "setup.py"]
        has_package_file = any((self.root / f).exists() for f in package_files)
        if not has_package_file:
            findings.append({
                "severity": "HIGH",
                "category": "Dependencies",
                "message": "No standard dependency descriptor file found (requirements.txt or pyproject.toml)."
            })
        else:
            # Check for lock files if descriptors exist
            lock_files = ["package-lock.json", "poetry.lock", "yarn.lock", "Pipfile.lock"]
            has_lock_file = any((self.root / f).exists() for f in lock_files)
            if not has_lock_file:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "Dependencies",
                    "message": "Lock file is missing (poetry.lock or package-lock.json). Package installations may not be reproducible."
                })

        # 7. Monolithic layouts (Severity: LOW)
        root_py_files = list(self.root.glob("*.py"))
        subfolder_py_files = list(self.root.glob("**/core/*.py")) + list(self.root.glob("**/app/*.py"))
        if len(root_py_files) > 5 and len(subfolder_py_files) == 0:
            findings.append({
                "severity": "LOW",
                "category": "Architecture",
                "message": "Flat root project layout detected. Consider organizing modules under standard subfolders."
            })

        # Check for Orix workspace specs (Severity: LOW)
        if not (self.root / ".orix").exists():
            findings.append({
                "severity": "LOW",
                "category": "Architecture",
                "message": "Orix active specifications folder (.orix/) is not configured."
            })

        # Score Calculations derived strictly from findings
        scores = {
            "Security": 100,
            "Testing": 100,
            "Dependencies": 100,
            "Architecture": 100
        }

        for f in findings:
            cat = f["category"]
            sev = f["severity"]

            # Deduction rule mapping
            deduction = 0
            if sev == "CRITICAL":
                deduction = 30
            elif sev == "HIGH":
                deduction = 15
            elif sev == "MEDIUM":
                deduction = 10
            elif sev == "LOW":
                deduction = 5

            scores[cat] = max(0, scores[cat] - deduction)

        # Average Overall Score
        overall_score = round(sum(scores.values()) / len(scores))
        scores["Overall"] = overall_score

        return {
            "scores": scores,
            "findings": findings,
            "scoring_model": (
                "Scoring Model Documentation (Evidence-Driven Rules):\n"
                "  - Base Score starts at 100 per category.\n"
                "  - Deductions applied dynamically for each identified finding:\n"
                "    * CRITICAL findings: -30 points (e.g. hardcoded secrets)\n"
                "    * HIGH findings: -15 points (e.g. missing Git, missing tests directory, unsafe eval/exec execution)\n"
                "    * MEDIUM findings: -10 points (e.g. missing lock files, missing pytest/jest configs)\n"
                "    * LOW findings: -5 points (e.g. missing .orix specifications directory, monolithic root files layout)\n"
                "  - Overall Score: Unweighted arithmetic mean of the four category scores."
            )
        }
