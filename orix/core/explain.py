import os
import ast
import re
from typing import Dict, Any

class Explainer:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)

    def explain_path(self, target_path: str) -> Dict[str, Any]:
        """Generate architectural explanations based on actual source code of a file or directory."""
        resolved = Path_resolver_check = os.path.abspath(os.path.join(self.workspace_root, target_path))
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Path does not exist: '{target_path}'")

        if os.path.isdir(resolved):
            return self._explain_directory(resolved)
        else:
            return self._explain_file(resolved)

    def _explain_file(self, file_path: str) -> Dict[str, Any]:
        filename = os.path.basename(file_path)

        # Check if binary
        if self._is_binary_file(file_path):
            return {
                "path": file_path,
                "purpose": "Binary File / Resource Asset",
                "dependencies": [],
                "important_functions": [],
                "execution_flow": "No execution flow analysis available for binary files.",
                "potential_risks": ["Binary files can contain untrusted code. Ensure proper validation before execution."]
            }

        # Check if too large (e.g. > 1MB)
        if os.path.getsize(file_path) > 1 * 1024 * 1024:
            return {
                "path": file_path,
                "purpose": "Large File / Resource Asset",
                "dependencies": [],
                "important_functions": [],
                "execution_flow": "File size exceeds 1MB limit. Structural analysis bypassed for efficiency.",
                "potential_risks": ["Large files might contain database dumps, compiled assets, or logs."]
            }

        try:
            content = open(file_path, "r", encoding="utf-8", errors="ignore").read()
        except Exception as e:
            raise IOError(f"Could not read file: {e}")

        purpose = "Generic Source Code / Configuration File"
        dependencies = []
        important_functions = []
        execution_flow = "Loads top-level definitions sequentially."
        potential_risks = []

        # Python-specific AST extraction
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(content)
                doc = ast.get_docstring(tree)
                if doc:
                    purpose = doc
                else:
                    purpose = f"Python module '{filename}' providing structural logic and configurations."

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            dependencies.append(name.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.append(node.module)
                    elif isinstance(node, ast.FunctionDef):
                        important_functions.append(f"Function: def {node.name}()")
                    elif isinstance(node, ast.ClassDef):
                        important_functions.append(f"Class: class {node.name}")

                if important_functions:
                    execution_flow = f"Initializes modules and exposes functions: {', '.join(important_functions[:3])}."

                # Risk analysis
                if "eval(" in content or "exec(" in content:
                    potential_risks.append("Uses dangerous dynamic evaluation functions (eval/exec).")
                if "subprocess" in content and "shell=True" in content:
                    potential_risks.append("Runs subprocesses with shell=True, vulnerable to shell injection.")
            except Exception:
                purpose = "Python Source Code (AST parsing failed)"

        # General text-based regex extraction
        else:
            if filename == "package.json":
                purpose = "NodeJS Package Configuration and dependencies manager."
            elif filename == "requirements.txt":
                purpose = "Python pip packages dependencies list."

            # Find imports
            imports = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content)
            dependencies.extend(imports)

            # Find functions
            funcs = re.findall(r"function\s+(\w+)", content)
            for fn in funcs:
                important_functions.append(f"Function: {fn}")

        if not potential_risks:
            potential_risks.append("No obvious critical security vulnerabilities observed.")

        return {
            "path": file_path,
            "purpose": purpose,
            "dependencies": sorted(list(set(dependencies))),
            "important_functions": important_functions,
            "execution_flow": execution_flow,
            "potential_risks": potential_risks
        }

    def _explain_directory(self, dir_path: str) -> Dict[str, Any]:
        sub_files = []
        for root, _, files in os.walk(dir_path):
            if ".orix" in root or ".git" in root or "__pycache__" in root:
                continue
            for f in files:
                sub_files.append(os.path.join(root, f))

        purpose = f"Directory containing {len(sub_files)} project files."
        dependencies = set()
        important_functions = []
        potential_risks = []

        # Analyze top files
        for f in sub_files[:5]:
            try:
                res = self._explain_file(f)
                dependencies.update(res["dependencies"])
                important_functions.extend(res["important_functions"][:2])
                potential_risks.extend(res["potential_risks"])
            except Exception:
                pass

        return {
            "path": dir_path,
            "purpose": purpose,
            "dependencies": sorted(list(dependencies))[:10],
            "important_functions": important_functions[:10],
            "execution_flow": "Walks folders and executes module entries recursively.",
            "potential_risks": list(set(potential_risks)) if potential_risks else ["None found."]
        }

    def _is_binary_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'tr') as f:
                f.read(512)
            return False
        except UnicodeDecodeError:
            return True
