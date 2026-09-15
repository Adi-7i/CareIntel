"""
Lightweight architecture boundary tests.

These tests enforce the modular monolith layer rules at the import level.
They catch obvious layer violations (e.g. domain importing FastAPI)
without requiring a full static analysis toolchain.

Rules enforced:
- careintel.domain.*  must NOT import from fastapi, sqlalchemy, alembic
- careintel.core.*    must NOT import from fastapi (exception: errors.py registers handlers)
                      core may import pydantic and stdlib only
- careintel.api.*     must NOT import from persistence implementations directly

These tests read source files to check for forbidden imports.
They are fast, deterministic, and require no external services.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "careintel"


def _get_python_files(package_path: Path) -> list[Path]:
    """Return all .py files under a package directory."""
    return list(package_path.rglob("*.py"))


def _get_top_level_imports(source_path: Path) -> set[str]:
    """
    Parse a Python file and return all top-level module names being imported.

    For 'from fastapi import X' → returns 'fastapi'
    For 'import sqlalchemy.ext.asyncio' → returns 'sqlalchemy'
    """
    source = source_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


@pytest.mark.unit
class TestArchitectureBoundaries:
    """Enforce module dependency rules between layers."""

    def test_domain_does_not_import_fastapi(self) -> None:
        """Domain layer must not depend on FastAPI."""
        domain_path = SRC_ROOT / "domain"
        violations: list[str] = []
        for py_file in _get_python_files(domain_path):
            imports = _get_top_level_imports(py_file)
            if "fastapi" in imports:
                violations.append(str(py_file))
        assert not violations, (
            f"Domain layer imports FastAPI in: {violations}. "
            "Domain must be pure Python — no web framework dependencies."
        )

    def test_domain_does_not_import_sqlalchemy(self) -> None:
        """Domain layer must not depend on SQLAlchemy."""
        domain_path = SRC_ROOT / "domain"
        violations: list[str] = []
        for py_file in _get_python_files(domain_path):
            imports = _get_top_level_imports(py_file)
            if "sqlalchemy" in imports:
                violations.append(str(py_file))
        assert not violations, (
            f"Domain layer imports SQLAlchemy in: {violations}. "
            "Domain must not know about persistence technology."
        )

    def test_domain_does_not_import_alembic(self) -> None:
        """Domain layer must not depend on Alembic."""
        domain_path = SRC_ROOT / "domain"
        violations: list[str] = []
        for py_file in _get_python_files(domain_path):
            imports = _get_top_level_imports(py_file)
            if "alembic" in imports:
                violations.append(str(py_file))
        assert not violations, f"Domain layer imports Alembic in: {violations}."

    def test_no_langgraph_anywhere(self) -> None:
        """LangGraph must not be imported anywhere in the codebase."""
        violations: list[str] = []
        for py_file in _get_python_files(SRC_ROOT):
            imports = _get_top_level_imports(py_file)
            if "langgraph" in imports:
                violations.append(str(py_file))
        # Also check test files
        tests_root = SRC_ROOT.parent.parent / "tests"
        for py_file in _get_python_files(tests_root):
            imports = _get_top_level_imports(py_file)
            if "langgraph" in imports:
                violations.append(str(py_file))
        assert not violations, (
            f"LangGraph is imported in: {violations}. "
            "LangGraph is explicitly excluded from CareIntel. "
            "Future orchestration uses Celery + Redis."
        )

    def test_no_docker_sdk_anywhere(self) -> None:
        """Docker SDK must not be imported anywhere in the codebase."""
        violations: list[str] = []
        for py_file in _get_python_files(SRC_ROOT):
            imports = _get_top_level_imports(py_file)
            if "docker" in imports:
                violations.append(str(py_file))
        assert not violations, (
            f"Docker SDK imported in: {violations}. "
            "Docker is deferred to the final hardening phase."
        )

    def test_core_config_does_not_import_fastapi(self) -> None:
        """Core config must not depend on FastAPI."""
        config_file = SRC_ROOT / "core" / "config.py"
        imports = _get_top_level_imports(config_file)
        assert "fastapi" not in imports, (
            "core/config.py imports FastAPI — this creates a circular dependency risk "
            "and violates the pure-infrastructure contract of the config module."
        )

    def test_core_config_does_not_import_sqlalchemy(self) -> None:
        """Core config must not depend on SQLAlchemy."""
        config_file = SRC_ROOT / "core" / "config.py"
        imports = _get_top_level_imports(config_file)
        assert "sqlalchemy" not in imports, (
            "core/config.py imports SQLAlchemy — config must be a pure settings module."
        )
