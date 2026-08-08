import os
import shutil
from typing import Dict, Any

class Doctor:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)

    def run_diagnostics(self) -> Dict[str, Any]:
        """Run system/project diagnostics and output scores based on the Orix P1 Scoring Model."""
        security = 100
        testing = 100
        dependencies = 100
        architecture = 100

        issues = []

        # 1. Security check
        # Check if git is initialized
        if not os.path.exists(os.path.join(self.workspace_root, ".git")):
            security -= 15
            issues.append("[Security] Git repository is not initialized.")

        # Check permissions of sensitive files if config.toml exists
        cfg_file = os.path.join(self.workspace_root, "config.toml")
        if os.path.exists(cfg_file):
            mode = os.stat(cfg_file).st_mode
            # check if readable by others (not secure)
            if mode & 0o077:
                security -= 20
                issues.append("[Security] Config file config.toml has broad read permissions.")

        # 2. Testing check
        has_pytest = shutil.which("pytest") is not None
        has_test_dir = os.path.exists(os.path.join(self.workspace_root, "tests")) or os.path.exists(os.path.join(self.workspace_root, "test"))
        if not has_test_dir:
            testing -= 50
            issues.append("[Testing] No dedicated 'tests/' directory found.")
        if not has_pytest:
            testing -= 30
            issues.append("[Testing] 'pytest' framework binary not found on host path.")

        # 3. Dependencies check
        req_file = os.path.join(self.workspace_root, "requirements.txt")
        pkg_file = os.path.join(self.workspace_root, "package.json")
        if not os.path.exists(req_file) and not os.path.exists(pkg_file):
            dependencies -= 40
            issues.append("[Dependencies] No package lock or dependency files (requirements.txt, package.json) found.")
        else:
            if os.path.exists(req_file):
                with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if ">=" in content or "~=" in content or "==" not in content:
                        dependencies -= 15
                        issues.append("[Dependencies] Loose dependency versioning observed in requirements.txt (prefer explicit '==').")

        # 4. Architecture check
        # Check standard python layout
        has_app_src = os.path.exists(os.path.join(self.workspace_root, "app")) or os.path.exists(os.path.join(self.workspace_root, "orix"))
        if not has_app_src:
            architecture -= 30
            issues.append("[Architecture] Missing core app/ source directory structure.")

        overall = int((security + testing + dependencies + architecture) / 4)

        return {
            "scores": {
                "security": max(0, security),
                "testing": max(0, testing),
                "dependencies": max(0, dependencies),
                "architecture": max(0, architecture),
                "overall": max(0, overall)
            },
            "issues": issues,
            "scoring_model_documentation": (
                "Orix P1 Scoring Model:\n"
                "- Security: Deducts points for lack of git tracking or loose configuration permissions.\n"
                "- Testing: Checks for standard tests/ folder and pytest availability.\n"
                "- Dependencies: Looks for standard requirement files and checks for strict version pinning.\n"
                "- Architecture: Looks for standard project directory layouts."
            )
        }
