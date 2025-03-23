#!/usr/bin/env python

"""Check for circular imports in a Python project."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Literal

ColorName = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]


def color(text: str, color_name: ColorName | None = None) -> str:
    """Use termcolor to return a string in the specified color if termcolor is available."""
    try:
        from termcolor import colored
    except ImportError:
        return text

    return colored(text, color_name)


def print_colored(text: str, color_name: ColorName | None = None) -> None:
    """Use termcolor to print text in the specified color if termcolor is available."""
    try:
        from termcolor import colored
    except ImportError:
        print(text)
        return

    print(colored(text, color_name))


def find_imports(file_path: str) -> list[str]:
    """Extract all imports from a Python file."""
    with Path(file_path).open(encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((name.name, node.lineno) for name in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))

    return imports


def build_import_graph(root_dir: str) -> dict[str, set[str]]:
    """Build a graph of imports between modules.

    Returns:
        Dictionary mapping module names to sets of imported modules.
    """
    graph = {}
    root_path = Path(root_dir)

    for path in root_path.glob("**/*.py"):
        rel_path = path.relative_to(root_path)
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")

        imports_with_lines = find_imports(str(path))

        if module_name not in graph:
            graph[module_name] = []

        for imported_module, line_number in imports_with_lines:
            graph[module_name].append((imported_module, str(path), line_number))

    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find cycles in the import graph using DFS."""
    cycles = []
    visited = set()
    path = []
    path_info = []

    def dfs(node: str):
        if node in path:
            cycle_start_idx = path.index(node)
            cycle = path[cycle_start_idx:] + [node]
            cycle_info = path_info[cycle_start_idx:] + [path_info[cycle_start_idx]]
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

        path.pop()

    for node in graph:
        dfs(node)

    return cycles


def print_self_import_cycle(cycle: list[str]) -> None:
    """Print a self-import cycle."""
    module, (file_path, line_number) = cycle[0]
    module_name = color(module, "red")
    location = color(f"{file_path}:{line_number}", "yellow")
    print(f"- {module_name} appears to import itself in {location}")


def print_circular_dependency_cycle(cycle: list[str]) -> None:
    """Print a circular dependency cycle."""
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
    """Analyze a Python project for circular imports."""
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    graph = build_import_graph(project_root)
    cycles = find_cycles(graph)

    if cycles:
        print_colored("Circular imports detected:\n", "yellow")
        for cycle in cycles:
            if len(cycle) == 2 and cycle[0][0] == cycle[1][0]:  # Self-import case
                print_self_import_cycle(cycle)
            else:
                print("\nCircular dependency:")
                print_circular_dependency_cycle(cycle)


if __name__ == "__main__":
    main()
