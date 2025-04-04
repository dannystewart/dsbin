#!/usr/bin/env python3

"""Analyze dependencies and imports across scripts to help separate concerns."""

from __future__ import annotations

import ast
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from polykit import polykit_setup

polykit_setup()


def run_tool(cmd: list, cwd: str | None = None) -> tuple[str, str]:
    """Run a uv tool and return its output.

    Raises:
        FileNotFoundError: If the tool is not found in PATH.
    """
    uvx_path = shutil.which("uvx")
    if not uvx_path:
        msg = "uvx not found in PATH"
        raise FileNotFoundError(msg)
    uv_cmd = [uvx_path, *cmd]
    result = subprocess.run(uv_cmd, capture_output=True, text=True, cwd=cwd, check=False)
    return result.stdout, result.stderr


def get_imports(path: Path, exclude_dirs: list[str] | None = None) -> dict:
    """Get all imports from Python files in the given path, excluding specified directories."""
    imports_by_file = defaultdict(set)
    exclude_dirs = exclude_dirs or []

    for file in path.rglob("*.py"):
        if any(excluded_dir in file.parts for excluded_dir in exclude_dirs):
            continue

        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError:
            print(f"Syntax error in {file}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports_by_file[file.relative_to(path)].add(name.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports_by_file[file.relative_to(path)].add(node.module.split(".")[0])

    return imports_by_file


def check_unused_imports() -> str:
    """Check for unused imports using ruff."""
    print("\nChecking for unused imports...")
    stdout, _ = run_tool(["ruff", "check", "--select", "F401,I", "."])
    return stdout


def analyze_imports(path: Path, name: str, exclude_dirs: list[str]) -> dict:
    """Analyze imports for a given path, excluding specified directories."""
    print(f"\nAnalyzing {name} imports...")
    return get_imports(path, exclude_dirs)


def get_installed_packages() -> set:
    """Get a set of installed packages."""
    stdout, _ = run_tool(["pipdeptree"])
    installed_packages = set()
    for line in stdout.splitlines():
        if line.strip() and not line.startswith(" "):
            pkg = line.split("==")[0].strip()
            installed_packages.add(pkg.lower())
    return installed_packages


def print_imports_by_file(imports_by_file: dict, title: str) -> None:
    """Print imports grouped by file."""
    print(f"\n{title} imports by file:")
    for file, imports in imports_by_file.items():
        print(f"\n{file}:")
        for imp in sorted(imports):
            print(f"  - {imp}")


def categorize_imports(dsbin_imports: dict, scripts_imports: dict) -> tuple[set, set, set]:
    """Categorize imports into dsbin-only, scripts-only, and shared."""
    all_imports = set()
    for imports in dsbin_imports.values():
        all_imports.update(imports)
    for imports in scripts_imports.values():
        all_imports.update(imports)

    dsbin_only = set()
    scripts_only = set()
    shared = set()

    for imp in all_imports:
        in_dsbin = any(imp in imports for imports in dsbin_imports.values())
        in_scripts = any(imp in imports for imports in scripts_imports.values())

        if in_dsbin and in_scripts:
            shared.add(imp)
        elif in_dsbin:
            dsbin_only.add(imp)
        else:
            scripts_only.add(imp)

    return dsbin_only, scripts_only, shared


def print_categorized_imports(
    dsbin_only: set, scripts_only: set, shared: set, installed_packages: set
) -> None:
    """Print categorized imports."""
    print("\nPotential package assignments:")
    print("-" * 30)

    print("\ndsbin-specific imports:")
    for imp in sorted(dsbin_only):
        if imp.lower() in installed_packages:
            print(f"  - {imp}")

    print("\nScripts-specific imports:")
    for imp in sorted(scripts_only):
        if imp.lower() in installed_packages:
            print(f"  - {imp}")

    print("\nShared imports:")
    for imp in sorted(shared):
        if imp.lower() in installed_packages:
            print(f"  - {imp}")


def analyze_dependencies() -> None:
    """Run dependency analysis using uv tools."""
    print("Running dependency analysis...")

    unused_imports = check_unused_imports()
    print(unused_imports)

    exclude_dirs = [".venv", "tests", "build", "dist"]
    dsbin_imports = analyze_imports(Path("dsbin"), "dsbin", exclude_dirs)
    scripts_imports = analyze_imports(Path(), "scripts", exclude_dirs)

    dsbin_imports = analyze_imports(Path("dsbin"), "dsbin", exclude_dirs)
    scripts_imports = analyze_imports(Path(), "scripts", exclude_dirs)

    installed_packages = get_installed_packages()

    print("\nDependency Analysis Report")
    print("=" * 50)

    print_imports_by_file(dsbin_imports, "dsbin")
    print_imports_by_file(scripts_imports, "scripts")

    dsbin_only, scripts_only, shared = categorize_imports(dsbin_imports, scripts_imports)
    print_categorized_imports(dsbin_only, scripts_only, shared, installed_packages)


def main() -> None:
    """Analyze dependencies and imports across dsbin and scripts."""
    analyze_dependencies()


if __name__ == "__main__":
    main()
