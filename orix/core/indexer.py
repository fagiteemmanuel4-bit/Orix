import ast
import os
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
    def list_files_to_index(self) -> List[Path]:
        return [p for p in self.root_path.rglob("*") if p.is_file() and p.suffix in self.CODE_EXTENSIONS]

    def index_workspace(self, paths: Optional[List[Path]] = None, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> None:
        self.store.clear()
        if paths is None:
            paths = self.list_files_to_index()
        total = len(paths)
        for count, path in enumerate(paths, start=1):
            if progress_callback:
                progress_callback(count, total, str(path))
            self._index_file(path)

    def _index_file(self, path: Path) -> None:
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            return
        # Prefer language-aware chunking if tree-sitter is available and configured
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
        # This method attempts to use a prebuilt tree-sitter Language library if available.
        # It is intentionally defensive: if no shared language library is found or parsing fails,
        # it returns None to let existing fallbacks take over.
        try:
            # Look for a user-provided shared library of languages. This is optional and
            # non-prescriptive; users can place a compiled language bundle at ~/.orix/tree_sitter_langs.so
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
                # node.type varies by language; look for common function/class names
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
