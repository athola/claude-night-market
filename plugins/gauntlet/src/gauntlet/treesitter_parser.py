"""Tree-sitter AST extraction for multi-language code graphs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind

try:
    from tree_sitter_language_pack import get_parser
except ImportError:  # pragma: no cover
    get_parser = None  # type: ignore[assignment]  # sentinel for missing optional dep

# ---------------------------------------------------------------------------
# Extension -> language mapping
# ---------------------------------------------------------------------------

_EXT_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".rb": "ruby",
    ".php": "php",
    ".kt": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
}

# AST node types per language for structural detection
_CLASS_TYPES: dict[str, set[str]] = {
    "python": {"class_definition"},
    "javascript": {"class_declaration", "class"},
    "typescript": {"class_declaration", "class"},
    "go": {"type_declaration"},
    "rust": {"struct_item", "enum_item", "impl_item"},
    "java": {"class_declaration", "interface_declaration"},
    "c_sharp": {"class_declaration", "interface_declaration"},
    "ruby": {"class", "module"},
    "php": {"class_declaration", "interface_declaration"},
    "kotlin": {"class_declaration", "object_declaration"},
    "swift": {"class_declaration", "struct_declaration"},
    "scala": {"class_definition", "object_definition"},
    "c": {"struct_specifier"},
    "cpp": {"class_specifier", "struct_specifier"},
}

_FUNCTION_TYPES: dict[str, set[str]] = {
    "python": {"function_definition"},
    "javascript": {"function_declaration", "method_definition", "arrow_function"},
    "typescript": {"function_declaration", "method_definition", "arrow_function"},
    "go": {"function_declaration", "method_declaration"},
    "rust": {"function_item"},
    "java": {"method_declaration", "constructor_declaration"},
    "c_sharp": {"method_declaration", "constructor_declaration"},
    "ruby": {"method", "singleton_method"},
    "php": {"function_definition", "method_declaration"},
    "kotlin": {"function_declaration"},
    "swift": {"function_declaration"},
    "scala": {"function_definition"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
}

_IMPORT_TYPES: dict[str, set[str]] = {
    "python": {"import_statement", "import_from_statement"},
    "javascript": {"import_statement"},
    "typescript": {"import_statement"},
    "go": {"import_declaration"},
    "rust": {"use_declaration"},
    "java": {"import_declaration"},
    "c_sharp": {"using_directive"},
    "ruby": {"call"},  # require/require_relative
    "php": {"namespace_use_declaration"},
    "kotlin": {"import_header"},
    "swift": {"import_declaration"},
    "scala": {"import_declaration"},
    "c": {"preproc_include"},
    "cpp": {"preproc_include"},
}

_TEST_PREFIXES = ("test_", "Test", "test", "spec_")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_language(file_path: str) -> str | None:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix
    return _EXT_TO_LANG.get(ext)


def parse_file(file_path: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Parse a source file and extract nodes and edges.

    Returns empty lists for unsupported languages or parse errors.
    """
    language = detect_language(file_path)
    if not language or get_parser is None:
        return [], []

    path = Path(file_path)
    if not path.exists():
        return [], []

    try:
        source = path.read_bytes()
        file_hash = hashlib.sha256(source).hexdigest()
    except OSError:
        return [], []

    try:
        parser = get_parser(language)  # type: ignore[arg-type]  # str from detect_language
        tree = parser.parse(source)
    except Exception as exc:  # noqa: BLE001 - catch-all for parse errors in unknown grammars
        import logging

        logging.getLogger(__name__).debug(
            "tree-sitter parse failed for %s: %s: %s",
            file_path,
            type(exc).__name__,
            exc,
        )
        return [], []

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # Always create a File node
    file_node = GraphNode(
        kind=NodeKind.FILE,
        qualified_name=file_path,
        file_path=file_path,
        line_start=0,
        line_end=tree.root_node.end_point[0],
        language=language,
        file_hash=file_hash,
    )
    nodes.append(file_node)

    _extract_from_tree(
        tree.root_node,
        file_path,
        language,
        file_hash,
        nodes,
        edges,
        parent_name="",
    )

    return nodes, edges


# ---------------------------------------------------------------------------
# Recursive AST walker
# ---------------------------------------------------------------------------


def _extract_from_tree(
    node: Any,
    file_path: str,
    language: str,
    file_hash: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    parent_name: str,
) -> None:
    """Walk the AST and extract structural nodes and relationship edges."""
    class_types = _CLASS_TYPES.get(language, set())
    func_types = _FUNCTION_TYPES.get(language, set())
    import_types = _IMPORT_TYPES.get(language, set())

    node_type = node.type

    if node_type in class_types:
        cls_name = _extract_name(node, language)
        if cls_name:
            qn = f"{file_path}::{cls_name}"
            graph_node = GraphNode(
                kind=NodeKind.CLASS,
                qualified_name=qn,
                file_path=file_path,
                line_start=node.start_point[0],
                line_end=node.end_point[0],
                language=language,
                parent_name=parent_name,
                file_hash=file_hash,
            )
            nodes.append(graph_node)

            # CONTAINS edge from file to class
            edges.append(
                GraphEdge(
                    kind=EdgeKind.CONTAINS,
                    source_qn=file_path,
                    target_qn=qn,
                    file_path=file_path,
                    line=node.start_point[0],
                )
            )

            # Extract inheritance
            _extract_inheritance(node, language, file_path, qn, edges)

            # Recurse with class as parent
            for child in node.children:
                _extract_from_tree(
                    child,
                    file_path,
                    language,
                    file_hash,
                    nodes,
                    edges,
                    parent_name=cls_name,
                )
            return

    if node_type in func_types:
        func_name = _extract_name(node, language)
        if func_name:
            is_test = _is_test_function(func_name)
            if parent_name:
                qn = f"{file_path}::{parent_name}.{func_name}"
            else:
                qn = f"{file_path}::{func_name}"

            graph_node = GraphNode(
                kind=NodeKind.TEST if is_test else NodeKind.FUNCTION,
                qualified_name=qn,
                file_path=file_path,
                line_start=node.start_point[0],
                line_end=node.end_point[0],
                language=language,
                parent_name=parent_name,
                is_test=is_test,
                file_hash=file_hash,
            )
            nodes.append(graph_node)

            # CONTAINS edge from parent
            if parent_name:
                parent_qn = f"{file_path}::{parent_name}"
                edges.append(
                    GraphEdge(
                        kind=EdgeKind.CONTAINS,
                        source_qn=parent_qn,
                        target_qn=qn,
                        file_path=file_path,
                        line=node.start_point[0],
                    )
                )

            # Extract calls from function body
            _extract_calls(node, file_path, language, qn, edges)
            return

    if node_type in import_types:
        _extract_import(node, file_path, language, edges)

    # Recurse into children
    for child in node.children:
        _extract_from_tree(
            child,
            file_path,
            language,
            file_hash,
            nodes,
            edges,
            parent_name=parent_name,
        )


# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------


def _extract_name(node: Any, language: str) -> str:
    """Extract the identifier name from a class/function definition node."""
    # Most languages use an 'identifier' or 'name' child
    for child in node.children:
        if child.type in ("identifier", "name", "type_identifier"):
            text = child.text
            return text.decode("utf-8") if isinstance(text, bytes) else text
    return ""


# ---------------------------------------------------------------------------
# Relationship extraction
# ---------------------------------------------------------------------------


def _extract_inheritance(
    node: Any,
    language: str,
    file_path: str,
    class_qn: str,
    edges: list[GraphEdge],
) -> None:
    """Extract INHERITS edges from class definition."""
    for child in node.children:
        if child.type in (
            "argument_list",  # Python: class Foo(Bar)
            "superclass",  # Ruby
            "class_heritage",  # JS/TS
            "superclasses",  # Java
        ):
            for ident in _find_identifiers(child):
                edges.append(
                    GraphEdge(
                        kind=EdgeKind.INHERITS,
                        source_qn=class_qn,
                        target_qn=ident,
                        file_path=file_path,
                        line=child.start_point[0],
                    )
                )


def _extract_calls(
    node: Any,
    file_path: str,
    language: str,
    caller_qn: str,
    edges: list[GraphEdge],
) -> None:
    """Extract CALLS edges from function call expressions."""
    call_types = {"call", "call_expression"}

    if node.type in call_types:
        callee_name = _extract_callee_name(node)
        if callee_name:
            edges.append(
                GraphEdge(
                    kind=EdgeKind.CALLS,
                    source_qn=caller_qn,
                    target_qn=callee_name,
                    file_path=file_path,
                    line=node.start_point[0],
                )
            )

    for child in node.children:
        _extract_calls(child, file_path, language, caller_qn, edges)


def _extract_callee_name(node: Any) -> str:
    """Extract the function name from a call expression."""
    if not node.children:
        return ""
    first = node.children[0]
    if first.type == "identifier":
        text = first.text
        return text.decode("utf-8") if isinstance(text, bytes) else text
    if first.type in ("attribute", "member_expression"):
        text = first.text
        return text.decode("utf-8") if isinstance(text, bytes) else text
    return ""


def _extract_import(
    node: Any,
    file_path: str,
    language: str,
    edges: list[GraphEdge],
) -> None:
    """Extract IMPORTS_FROM edges from import statements."""
    # Collect all dotted names / identifiers from the import
    module_parts: list[str] = []
    for child in node.children:
        if child.type in (
            "dotted_name",
            "identifier",
            "string",
            "scoped_identifier",
            "module",
        ):
            text = child.text
            decoded = text.decode("utf-8") if isinstance(text, bytes) else text
            if decoded not in ("import", "from"):
                module_parts.append(decoded)

    if module_parts:
        target = module_parts[0]
        edges.append(
            GraphEdge(
                kind=EdgeKind.IMPORTS_FROM,
                source_qn=file_path,
                target_qn=target,
                file_path=file_path,
                line=node.start_point[0],
            )
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_identifiers(node: Any) -> list[str]:
    """Recursively find all identifier text in a subtree."""
    results: list[str] = []
    if node.type in ("identifier", "type_identifier"):
        text = node.text
        decoded = text.decode("utf-8") if isinstance(text, bytes) else text
        results.append(decoded)
    for child in node.children:
        results.extend(_find_identifiers(child))
    return results


def _is_test_function(name: str) -> bool:
    """Check if a function name indicates a test."""
    return any(name.startswith(prefix) for prefix in _TEST_PREFIXES)
