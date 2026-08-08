import os
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional

class OrixExplain:
    def __init__(self, workspace_root: Optional[str] = None):
        self.root = Path(workspace_root or os.getcwd()).resolve()

    def explain_path(self, target_path: str) -> Dict[str, Any]:
        path = Path(target_path)
        if not path.is_absolute():
            path = self.root / path
        resolved = path.resolve()

        # Workspace boundary check
        try:
            resolved.relative_to(self.root)
        except ValueError:
            raise ValueError(f"Path '{target_path}' is outside the workspace boundary '{self.root}'")

        if not resolved.exists():
            raise FileNotFoundError(f"Target path '{target_path}' does not exist.")

        if resolved.is_dir():
            return self._explain_directory(resolved)
        else:
            return self._explain_file(resolved)

    def _explain_file(self, path: Path) -> Dict[str, Any]:
        # Handle potential binary file check
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {
                "type": "binary_file",
                "path": str(path.relative_to(self.root)),
                "purpose": "Binary or non-UTF-8 compiled resource file.",
                "dependencies": [],
                "important_functions": [],
                "execution_flow": "Executed or loaded as an external asset/binary package.",
                "risks": ["Cannot be analyzed statically as source code.", "Verify binary source integrity before use."]
            }

        # Handle very large file check
        is_large = len(content) > 100000  # >100KB
        if is_large:
            content_sample = content[:10000]
            truncated_warning = "File is extremely large; performing static structure analysis on sample header only."
        else:
            content_sample = content
            truncated_warning = None

        purpose = f"Source code resource: '{path.name}'"
        dependencies: List[str] = []
        important_functions: List[str] = []
        execution_flow = "Linear evaluation of source lines from top to bottom."
        risks: List[str] = []

        if path.suffix == ".py":
            try:
                tree = ast.parse(content_sample)
                # Parse docstrings for purpose
                doc = ast.get_docstring(tree)
                if doc:
                    purpose = doc.split("\n")[0]
                else:
                    purpose = f"Python module containing code structure for '{path.stem}'."

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            dependencies.append(name.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.append(node.module)
                    elif isinstance(node, ast.FunctionDef):
                        important_functions.append(f"Function: {node.name}()")
                    elif isinstance(node, ast.ClassDef):
                        important_functions.append(f"Class: {node.name}")

                if "if __name__ == '__main__':" in content_sample:
                    execution_flow = "Executable script. Triggers entry point block under '__main__'."
                else:
                    execution_flow = "Importable library module containing reusable functions/classes."

                # Security / design risks
                if "eval(" in content_sample or "exec(" in content_sample:
                    risks.append("Contains highly dangerous 'eval()' or 'exec()' statement.")
                if "shell=True" in content_sample:
                    risks.append("Runs subprocesses with 'shell=True', vulnerable to shell injection.")
                if len(content) > 50000:
                    risks.append("Module size is large. Consider refactoring into submodules for modularity.")

            except Exception as e:
                purpose = f"Python source file (unable to parse fully: {str(e)})"
        else:
            # Simple text pattern checks for other files (JS, TS, JSON, etc.)
            purpose = f"Text or configuration file: '{path.name}'"
            if "import " in content_sample:
                dependencies.append("External ES6/Typescript resources")
            if "function " in content_sample:
                important_functions.append("Custom functional blocks detected via text search")

        if not risks:
            risks.append("None detected. Follows standard code patterns.")

        return {
            "type": "file",
            "path": str(path.relative_to(self.root)),
            "purpose": purpose,
            "dependencies": list(set(dependencies)),
            "important_functions": important_functions[:15],
            "execution_flow": execution_flow,
            "risks": risks,
            "warning": truncated_warning
        }

    def _explain_directory(self, path: Path) -> Dict[str, Any]:
        files_summary = []
        subdirs = []
        for item in path.iterdir():
            if item.is_dir():
                if item.name not in (".git", "__pycache__", ".orix", "venv", ".venv"):
                    subdirs.append(item.name)
            else:
                files_summary.append(item.name)

        purpose = f"Workspace directory: '{path.name}'"
        if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
            purpose = f"Python project directory root: '{path.name}'"
        elif (path / "package.json").exists():
            purpose = f"NodeJS/Frontend project directory root: '{path.name}'"

        return {
            "type": "directory",
            "path": str(path.relative_to(self.root)) if path != self.root else ".",
            "purpose": purpose,
            "subdirectories": subdirs[:10],
            "files": files_summary[:20],
            "execution_flow": "Workspace container folder hosting components, templates, or tests.",
            "risks": ["Make sure correct permissions are set on files within this folder."]
        }
