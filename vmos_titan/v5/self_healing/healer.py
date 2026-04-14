"""
Titan Apex v5.0 — Self-Healing Codebase Engine.

Performs AST-based analysis, dependency resolution, duplicate detection,
and auto-repair of import failures across the repository.
"""
from __future__ import annotations

import os
import ast
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

log = logging.getLogger("self_healing")


class CodebaseHealer:
    """
    Autonomously scans the vmos-titan-unified repository to identify
    and resolve structural failures: missing imports, duplicate logic,
    broken references, and stale modules.
    """

    KNOWN_INTERNAL_PREFIXES = {
        "vmos_titan", "genesis", "autonomous", "escape",
        "injection", "scanning", "neighbor", "cloning",
    }

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.scan_results: Dict[str, object] = {}

    # ------------------------------------------------------------------
    # Import analysis
    # ------------------------------------------------------------------

    def find_missing_imports(self, exclude_dirs: Set[str] = None) -> Dict[str, List[str]]:
        """Scan all .py files and detect unresolvable imports."""
        exclude = exclude_dirs or {".venv", "__pycache__", "node_modules", ".git"}
        missing: Dict[str, List[str]] = defaultdict(list)

        for py_file in self._iter_py_files(exclude):
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError) as e:
                log.warning("Parse error in %s: %s", py_file, e)
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_resolve(alias.name, py_file):
                            missing[alias.name].append(str(py_file.relative_to(self.repo_path)))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if not self._can_resolve(node.module, py_file):
                        missing[node.module].append(str(py_file.relative_to(self.repo_path)))

        self.scan_results["missing_imports"] = dict(missing)
        return dict(missing)

    def _can_resolve(self, module_name: str, source_file: Path) -> bool:
        """Check if a module can be resolved — handles internal + external."""
        top = module_name.split(".")[0]
        # Known internal — check if corresponding path exists
        if top in self.KNOWN_INTERNAL_PREFIXES:
            parts = module_name.replace(".", "/")
            pkg = self.repo_path / parts
            return (pkg.exists() or
                    (pkg.with_suffix(".py")).exists() or
                    (pkg / "__init__.py").exists())
        # External — try import
        try:
            __import__(top)
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def find_duplicate_modules(self, pattern: str = "genesis*.py") -> Dict[str, List[str]]:
        """Find scripts matching pattern across the repo that may contain duplicate logic."""
        matches: Dict[str, List[str]] = defaultdict(list)
        for py_file in self.repo_path.rglob(pattern):
            if any(p in str(py_file) for p in (".venv", "__pycache__")):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                funcs = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                for fn in funcs:
                    matches[fn].append(str(py_file.relative_to(self.repo_path)))
            except Exception:
                continue

        duplicates = {fn: files for fn, files in matches.items() if len(files) > 1}
        self.scan_results["duplicate_functions"] = duplicates
        return duplicates

    # ------------------------------------------------------------------
    # Auto-repair: generate stubs for missing internal modules
    # ------------------------------------------------------------------

    def auto_repair_missing_modules(self, dry_run: bool = True) -> List[Dict[str, str]]:
        """Generate stub modules for missing internal imports."""
        missing = self.scan_results.get("missing_imports") or self.find_missing_imports()
        repairs: List[Dict[str, str]] = []
        for module_name in missing:
            top = module_name.split(".")[0]
            if top not in self.KNOWN_INTERNAL_PREFIXES:
                continue
            parts = module_name.replace(".", "/")
            target_pkg = self.repo_path / parts
            target_file = target_pkg.with_suffix(".py")

            if target_pkg.exists() or target_file.exists():
                continue

            # Decide: create package or module
            if "." in module_name and not target_file.parent.exists():
                action = "create_package"
                create_path = target_pkg / "__init__.py"
            else:
                action = "create_module"
                create_path = target_file

            if not dry_run:
                create_path.parent.mkdir(parents=True, exist_ok=True)
                create_path.write_text(
                    f'"""Auto-generated stub for {module_name}"""\n',
                    encoding="utf-8",
                )
                log.info("Repaired: created %s", create_path)

            repairs.append({
                "module": module_name,
                "action": action,
                "path": str(create_path.relative_to(self.repo_path)),
                "applied": not dry_run,
            })

        self.scan_results["repairs"] = repairs
        return repairs

    # ------------------------------------------------------------------
    # Centralize duplicate scripts
    # ------------------------------------------------------------------

    def centralize_duplicate_scripts(self, pattern: str,
                                      central_location: str,
                                      dry_run: bool = True) -> List[Dict[str, str]]:
        """Find scripts matching pattern and consolidate them."""
        duplicates = list(self.repo_path.rglob(pattern))
        duplicates = [d for d in duplicates if ".venv" not in str(d)]
        actions: List[Dict[str, str]] = []
        if len(duplicates) > 1:
            central = self.repo_path / central_location
            for dup in duplicates:
                rel = str(dup.relative_to(self.repo_path))
                if rel == central_location:
                    continue
                action = {
                    "source": rel,
                    "target": central_location,
                    "action": "consolidate",
                    "applied": False,
                }
                if not dry_run:
                    central.parent.mkdir(parents=True, exist_ok=True)
                    if not central.exists():
                        shutil.copy2(dup, central)
                    action["applied"] = True
                actions.append(action)
        return actions

    # ------------------------------------------------------------------
    # Full health report
    # ------------------------------------------------------------------

    def full_scan(self) -> Dict[str, object]:
        """Run all scanners and return comprehensive health report."""
        self.find_missing_imports()
        self.find_duplicate_modules()
        repairs = self.auto_repair_missing_modules(dry_run=True)
        return {
            "missing_imports": self.scan_results.get("missing_imports", {}),
            "duplicate_functions": self.scan_results.get("duplicate_functions", {}),
            "recommended_repairs": repairs,
            "repo_path": str(self.repo_path),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_py_files(self, exclude: Set[str]) -> List[Path]:
        result = []
        for py_file in self.repo_path.rglob("*.py"):
            if any(part in py_file.parts for part in exclude):
                continue
            result.append(py_file)
        return result
