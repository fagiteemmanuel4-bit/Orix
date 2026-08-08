import ast
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from orix.core.vector_store import SimpleVectorStore

try:
    from tree_sitter import Parser, Language  # optional
    TREE_SITTER_AVAILABLE = True
except Exception:
    TREE_SITTER_AVAILABLE = False

class WorkspaceIndexer:
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".go", ".rs", ".swift", ".kt", ".dart"}

    def __init__(self, root_path: str, storage_dir: Optional[str] = None):
        self.root_path = Path(root_path).resolve()
        self.store = SimpleVectorStore(storage_dir)
        self.file_symbols: Dict[str, List[Dict[str, Any]]] = {}
        self.file_imports: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, List[str]] = {}

    def list_files_to_index(self) -> List[Path]:
        return [p for p in self.root_path.rglob("*") if p.is_file() and p.suffix in self.CODE_EXTENSIONS]

    def index_workspace(self, paths: Optional[List[Path]] = None, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> None:
        self.store.clear()
        self.file_symbols.clear()
        self.file_imports.clear()
        self.dependencies.clear()

        if paths is None:
            paths = self.list_files_to_index()
        total = len(paths)
        for count, path in enumerate(paths, start=1):
            if progress_callback:
                progress_callback(count, total, str(path))
            self._index_file(path)

        # Build reverse relationships/dependencies
        self._build_relationships()

    def _index_file(self, path: Path) -> None:
        rel_path = str(path.relative_to(self.root_path))
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            return

        self.file_symbols[rel_path] = []
        self.file_imports[rel_path] = []

        # Parse python files with AST for highly detailed symbol relationships
        if path.suffix == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.file_symbols[rel_path].append({
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno
                        })
                    elif isinstance(node, ast.ClassDef):
                        self.file_symbols[rel_path].append({
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno
                        })
                    elif isinstance(node, ast.Import):
                        for name in node.names:
                            self.file_imports[rel_path].append(name.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.file_imports[rel_path].append(node.module)
                            for name in node.names:
                                self.file_imports[rel_path].append(f"{node.module}.{name.name}")
            except Exception:
                pass

        # Parse general symbols / keywords via regex for non-python files
        else:
            # Extract common function / class matches in JS/TS
            func_matches = re.findall(r"(?:function\s+(\w+)|class\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)|_?)\s*=>)", source)
            for fm in func_matches:
                name = next((n for n in fm if n), None)
                if name:
                    self.file_symbols[rel_path].append({
                        "type": "symbol",
                        "name": name,
                        "line": 1
                    })

            # Extract imports in JS/TS
            import_matches = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", source)
            for im in import_matches:
                self.file_imports[rel_path].append(im)

        # Also leverage existing chunk indexing into vector/substring store
        ts_chunks = self._try_tree_sitter_chunks(source, path) if TREE_SITTER_AVAILABLE else None
        if ts_chunks:
            chunks = ts_chunks
        elif path.suffix == ".py":
            chunks = self._ast_chunks(source)
        else:
            chunks = self._text_chunks(source)

        for idx, chunk in enumerate(chunks):
            self.store.add_chunk(
                str(path),
                f"{path.name}-{idx}",
                chunk["text"],
                {"path": str(path), "type": chunk["type"], "name": chunk.get("name", ""), "length": len(chunk["text"])},
            )

    def _build_relationships(self):
        # Resolve which files depend on other files based on imports or references
        for file_path, imports in self.file_imports.items():
            self.dependencies[file_path] = []
            for imp in imports:
                # Find if imported name resolves to another file in the workspace
                imp_parts = imp.split('.')
                for target_file in self.file_symbols.keys():
                    target_base = os.path.splitext(target_file)[0].replace(os.path.sep, '.')
                    if imp.startswith(target_base) or any(part in target_file for part in imp_parts):
                        if target_file != file_path and target_file not in self.dependencies[file_path]:
                            self.dependencies[file_path].append(target_file)

    def find_authentication_files(self) -> List[str]:
        """Query: 'Where is authentication implemented?'

        Searches indexed files, function names, and comments for auth-related terms.
        """
        auth_keywords = {"auth", "login", "jwt", "token", "password", "authenticate", "credential"}
        matched_files = set()

        # 1. Search in file paths & symbols
        for file_path, symbols in self.file_symbols.items():
            file_lower = file_path.lower()
            if any(kw in file_lower for kw in auth_keywords):
                matched_files.add(file_path)
                continue

            for sym in symbols:
                if any(kw in sym["name"].lower() for kw in auth_keywords):
                    matched_files.add(file_path)
                    break

        # 2. Substring query inside code chunks
        chunks = self.store.query("auth") + self.store.query("login") + self.store.query("jwt")
        for chunk in chunks:
            path = chunk["path"]
            try:
                rel_path = str(Path(path).relative_to(self.root_path))
                matched_files.add(rel_path)
            except Exception:
                pass

        return sorted(list(matched_files))

    def find_dependents_of_symbol(self, symbol_name: str) -> List[str]:
        """Query: 'What files depend on this function/symbol?'

        Looks at imported references or direct name references in all workspace files.
        """
        dependents = set()
        symbol_lower = symbol_name.lower()

        for file_path, symbols in self.file_symbols.items():
            # Check if file imports the symbol or module
            imports = self.file_imports.get(file_path, [])
            if any(symbol_lower in imp.lower() for imp in imports):
                dependents.add(file_path)
                continue

            # Or check if any chunk contains the symbol name text
            chunks = self.store.query(symbol_name)
            for chunk in chunks:
                try:
                    rel_path = str(Path(chunk["path"]).relative_to(self.root_path))
                    if rel_path != file_path:
                        dependents.add(rel_path)
                except Exception:
                    pass

        return sorted(list(dependents))

    def _ast_chunks(self, source: str) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._text_chunks(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunks.append({"type": "function", "name": node.name, "text": ast.get_source_segment(source, node) or ""})
            elif isinstance(node, ast.ClassDef):
                chunks.append({"type": "class", "name": node.name, "text": ast.get_source_segment(source, node) or ""})
            elif isinstance(node, ast.Assign):
                text = ast.get_source_segment(source, node) or ""
                if text:
                    chunks.append({"type": "assignment", "text": text})
        if not chunks:
            chunks = self._text_chunks(source)
        return chunks

    def _try_tree_sitter_chunks(self, source: str, path: Path) -> Optional[List[Dict[str, Any]]]:
        try:
            lang_bundle = Path.home() / ".orix" / "tree_sitter_langs.so"
            if not lang_bundle.exists():
                return None

            ext = path.suffix.lstrip('.')
            Language.build_library  # type: ignore
            LANGUAGE = Language(str(lang_bundle), ext)
            parser = Parser()
            parser.set_language(LANGUAGE)
            tree = parser.parse(bytes(source, "utf8"))

            chunks: List[Dict[str, Any]] = []

            def visit(node):
                if node.type in ("function_definition", "function", "method_definition", "class_definition", "class", "method_declaration", "function_declaration"):
                    start = node.start_byte
                    end = node.end_byte
                    text = source.encode("utf8")[start:end].decode("utf8", errors="ignore")
                    chunks.append({"type": node.type, "text": text})
                for c in node.children:
                    visit(c)

            visit(tree.root_node)
            return chunks if chunks else None
        except Exception:
            return None

    def _text_chunks(self, text: str, chunk_size: int = 800) -> List[Dict[str, Any]]:
        lines = text.splitlines()
        chunks: List[Dict[str, Any]] = []
        current: List[str] = []
        for line in lines:
            current.append(line)
            if len(current) >= chunk_size:
                chunks.append({"type": "text", "text": "\n".join(current)})
                current = []
        if current:
            chunks.append({"type": "text", "text": "\n".join(current)})
        return chunks
