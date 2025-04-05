"""Analyze package dependencies and generate an import graph."""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path

from polykit.formatters import color, print_color

# Default packages to analyze
DEFAULT_PACKAGES: list[str] = [
    "dsbin",
    "evremixes",
    "iplooker",
    "polykit",
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

        if not package_found or not package_path:
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
) -> tuple[defaultdict[str, set[str]], list[tuple[str, ...]]]:
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
            cycles.append((*path[cycle_start:], node))
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


def calculate_version_bump_order(
    dependency_graph: dict[str, set[str]], reverse_graph: dict[str, set[str]], packages: list[str]
) -> list[str]:
    """Calculate the optimal order for bumping package versions.

    This identifies the dependency hierarchy from foundational packages to terminal packages,
    ensuring that when you bump a package, you've already bumped all the packages it depends on.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies.
        reverse_graph: Dictionary mapping packages to packages that import them.
        packages: List of all packages to consider.

    Returns:
        List of packages in optimal bumping order (most foundational to most dependent).
    """
    result = []
    remaining = set(packages)

    while remaining:
        # Find packages with no unsatisfied dependencies
        ready = []
        for pkg in remaining:
            deps = dependency_graph.get(pkg, set())
            if all(dep not in remaining for dep in deps):
                ready.append(pkg)

        if not ready:
            # If we have a cycle, just pick the most imported package
            ready = [max(remaining, key=lambda p: len(reverse_graph.get(p, set())))]

        # Sort ready packages by how many other packages import them
        ready.sort(key=lambda p: len(reverse_graph.get(p, set())), reverse=True)

        # Add the highest priority ready package
        next_pkg = ready[0]
        result.append(next_pkg)
        remaining.remove(next_pkg)

    return result


def format_affects_message(
    package: str, reverse_graph: dict[str, set[str]], filter_packages: list[str] | None = None
) -> str:
    """Format a message describing what packages are affected by this one.

    Args:
        package: The package to describe.
        reverse_graph: Dictionary mapping packages to packages that import them.
        filter_packages: Optional list of packages to filter the results to.

    Returns:
        A formatted string describing what this package affects.
    """
    directly_affected = reverse_graph.get(package, set())

    if not directly_affected:
        return "terminal package" + (" (affects nothing)" if not filter_packages else "")

    total = len(directly_affected)
    return f"directly affects {total} package{'s' if total != 1 else ''}"


def print_missing_packages_warning(found: list[str], requested: list[str]) -> None:
    """Print a warning about packages that were requested but not found.

    Args:
        found: List of packages that were found
        requested: List of packages that were requested
    """
    missing = set(requested) - set(found)
    if missing:
        print_color(f"\nWarning: {len(missing)} specified packages were not found:", "red")
        for pkg in sorted(missing):
            print(f"  - {pkg}")


def print_bump_order_header(is_filtered: bool, count: int) -> None:
    """Print the header for the bump order report.

    Args:
        is_filtered: Whether we're showing a filtered list
        count: Number of packages being shown
    """
    if is_filtered:
        print_color("\n=== Optimal Version Bump Order (Filtered) ===\n", "yellow")
        print(f"Bump these {count} packages in this order:")
    else:
        print_color("\n=== Optimal Version Bump Order ===\n", "yellow")
        print("Bump packages in this order to minimize update cascades:")


def print_version_bump_order(
    dependency_graph: dict[str, set[str]],
    reverse_graph: dict[str, set[str]],
    packages: list[str],
    filter_packages: list[str] | None = None,
) -> None:
    """Print the optimal order for bumping package versions.

    Args:
        dependency_graph: Dictionary mapping packages to their dependencies
        reverse_graph: Dictionary mapping packages to packages that import them
        packages: List of all packages analyzed
        filter_packages: Optional list of packages to filter the results to
    """
    # Get the complete bump order
    bump_order = calculate_version_bump_order(dependency_graph, reverse_graph, packages)

    # Filter to specified packages if requested
    if filter_packages:
        filtered_order = [pkg for pkg in bump_order if pkg in filter_packages]
        packages_to_show = filtered_order
        is_filtered = True
    else:
        packages_to_show = bump_order
        is_filtered = False

    # Print the header
    print_bump_order_header(is_filtered, len(packages_to_show))

    # Calculate the width needed for the numbers
    num_width = len(str(len(packages_to_show)))

    # Print each package in order
    for i, package in enumerate(packages_to_show, 1):
        affects_str = format_affects_message(
            package, reverse_graph, filter_packages if is_filtered else None
        )
        print(f"{i:>{num_width}}. {color(package, 'green')} - {affects_str}")

    # Print warning for missing packages
    if is_filtered and filter_packages:
        print_missing_packages_warning(filtered_order, filter_packages)


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


def print_circular_dependencies(cycles: list[tuple[str, ...]]) -> None:
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
        "filter_packages",
        nargs="*",
        help="specific packages to analyze (filters the results)",
    )
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
    parser.add_argument("--stats", action="store_true", help="Show dependency statistics")
    parser.add_argument("--bump-order", action="store_true", help="Show optimal version bump order")
    return parser.parse_args()


def main() -> int:
    """Main entry point for the package dependency analyzer."""
    args = parse_args()

    # Always analyze all packages to build the complete dependency graph
    all_packages = args.packages.copy()

    # Add any filter packages that aren't in the default list
    if args.filter_packages:
        for pkg in args.filter_packages:
            if pkg not in all_packages:
                all_packages.append(pkg)

    # Build dependency graph for all packages
    dependency_graph = build_package_dependency_graph(all_packages, args.search_paths)

    # Analyze dependencies
    reverse_graph, cycles = analyze_package_dependencies(dependency_graph)

    # Print the appropriate report
    if args.bump_order or args.filter_packages:
        print_version_bump_order(
            dependency_graph, reverse_graph, all_packages, args.filter_packages or None
        )
    elif args.stats:
        print_dependency_statistics(dependency_graph, reverse_graph, all_packages)
    else:
        print_color("\n=== Package Dependency Report ===", "yellow")
        print_package_details(dependency_graph, reverse_graph, all_packages)
        print_circular_dependencies(cycles)

    # Exit with error code if cycles found
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main())
