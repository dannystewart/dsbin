"""Analyze release impact based on changes internally or to a utility library."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from dsbase import ArgParser, EnvManager, LocalLogger
from dsbase.text import color_print
from dsbase.text.diff import show_diff

if TYPE_CHECKING:
    import argparse
    from logging import Logger


class ImpactAnalyzer:
    """Analyzes the impact of changes in dsbase on dependent packages."""

    DSBASE_PATH: ClassVar[Path] = Path("src/dsbase")
    PACKAGES_PATH: ClassVar[Path] = Path("packages")

    def __init__(self, packages: list[str], args: argparse.Namespace, logger: Logger) -> None:
        self.packages = packages
        self.logger = logger
        self.base_commit = args.base
        self.verbose = args.verbose

        # Initialize empty lists for changes
        self.changed_files: list[str] = []
        self.changed_modules: set[str] = set()
        self.impacted_packages: dict[str, set[str]] = {}
        self.package_changes: dict[str, dict[str, list[str] | str | None]] = {}

        # Cache for imports to avoid rescanning
        self._imports_cache: dict[str, dict[str, set[str]]] = {}

    def analyze(self) -> None:
        """Run the analysis and display results."""
        # Analyze dsbase changes and their impact
        self.analyze_dsbase_changes()

        # Analyze package changes since last release
        self.analyze_package_changes()
        self.display_package_changes()

        # Determine which packages need releases
        self.display_release_recommendations()

    def analyze_dsbase_changes(self) -> None:
        """Analyze changes in dsbase and their impact on dependent packages."""
        # Get changed files in dsbase
        self.changed_files = self.find_changed_files(self.base_commit)

        if not self.changed_files:
            self.logger.info("✓ No Python files changed in dsbase.")
            return

        color_print("\n=== Current Changes Detected ===\n", "yellow")

        color_print("Changed files in dsbase:", "blue")
        for file in self.changed_files:
            print(f"  {file}")

        # Convert to module paths
        self.changed_modules = self.get_changed_modules(self.changed_files)
        color_print("\nChanged modules:", "blue")
        for module in sorted(self.changed_modules):
            print(f"  {module}")

        # Analyze impact
        self.impacted_packages = self.analyze_impact(self.changed_modules)

        if self.impacted_packages:
            color_print("\n=== Current Impacted Packages ===", "yellow")
            for package, imports in self.impacted_packages.items():
                color_print(f"\n{package} (uses {len(imports)} affected modules):", "cyan")
                for import_path in sorted(imports):
                    print(f"  - {import_path}")
        else:
            self.logger.info("No packages are directly impacted by these changes.")

    def display_package_changes(self) -> None:
        """Display changes in packages since their last release."""
        color_print("\n=== Package Changes Since Last Release ===", "yellow")

        for package, info in self.package_changes.items():
            if info["latest_tag"]:
                if info["changes"]:
                    color_print(f"\n{package} (last release: {info['latest_tag']}):", "cyan")
                    for file in info["changes"]:
                        print(f"  - {file}")
            else:
                color_print(f"\n{package}:", "red")
                print("  No release tags found")

    def display_release_recommendations(self) -> None:
        """Display recommendations for packages that need new releases."""
        color_print("\nPackages requiring new releases:", "yellow")
        release_packages = set()

        # Add packages impacted by dsbase changes
        if self.impacted_packages:
            release_packages.update(self.impacted_packages)

        # Add packages with their own changes
        for package, info in self.package_changes.items():
            if info["needs_release"]:
                release_packages.add(package)

        if release_packages:
            for package in sorted(release_packages):
                color_print(f"  - {package}", "green")
        elif self.changed_files:
            color_print("  None (but you should still release a new version of dsbase)", "yellow")
        else:
            color_print("  None", "green")

    def find_imports_in_file(self, file_path: Path) -> set[str]:
        """Find all imports from dsbase in a given file."""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            self.logger.warning("Couldn't read %s: %s", file_path, str(e))
            return set()

        imports = set()

        try:  # Parse the Python file
            tree = ast.parse(content)

            # Look for imports
            for node in ast.walk(tree):
                # Regular imports: import dsbase.xyz
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.startswith("dsbase."):
                            imports.add(name.name)

                # From imports: from dsbase import xyz
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("dsbase"):
                        imports.update(f"{node.module}.{name.name}" for name in node.names)
        except SyntaxError:
            self.logger.warning("Couldn't parse %s as a valid Python file.", file_path)

        return imports

    def find_latest_tag_for_package(self, package_name: str) -> str | None:
        """Return the most recent tag for a package in the Git history, or None if not found."""
        try:
            # Get all tags matching the package prefix, sorted by version (most recent first)
            cmd = ["git", "tag", "--sort=-v:refname", "-l", f"{package_name}-v*"]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            tags = result.stdout.strip().splitlines()

            self.logger.debug(
                "Found %d tags for package %s: %s", len(tags), package_name, tags or "None"
            )

            if not tags:
                return None

            latest_tag = tags[0]
            self.logger.debug("Latest tag for %s: %s", package_name, latest_tag)
            return latest_tag
        except subprocess.CalledProcessError as e:
            self.logger.error("Error finding tags for %s: %s", package_name, str(e))
            return None

    def get_changes_since_tag(self, package_name: str, tag: str) -> list[str]:
        """Get files changed in a package since the specified tag.

        Args:
            package_name: The name of the package to check.
            tag: The Git tag to compare against.

        Returns:
            A list of changed file paths.
        """
        package_path = f"{self.PACKAGES_PATH}/{package_name}"

        try:
            cmd = ["git", "diff", "--name-only", f"{tag}..HEAD", "--", package_path]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = result.stdout.strip().splitlines()

            # Filter for Python files only
            python_files = [f for f in changed_files if f.endswith(".py")]
            self.logger.debug(
                "Found %d Python files changed in %s since %s", len(python_files), package_name, tag
            )
            return python_files
        except subprocess.CalledProcessError as e:
            self.logger.error(
                "Error checking changes for %s since %s: %s", package_name, tag, str(e)
            )
            return []

    def analyze_package_changes(self) -> None:
        """Analyze changes to packages since their last release tag."""
        results = {}

        try:  # Check for tags
            cmd = ["git", "tag"]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            all_tags = result.stdout.strip().splitlines()
            self.logger.debug(
                "Found %d total tags in repository: %s",
                len(all_tags),
                all_tags[:5] if len(all_tags) > 5 else all_tags,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error("Error listing tags: %s", str(e))

        for package in self.packages:
            if latest_tag := self.find_latest_tag_for_package(package):
                changes = self.get_changes_since_tag(package, latest_tag)
                results[package] = {
                    "latest_tag": latest_tag,
                    "changes": changes,
                    "needs_release": len(changes) > 0,
                }
            else:
                results[package] = {"latest_tag": None, "changes": [], "needs_release": False}

        self.package_changes = results

    def scan_package_for_imports(self, package_name: str) -> dict[str, set[str]]:
        """Scan a package for all dsbase imports.

        Returns:
            A dictionary mapping file paths to sets of imports.
        """
        # Use cached results if available
        if package_name in self._imports_cache:
            return self._imports_cache[package_name]

        package_dir = self.PACKAGES_PATH / package_name
        imports_by_file = {}

        if self.verbose:
            color_print(f"Scanning {package_name} for imports...", "blue")

        # Find all Python files
        for py_file in package_dir.glob("**/*.py"):
            if imports := self.find_imports_in_file(py_file):
                imports_by_file[str(py_file)] = imports
                if self.verbose:
                    color_print(
                        f"  Found {len(imports)} imports in {py_file.relative_to(package_dir)}",
                        "cyan",
                    )

        # Cache the results
        self._imports_cache[package_name] = imports_by_file
        return imports_by_file

    def find_changed_files(
        self, base_commit: str = "HEAD", include_staged: bool = True
    ) -> list[str]:
        """Find files changed in the current working directory compared to base_commit."""
        try:
            changed_files = []

            self._analyze_git_diff(
                "--name-only", base_commit, "Found %d unstaged changes: %s", changed_files
            )
            # Get staged changes if requested
            if include_staged:
                self._analyze_git_diff(
                    "--cached", "--name-only", "Found %d staged changes: %s", changed_files
                )
            filtered = [
                f
                for f in changed_files
                if f.endswith(".py") and f.startswith(self.DSBASE_PATH.as_posix())
            ]
            self.logger.debug(
                "After filtering for Python files in %s: %s", self.DSBASE_PATH.as_posix(), filtered
            )
            return filtered
        except subprocess.CalledProcessError as e:
            self.logger.error("Error running git diff: %s", str(e))
            return []

    def _analyze_git_diff(
        self, base_commit: str, target_commit: str, log_message: str, changed_files: list[str]
    ):
        cmd = ["git", "diff", base_commit, target_commit]
        self.logger.debug("Running: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        staged = result.stdout.splitlines()
        self.logger.debug(log_message, len(staged), staged)
        changed_files.extend(staged)

    def get_changed_modules(self, changed_files: list[str]) -> set[str]:
        """Convert file paths to module paths."""
        modules = set()

        for file_path in changed_files:
            # Convert src/dsbase/xyz/abc.py to dsbase.xyz.abc
            if file_path.endswith(".py"):
                rel_path = file_path.replace("src/", "", 1).replace("/", ".").replace(".py", "")
                modules.add(rel_path)

                # Also add the parent module
                parts = rel_path.split(".")
                if len(parts) > 1:
                    parent = ".".join(parts[:-1])
                    modules.add(parent)

        return modules

    def analyze_impact(self, changed_modules: set[str]) -> dict[str, set[str]]:
        """Analyze which packages are impacted by changes to specific modules."""
        impacted_packages = {}

        for package_name in self.packages:
            imports_by_file = self.scan_package_for_imports(package_name)
            package_imports = set()

            # Check if any of the changed modules are imported
            for imports in imports_by_file.values():
                for import_path in imports:
                    for changed_module in changed_modules:
                        # Check if the import matches or is a submodule of the changed module
                        if import_path == changed_module or import_path.startswith(
                            f"{changed_module}."
                        ):
                            package_imports.add(import_path)

            if package_imports:
                impacted_packages[package_name] = package_imports

        return impacted_packages

    def show_package_diffs(self, package_name: str) -> None:
        """Show detailed diffs for a specific package since its last release.

        Args:
            package_name: Name of the package to show diffs for
        """
        # Validate package and get latest tag
        latest_tag = self._validate_package_for_diff(package_name)
        if not latest_tag:
            return

        # Get changed files
        changed_files = self.get_changes_since_tag(package_name, latest_tag)

        if not changed_files:
            self.logger.info("No changes detected in %s since %s.", package_name, latest_tag)
            return

        color_print(f"\n=== Detailed Changes in {package_name} since {latest_tag} ===", "yellow")

        # Track new files separately
        new_files = [
            file_path
            for file_path in changed_files
            if self._process_file_diff(file_path, latest_tag)
        ]

        # Display new files separately
        self._display_new_files(new_files)

    def _validate_package_for_diff(self, package_name: str) -> str | None:
        """Validate the package exists and has release tags.

        Args:
            package_name: Name of the package to validate

        Returns:
            The latest tag if found, None otherwise
        """
        if package_name not in self.packages:
            self.logger.error("Package %s not found in available packages.", package_name)
            return None

        latest_tag = self.find_latest_tag_for_package(package_name)
        if not latest_tag:
            self.logger.error("No release tags found for package %s.", package_name)
            return None

        return latest_tag

    def _process_file_diff(self, file_path: str, latest_tag: str) -> bool:
        """Process and show diff for a single file.

        Compares the file at the given path between its current state and the state
        at the latest tag. Shows a colored diff output if changes are detected.

        Args:
            file_path: The path to the file to process.
            latest_tag: The git tag to compare against.

        Returns:
            True if the file is new (didn't exist at the specified tag), False otherwise.
        """
        try:
            cmd = ["git", "show", f"{latest_tag}:{file_path}"]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:  # File is new
                return True

            # Get current file content
            old_content = result.stdout
            current_path = Path(file_path)
            if not current_path.exists():
                self.logger.warning("File %s no longer exists.", file_path)
                return False

            new_content = current_path.read_text(encoding="utf-8")

            # Show diff only if the file existed before
            color_print(f"\nChanges in {file_path}:", "cyan")
            diff_result = show_diff(old=old_content, new=new_content)

            # Print summary
            if diff_result.has_changes:
                self.logger.info(
                    "\nSummary: %d addition%s, %d deletion%s.",
                    len(diff_result.additions),
                    "s" if len(diff_result.additions) != 1 else "",
                    len(diff_result.deletions),
                    "s" if len(diff_result.deletions) != 1 else "",
                )

            return False
        except Exception as e:
            self.logger.error("Error showing diff for %s: %s", file_path, str(e))
            return False

    def _display_new_files(self, new_files: list[str]) -> None:
        """Display the list of new files.

        Args:
            new_files: The list of new file paths.
        """
        if new_files:
            color_print("\nNew files:", "green")
            for file_path in new_files:
                print(f"  + {file_path}")

    @classmethod
    def discover_packages(cls) -> list[str]:
        """Discover available packages in the packages directory."""
        return [p.name for p in cls.PACKAGES_PATH.glob("*") if (p / "pyproject.toml").exists()]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description="Analyze the impact of changes in dsbase on dependent packages.")
    parser.add_argument(
        "-b",
        "--base",
        default="HEAD",
        help="Git reference to compare against (default: HEAD)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show detailed output",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="only check staged changes, not working directory changes",
    )
    parser.add_argument(
        "--diff",
        metavar="PACKAGE",
        help="show detailed diffs for the specified package",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to analyze impact of changes in dsbase."""
    env = EnvManager(add_debug=True)
    logger = LocalLogger().get_logger(simple=True, env=env)
    args = parse_args()

    packages = ImpactAnalyzer.discover_packages()
    logger.debug("Discovered packages: %s", ", ".join(packages))

    analyzer = ImpactAnalyzer(packages, args, logger)

    if args.diff:  # If a specific package is specified for diff, just show that
        analyzer.show_package_diffs(args.diff)
    else:  # Otherwise run the normal analysis
        analyzer.analyze()


if __name__ == "__main__":
    main()
