"""Analyze package dependencies and generate an import graph."""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path

from textparse import color, print_color

# Default packages to analyze
DEFAULT_PACKAGES: list[str] = [
    "arguer",
    "devpkg",
    "dsbase",
    "dsbin",
    "enviromancer",
    "evremixes",
    "iplooker",
    "logician",
    "masterclass",
    "pathkeeper",
    "shelper",
    "textparse",
    "timecapsule",
    "walking_man",
]


def find_package_imports(file_path: str) -> list[str]:
    """Extract package-level imports from a Python file.

    Args:
        file_path: Path to the Python file.

    Returns:
        List of imported package names.
    """
    with Path(file_path).open(encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                # Get top-level package name
                package = name.name.split(".")[0]
                imports.add(package)
        elif isinstance(node, ast.ImportFrom) and node.module:
            # Get top-level package name
            package = node.module.split(".")[0]
            imports.add(package)

    return list(imports)


def build_package_dependency_graph(
    packages: list[str], search_paths: list[str]
) -> dict[str, set[str]]:
    """Build a graph of package dependencies.

    Args:
        packages: List of packages to analyze.
        search_paths: List of directories to search for packages.

    Returns:
        Dictionary mapping package names to sets of imported packages.
    """
    graph = defaultdict(set)

    for package_name in packages:
        # Try to find the package
        package_found = False
        package_path = None

        for search_path in search_paths:
            path = Path(search_path) / package_name.replace("_", "-")
            if path.exists() and path.is_dir():
                package_found = True
                package_path = path
                break

            # Try src directory structure
            src_path = Path(search_path) / package_name.replace("_", "-") / "src" / package_name
            if src_path.exists() and src_path.is_dir():
                package_found = True
                package_path = src_path
                break

        if not package_found:
            print_color(f"Package {package_name} not found in search paths", "yellow")
            continue

        # Find all Python files in the package
        for py_file in package_path.glob("**/*.py"):
            if "__pycache__" in str(py_file):
                continue

            # Extract imports from this file
            imports = find_package_imports(str(py_file))

            # Add to the graph
            for imported_package in imports:
                if imported_package in packages and imported_package != package_name:
                    graph[package_name].add(imported_package)

    return graph


def analyze_package_dependencies(
    dependency_graph: dict[str, set[str]],
) -> tuple[defaultdict[str, set[str]], list[tuple[str, str]]]:
    """Analyze package dependencies to find import relationships and cycles.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.

    Returns:
        Tuple of (reverse_graph, cycles).
    """
    # Build reverse graph (what packages import each package)
    reverse_graph = defaultdict(set)
    for package, dependencies in dependency_graph.items():
        for dep in dependencies:
            reverse_graph[dep].add(package)

    # Find cycles
    cycles = []

    def find_cycles_dfs(node: str, path: list[str], visited: set[str]):
        if node in path:
            cycle_start = path.index(node)
            cycles.append(tuple(path[cycle_start:] + [node]))
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for dep in dependency_graph.get(node, []):
            find_cycles_dfs(dep, path, visited)

        path.pop()

    for package in dependency_graph:
        find_cycles_dfs(package, [], set())

    return reverse_graph, cycles


def calculate_impact_scores(
    reverse_graph: dict[str, set[str]], packages: list[str]
) -> dict[str, int]:
    """Calculate how many packages each package affects directly or indirectly."""
    impact_scores = {}

    for package in packages:
        # Use BFS to find all packages affected by this one
        affected = set()
        queue = list(reverse_graph.get(package, set()))
        visited = set(queue)

        while queue:
            current = queue.pop(0)
            affected.add(current)

            for dependent in reverse_graph.get(current, set()):
                if dependent not in visited:
                    visited.add(dependent)
                    queue.append(dependent)

        impact_scores[package] = len(affected)

    return impact_scores


def create_topological_graph(dependency_graph: dict[str, set[str]]) -> dict[str, set[str]]:
    """Create a reversed graph suitable for topological sorting."""
    topo_graph = defaultdict(set)
    for package, deps in dependency_graph.items():
        for dep in deps:
            # Reverse the edges for topological sort
            topo_graph[dep].add(package)
    return topo_graph


def modified_topological_sort(
    topo_graph: dict[str, set[str]], packages: list[str], impact_scores: dict[str, int]
) -> list[str]:
    """Perform topological sort that respects impact scores."""
    result = []
    visited = set()

    def visit(pkg: str) -> None:
        if pkg in visited:
            return
        visited.add(pkg)

        # Visit dependencies
        for dependent in sorted(
            topo_graph.get(pkg, set()), key=lambda x: impact_scores.get(x, 0), reverse=True
        ):
            visit(dependent)

        result.append(pkg)

    # Start with packages sorted by impact score (highest first)
    for package in sorted(packages, key=lambda x: impact_scores.get(x, 0), reverse=True):
        visit(package)

    return result


def calculate_version_bump_order(
    dependency_graph: dict[str, set[str]], reverse_graph: dict[str, set[str]], packages: list[str]
) -> list[str]:
    """Calculate the optimal order for bumping package versions.

    This uses a topological sort with priority given to packages that affect the most other packages
    (directly or indirectly).

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
        reverse_graph: Dictionary mapping packages to packages that import them.
        packages: List of all packages to consider.

    Returns:
        List of packages in optimal bumping order (most affecting to least affecting).
    """
    # Calculate impact scores
    impact_scores = calculate_impact_scores(reverse_graph, packages)

    # Create graph for topological sorting
    topo_graph = create_topological_graph(dependency_graph)

    # Perform modified topological sort
    return modified_topological_sort(topo_graph, packages, impact_scores)

    # Reverse to get the correct order


def print_version_bump_order(
    dependency_graph: dict[str, set[str]], reverse_graph: dict[str, set[str]], packages: list[str]
) -> None:
    """Print the optimal order for bumping package versions.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies
        reverse_graph: Dictionary mapping packages to packages that import them
        packages: List of all packages analyzed
    """
    bump_order = calculate_version_bump_order(dependency_graph, reverse_graph, packages)

    print_color("\n=== Optimal Version Bump Order ===\n", "yellow")
    print("Bump packages in this order to minimize update cascades:")

    for i, package in enumerate(bump_order, 1):
        # Calculate what this affects
        direct_affects = reverse_graph.get(package, set())

        if direct_affects:
            affects_str = f"directly affects {len(direct_affects)} package(s)"
        else:
            affects_str = "terminal package (affects nothing)"

        print(f"{i}. {color(package, 'green')} - {affects_str}")

    print("\nThis order ensures that when you bump a package version:")
    print("1. You bump the most fundamental packages first")
    print("2. Each bump only requires updating packages that haven't been bumped yet")
    print("3. Terminal packages (those that don't affect others) are bumped last")


def print_dependency_report(
    dependency_graph: dict[str, set[str]],
    reverse_graph: dict[str, set[str]],
    cycles: list[tuple[str, str]],
    packages: list[str],
    stats: bool = False,
    bump_order: bool = False,
) -> None:
    """Print a comprehensive dependency report.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
        reverse_graph: Dictionary mapping packages to packages that import them.
        cycles: List of dependency cycles.
        packages: List of all packages analyzed.
        stats: Whether to show statistics or detailed package information.
        bump_order: Whether to show the optimal version bump order.
    """
    if bump_order:
        print_version_bump_order(dependency_graph, reverse_graph, packages)
    elif stats:
        print_dependency_statistics(dependency_graph, reverse_graph, packages)
    else:
        print_color("\n=== Package Dependency Report ===", "yellow")
        print_package_details(dependency_graph, reverse_graph, packages)
        print_circular_dependencies(cycles)


def print_package_details(
    dependency_graph: dict[str, set[str]],
    reverse_graph: dict[str, set[str]],
    packages: list[str],
) -> None:
    """Print detailed dependency information for each package.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
        reverse_graph: Dictionary mapping packages to packages that import them.
        packages: List of all packages analyzed.
    """
    # Print package dependencies
    for package in sorted(packages):
        print_color(f"\n{package}", "green")

        # What this package imports
        deps = sorted(dependency_graph.get(package, []))
        if deps:
            print_color("  Imports:", "cyan")
            for dep in deps:
                print(f"    - {dep}")
        else:
            print_color("  Imports: None", "cyan")

        # What imports this package
        importers = sorted(reverse_graph.get(package, []))
        if importers:
            print_color("  Imported by:", "cyan")
            for importer in importers:
                print(f"    - {importer}")
        else:
            print_color("  Imported by: None", "cyan")


def print_dependency_statistics(
    dependency_graph: dict[str, set[str]],
    reverse_graph: dict[str, set[str]],
    packages: list[str],
) -> None:
    """Print statistics about package dependencies.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
        reverse_graph: Dictionary mapping packages to packages that import them.
        packages: List of all packages analyzed.
    """
    print_color("\n=== Dependency Statistics ===\n", "yellow")

    print_most_imported_packages(reverse_graph)
    print_packages_with_most_dependencies(dependency_graph)
    print_standalone_packages(reverse_graph, packages)
    print_core_packages(reverse_graph)


def print_most_imported_packages(reverse_graph: dict[str, set[str]]) -> None:
    """Print packages that are imported by the most other packages.

    Args:
        reverse_graph: Dictionary mapping packages to packages that import them.
    """
    most_imported = sorted(reverse_graph.items(), key=lambda x: len(x[1]), reverse=True)
    if most_imported:
        print_color("Most imported packages:", "cyan")
        for package, importers in most_imported:
            if importers:
                package = color(package, "green")
                print(f"  - {package}: imported by {len(importers)} packages")


def print_packages_with_most_dependencies(dependency_graph: dict[str, set[str]]) -> None:
    """Print packages that import the most other packages.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
    """
    most_dependencies = sorted(dependency_graph.items(), key=lambda x: len(x[1]), reverse=True)
    if most_dependencies:
        print_color("\nPackages with most dependencies:", "cyan")
        for package, deps in most_dependencies:
            if deps:
                package = color(package, "green")
                print(f"  - {package}: imports {len(deps)} packages")


def print_standalone_packages(reverse_graph: dict[str, set[str]], packages: list[str]) -> None:
    """Print packages that aren't imported by any other package.

    Args:
        reverse_graph: Dictionary mapping packages to packages that import them.
        packages: List of all packages analyzed.
    """
    standalone = [p for p in packages if p not in reverse_graph or not reverse_graph[p]]
    if standalone:
        print_color("\nStandalone packages (not imported by other packages):", "cyan")
        for package in sorted(standalone):
            package = color(package, "green")
            print(f"  - {package}")


def print_core_packages(reverse_graph: dict[str, set[str]]) -> None:
    """Print core packages that are imported by multiple other packages.

    Args:
        reverse_graph: Dictionary mapping packages to packages that import them.
    """
    core_threshold = 2  # Packages imported by at least this many others
    core_packages = [
        p for p, importers in reverse_graph.items() if len(importers) >= core_threshold
    ]
    if core_packages:
        print_color(f"\nCore packages (imported by {core_threshold}+ packages):", "cyan")
        for package in sorted(core_packages):
            importers = reverse_graph[package]
            package = color(package, "green")
            print(f"  - {package}: imported by {', '.join(sorted(importers))}")


def print_circular_dependencies(cycles: list[tuple[str, str]]) -> None:
    """Print any circular dependencies found between packages.

    Args:
        cycles: List of dependency cycles.
    """
    if cycles:
        print_color("\n=== Circular Dependencies ===\n", "red")
        for i, cycle in enumerate(cycles, 1):
            print(f"Cycle {i}: {' -> '.join(cycle)}")
    else:
        print_color("\nNo circular dependencies found! 🎉", "green")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze package dependencies")
    parser.add_argument(
        "--packages",
        nargs="+",
        default=DEFAULT_PACKAGES,
        help="packages to analyze (defaults to predefined list)",
    )
    parser.add_argument(
        "--search-paths",
        nargs="+",
        default=[Path.cwd(), Path("~/Developer").expanduser()],
        help="paths to search for packages",
    )
    parser.add_argument("--stats", action="store_true", help="show dependency statistics")
    parser.add_argument("--bump-order", action="store_true", help="show optimal version bump order")
    return parser.parse_args()


def main() -> int:
    """Main entry point for the package dependency analyzer."""
    args = parse_args()

    # Build dependency graph
    dependency_graph = build_package_dependency_graph(args.packages, args.search_paths)

    # Analyze dependencies
    reverse_graph, cycles = analyze_package_dependencies(dependency_graph)

    # Print report
    print_dependency_report(
        dependency_graph, reverse_graph, cycles, args.packages, args.stats, args.bump_order
    )

    # Exit with error code if cycles found
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main())
