#!/usr/bin/env python

"""Check for circular imports in a Python project."""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path

from polykit.formatters import color, print_color


def find_imports(file_path: str) -> list[tuple[str, int]]:
    """Extract all imports from a Python file with line numbers.

    Returns:
        List of tuples (module_name, line_number).
    """
    with Path(file_path).open(encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((name.name, node.lineno) for name in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))

    return imports


def build_import_graph(
    root_dir: str, exclude_stdlib: bool = False
) -> dict[str, list[tuple[str, str, int]]]:
    """Build a graph of imports between modules with file paths and line numbers.

    Args:
        root_dir: The root directory of the project.
        exclude_stdlib: Whether to exclude standard library modules.

    Returns:
        Dictionary mapping module names to lists of (imported_module, file_path, line_number)
    """
    graph = {}
    root_path = Path(root_dir)

    # Get list of stdlib modules if excluding them
    stdlib_modules = set()
    if exclude_stdlib:
        import pkgutil

        stdlib_modules = {module.name for module in pkgutil.iter_modules()}

    for path in root_path.glob("**/*.py"):
        rel_path = path.relative_to(root_path)
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")

        imports_with_lines = find_imports(str(path))

        if module_name not in graph:
            graph[module_name] = []

        for imported_module, line_number in imports_with_lines:
            if exclude_stdlib and imported_module in stdlib_modules:
                continue
            graph[module_name].append((imported_module, str(path), line_number))

    return graph


def find_cycles(
    graph: dict[str, list[tuple[str, str, int]]],
) -> list[list[tuple[str, tuple[str, int]]]]:
    """Find cycles in the import graph using DFS with file paths and line numbers.

    Args:
        graph: Import graph with file paths and line numbers.

    Returns:
        List of cycles found in the graph with context.
    """
    cycles = []
    visited = set()
    path = []
    path_info = []

    def dfs(node: str):
        if node in path:
            cycle_start_idx = path.index(node)
            cycle = [*path[cycle_start_idx:], node]
            cycle_info = [
                *path_info[cycle_start_idx:],
                path_info[cycle_start_idx] if cycle_start_idx < len(path_info) else None,
            ]
            cycles.append(list(zip(cycle, cycle_info, strict=False)))
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for imported_module, file_path, line_number in graph.get(node, []):
            if imported_module == node:  # Self-import
                cycles.append([(node, (file_path, line_number)), (node, (file_path, line_number))])
            elif imported_module in graph:  # Only consider modules we know about
                path_info.append((file_path, line_number))
                dfs(imported_module)
                if path_info:  # Ensure path_info is not empty before popping
                    path_info.pop()

        if path:  # Ensure path is not empty before popping
            path.pop()

    for graph_node in graph:
        path = []
        path_info = []
        dfs(graph_node)

    return cycles


def print_self_import_cycle(cycle: list[tuple[str, tuple[str, int]]]) -> None:
    """Print a self-import cycle."""
    module, (file_path, line_number) = cycle[0]
    module_name = color(module, "red")
    location = color(f"{file_path}:{line_number}", "yellow")
    print(f"- {module_name} appears to import itself in {location}")


def print_circular_dependency_cycle(cycle: list[tuple[str, tuple[str, int]]]) -> None:
    """Print a circular dependency cycle."""
    print("\nCircular dependency:")
    for i, (module, (file_path, line_number)) in enumerate(cycle):
        mod_name = color(module, "red")
        location = color(f"{file_path}:{line_number}", "yellow")
        if i < len(cycle) - 1:
            next_module = cycle[i + 1][0]
            print(f"  {mod_name} (in {location}) imports {color(next_module, 'red')}")
        else:
            first_module = cycle[0][0]
            print(f"  {mod_name} (in {location}) imports {color(first_module, 'red')}")


def main() -> None:
    """Main entry point for the import checker tool."""
    parser = argparse.ArgumentParser(description="Check for circular imports in a Python project")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the Python project directory (default: current directory)",
    )
    parser.add_argument(
        "--exclude-stdlib",
        action="store_true",
        help="Exclude standard library modules from analysis",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text", help="Output format (default: text)"
    )

    args = parser.parse_args()

    project_root = args.path
    graph = build_import_graph(project_root, exclude_stdlib=args.exclude_stdlib)
    cycles = find_cycles(graph)

    if args.output == "json":
        import json

        # Convert to JSON-serializable format
        json_cycles = []
        for cycle in cycles:
            json_cycle = []
            for module, (file_path, line_number) in cycle:
                json_cycle.append({"module": module, "file": file_path, "line": line_number})
            json_cycles.append(json_cycle)

        print(json.dumps({"cycles": json_cycles}, indent=2))
        return

    # Default text output
    self_imports = 0
    circular_deps = 0

    if cycles:
        print_color("Circular imports detected:\n", "yellow")
        for cycle in cycles:
            if len(cycle) == 2 and cycle[0][0] == cycle[1][0]:  # Self-import case
                print_self_import_cycle(cycle)
                self_imports += 1
            else:
                print_circular_dependency_cycle(cycle)
                circular_deps += 1

        # Print summary
        summary = []
        if self_imports > 0:
            summary.append(f"{self_imports} self-import{'s' if self_imports != 1 else ''}")
        if circular_deps > 0:
            summary.append(
                f"{circular_deps} circular dependenc{'ies' if circular_deps != 1 else 'y'}"
            )

        if summary:
            print_color(f"\nFound {' and '.join(summary)}.", "yellow")
        import sys

        sys.exit(1)
    else:
        print_color("No circular imports found! 🎉", "green")


if __name__ == "__main__":
    main()
