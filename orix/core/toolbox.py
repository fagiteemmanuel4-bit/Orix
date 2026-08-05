import fnmatch
import os
import subprocess
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class WorkspaceToolbox:
    def __init__(self, root_path: str, dry_run: bool = False, auto_approve: bool = False):
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        self.auto_approve = auto_approve

    def resolve_path(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if not path.is_absolute():
            path = self.root_path / path
        return path.resolve()

    def read_file(self, relative_path: str) -> str:
        path = self.resolve_path(relative_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> Tuple[Path, str]:
        path = self.resolve_path(relative_path)
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""
        diff = self.compute_diff(old_content, content, str(path))
        if self.dry_run:
            return path, diff
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path, diff

    def search_code(self, query: str, patterns: Optional[List[str]] = None) -> List[Path]:
        patterns = patterns or ["*.py", "*.js", "*.ts", "*.html", "*.css", "*.md"]
        matches: List[Path] = []
        for root, _, files in os.walk(self.root_path):
            for pattern in patterns:
                for filename in fnmatch.filter(files, pattern):
                    path = Path(root) / filename
                    try:
                        text = path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if query.lower() in text.lower() or query.lower() in filename.lower():
                        matches.append(path)
        return matches

    def list_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
        patterns = patterns or ["*"]
        files: List[Path] = []
        for root, _, filenames in os.walk(self.root_path):
            for pattern in patterns:
                for filename in fnmatch.filter(filenames, pattern):
                    files.append(Path(root) / filename)
        return files

    def run_shell(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, str]:
        if self.dry_run:
            return {"command": " ".join(command), "stdout": "[dry run]", "stderr": "", "returncode": 0}
        cwd_path = self.resolve_path(cwd) if cwd else self.root_path
        process = subprocess.run(command, capture_output=True, text=True, cwd=str(cwd_path), shell=False)
        return {
            "command": " ".join(command),
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode,
        }

    def git_status(self) -> str:
        result = self.run_shell(["git", "status", "--short"])
        return result["stdout"]

    def git_diff(self, args: Optional[List[str]] = None) -> str:
        args = args or ["--stat"]
        result = self.run_shell(["git", "diff"] + args)
        return result["stdout"]

    def git_current_branch(self) -> str:
        result = self.run_shell(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return result["stdout"].strip()

    def compute_diff(self, old: str, new: str, filename: str) -> str:
        return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=f"{filename}.old", tofile=filename, lineterm=""))
