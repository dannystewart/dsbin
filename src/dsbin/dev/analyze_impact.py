"""Analyze release impact based on changes internally or to a utility library."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase import ArgParser, EnvManager, LocalLogger
from dsbase.text import color_print
from dsbase.text.diff import show_diff

if TYPE_CHECKING:
    import argparse
    from logging import Logger


@dataclass
class RepoConfig:
    """Configuration for a repository to analyze."""

    name: str
    path: Path
    latest_tag: str | None = None
    changes: list[str] = field(default_factory=list)
    needs_release: bool = False


class ImpactAnalyzer:
    """Analyzes the impact of changes in a utility library on dependent packages."""

    def __init__(
        self,
        utility_repo: RepoConfig,
        dependent_repos: list[RepoConfig],
        args: argparse.Namespace,
        logger: Logger,
    ) -> None:
        self.utility_repo = utility_repo
        self.dependent_repos = dependent_repos
        self.logger = logger
        self.base_commit = args.base
        self.verbose = args.verbose

        # Initialize empty lists for changes
        self.changed_files: list[str] = []
        self.changed_modules: set[str] = set()
        self.impacted_repos: dict[str, set[str]] = {}

        # Cache for imports to avoid rescanning
        self._imports_cache: dict[str, dict[str, set[str]]] = {}

    def analyze(self) -> None:
        """Run the analysis and display results."""
        # Analyze utility library changes and their impact
        self.analyze_utility_changes()

        # Analyze dependent repo changes since last release
        self.analyze_repo_changes()
        self.display_repo_changes()

        # Determine which repos need releases
        self.display_release_recommendations()

    def analyze_utility_changes(self) -> None:
        """Analyze changes in utility library and their impact on dependent repos."""
        # Get changed files in utility repo
        self.changed_files = self.find_changed_files(self.utility_repo.path, self.base_commit)

        if not self.changed_files:
            self.logger.info("✓ No Python files changed in %s.", self.utility_repo.name)
            return

        color_print("\n=== Current Changes Detected ===\n", "yellow")

        color_print(f"Changed files in {self.utility_repo.name}:", "blue")
        for file in self.changed_files:
            print(f"  {file}")

        # Convert to module paths
        self.changed_modules = self.get_changed_modules(self.changed_files, self.utility_repo.path)
        color_print("\nChanged modules:", "blue")
        for module in sorted(self.changed_modules):
            print(f"  {module}")

        # Analyze impact
        self.impacted_repos = self.analyze_impact(self.changed_modules)

        if self.impacted_repos:
            color_print("\n=== Current Impacted Repositories ===", "yellow")
            for repo_name, imports in self.impacted_repos.items():
                color_print(f"\n{repo_name} (uses {len(imports)} affected modules):", "cyan")
                for import_path in sorted(imports):
                    print(f"  - {import_path}")
        else:
            self.logger.info("No repositories are directly impacted by these changes.")

    def display_repo_changes(self) -> None:
        """Display changes in repositories since their last release."""
        color_print("\n=== Repository Changes Since Last Release ===", "yellow")

        for repo in self.dependent_repos:
            if repo.latest_tag:
                if repo.changes:
                    color_print(f"\n{repo.name} (last release: {repo.latest_tag}):", "cyan")
                    for file in repo.changes:
                        print(f"  - {file}")
            else:
                color_print(f"\n{repo.name}:", "red")
                print("  No release tags found")

    def display_release_recommendations(self) -> None:
        """Display recommendations for repos that need new releases."""
        color_print("\nRepositories requiring new releases:", "yellow")
        release_repos = {}  # Map repo names to reasons for release

        # Add repos impacted by utility changes
        for repo_name in self.impacted_repos:
            release_repos[repo_name] = ["Affected by utility library changes"]

        # Add repos with their own changes
        for repo in self.dependent_repos:
            if repo.needs_release:
                if repo.name in release_repos:
                    release_repos[repo.name].append(
                        f"Has {len(repo.changes)} file changes since last release"
                    )
                else:
                    release_repos[repo.name] = [
                        f"Has {len(repo.changes)} file changes since last release"
                    ]

        if release_repos:
            for repo_name, reasons in sorted(release_repos.items()):
                color_print(f"  - {repo_name}:", "green")
                for reason in reasons:
                    print(f"      {reason}")
        elif self.changed_files:
            color_print(
                f"  None (but you should still release a new version of {self.utility_repo.name})",
                "yellow",
            )
        else:
            color_print("  None", "green")

    def find_imports_in_file(self, file_path: Path, utility_name: str) -> set[str]:
        """Find all imports from the utility library in a given file."""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            self.logger.warning("Couldn't read %s: %s", file_path, str(e))
            return set()

        imports = set()
        utility_prefix = f"{utility_name}."

        try:  # Parse the Python file
            tree = ast.parse(content)

            # Look for imports
            for node in ast.walk(tree):
                # Regular imports: import utility.xyz
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.startswith(utility_prefix):
                            imports.add(name.name)

                # From imports: from utility import xyz
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith(utility_name):
                        imports.update(f"{node.module}.{name.name}" for name in node.names)
        except SyntaxError:
            self.logger.warning("Couldn't parse %s as a valid Python file.", file_path)

        return imports

    def find_latest_tag(self, repo_path: Path) -> str | None:
        """Return the most recent tag in the Git history, or None if not found."""
        try:
            # Get all tags sorted by version (most recent first)
            cmd = ["git", "-C", str(repo_path), "tag", "--sort=-v:refname"]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            tags = result.stdout.strip().splitlines()

            self.logger.debug(
                "Found %d tags for repo at %s: %s",
                len(tags),
                repo_path,
                tags[:5] if len(tags) > 5 else tags,
            )

            if not tags:
                return None

            latest_tag = tags[0]
            self.logger.debug("Latest tag: %s", latest_tag)
            return latest_tag
        except subprocess.CalledProcessError as e:
            self.logger.error("Error finding tags for %s: %s", repo_path, str(e))
            return None

    def get_changes_since_tag(self, repo_path: Path, tag: str) -> list[str]:
        """Get files changed in a repo since the specified tag."""
        try:
            cmd = ["git", "-C", str(repo_path), "diff", "--name-only", f"{tag}..HEAD"]
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
                "Found %d Python files changed in %s since %s", len(python_files), repo_path, tag
            )
            return python_files
        except subprocess.CalledProcessError as e:
            self.logger.error("Error checking changes for %s since %s: %s", repo_path, tag, str(e))
            return []

    def analyze_repo_changes(self) -> None:
        """Analyze changes to repositories since their last release tag."""
        for repo in self.dependent_repos:
            latest_tag = self.find_latest_tag(repo.path)
            repo.latest_tag = latest_tag

            if latest_tag:
                changes = self.get_changes_since_tag(repo.path, latest_tag)
                repo.changes = changes
                repo.needs_release = len(changes) > 0

                if self.verbose and changes:
                    color_print(
                        f"\nDetected {len(changes)} files changed in {repo.name} since {latest_tag}",
                        "blue",
                    )

    def scan_repo_for_imports(self, repo_path: Path, utility_name: str) -> dict[str, set[str]]:
        """Scan a repo for all utility library imports."""
        repo_key = str(repo_path)

        # Use cached results if available
        if repo_key in self._imports_cache:
            return self._imports_cache[repo_key]

        imports_by_file = {}

        if self.verbose:
            color_print(f"Scanning {repo_path} for imports...", "blue")

        # Find all Python files
        for py_file in repo_path.glob("**/*.py"):
            if imports := self.find_imports_in_file(py_file, utility_name):
                imports_by_file[str(py_file)] = imports
                if self.verbose:
                    color_print(
                        f"  Found {len(imports)} imports in {py_file.relative_to(repo_path)}",
                        "cyan",
                    )

        # Cache the results
        self._imports_cache[repo_key] = imports_by_file
        return imports_by_file

    def find_changed_files(
        self, repo_path: Path, base_commit: str = "HEAD", include_staged: bool = True
    ) -> list[str]:
        """Find Python files changed in the repo compared to base_commit."""
        try:
            changed_files = []

            # Get unstaged changes
            cmd = ["git", "-C", str(repo_path), "diff", "--name-only", base_commit]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            unstaged = result.stdout.splitlines()
            self.logger.debug("Found %d unstaged changes: %s", len(unstaged), unstaged)
            changed_files.extend(unstaged)

            # Get staged changes if requested
            if include_staged:
                cmd = ["git", "-C", str(repo_path), "diff", "--cached", "--name-only"]
                self.logger.debug("Running: %s", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                staged = result.stdout.splitlines()
                self.logger.debug("Found %d staged changes: %s", len(staged), staged)
                changed_files.extend(staged)

            # Filter for Python files only
            filtered = [f for f in changed_files if f.endswith(".py")]
            self.logger.debug("After filtering for Python files: %s", filtered)
            return filtered
        except subprocess.CalledProcessError as e:
            self.logger.error("Error running git diff: %s", str(e))
            return []

    def get_changed_modules(self, changed_files: list[str], repo_path: Path) -> set[str]:
        """Convert file paths to module paths."""
        modules = set()
        repo_name = repo_path.name
        src_path = repo_path / "src"
        has_src = src_path.exists()

        for file_path in changed_files:
            if file_path.endswith(".py"):
                path_obj = Path(file_path)

                # Handle src layout vs flat layout
                if has_src and str(path_obj).startswith("src/"):
                    rel_path = str(path_obj).replace("src/", "", 1)
                else:
                    rel_path = str(path_obj)

                # Convert path to module
                module_path = rel_path.replace("/", ".").replace(".py", "")

                # If the module is in the repo's main package, add it
                if module_path.startswith(f"{repo_name}."):
                    modules.add(module_path)
                elif "/" in rel_path:  # It's a submodule but doesn't start with repo name
                    # Try to determine the package name from the path
                    parts = rel_path.split("/")
                    if len(parts) > 1:
                        module_path = rel_path.replace("/", ".").replace(".py", "")
                        modules.add(module_path)
                else:
                    # It's a top-level module
                    modules.add(module_path)

                # Also add the parent module
                parts = module_path.split(".")
                if len(parts) > 1:
                    parent = ".".join(parts[:-1])
                    modules.add(parent)

        return modules

    def analyze_impact(self, changed_modules: set[str]) -> dict[str, set[str]]:
        """Analyze which repos are impacted by changes to specific modules."""
        impacted_repos = {}
        utility_name = self.utility_repo.name

        for repo in self.dependent_repos:
            imports_by_file = self.scan_repo_for_imports(repo.path, utility_name)
            repo_imports = set()

            # Check if any of the changed modules are imported
            for imports in imports_by_file.values():
                for import_path in imports:
                    for changed_module in changed_modules:
                        # Check if the import matches or is a submodule of the changed module
                        if import_path == changed_module or import_path.startswith(
                            f"{changed_module}."
                        ):
                            repo_imports.add(import_path)

            if repo_imports:
                impacted_repos[repo.name] = repo_imports

        return impacted_repos

    def show_repo_diffs(self, repo_name: str) -> None:
        """Show detailed diffs for a specific repo since its last release."""
        # Find the repo config
        repo = next((r for r in self.dependent_repos if r.name == repo_name), None)
        if not repo:
            self.logger.error("Repository %s not found.", repo_name)
            return

        # Check if the repo has a latest tag
        if not repo.latest_tag:
            self.logger.error("No release tags found for repository %s.", repo_name)
            return

        # Get changed files
        changed_files = self.get_changes_since_tag(repo.path, repo.latest_tag)

        if not changed_files:
            self.logger.info("No changes detected in %s since %s.", repo_name, repo.latest_tag)
            return

        color_print(f"\n=== Detailed Changes in {repo_name} since {repo.latest_tag} ===", "yellow")

        # Track new files separately
        new_files = []

        for file_path in changed_files:
            is_new = self._process_file_diff(repo.path, file_path, repo.latest_tag)
            if is_new:
                new_files.append(file_path)

        # Display new files separately
        if new_files:
            color_print("\nNew files:", "green")
            for file_path in new_files:
                print(f"  + {file_path}")

    def _process_file_diff(self, repo_path: Path, file_path: str, latest_tag: str) -> bool:
        """Process and show diff for a single file.

        Returns:
            True if the file is new, False otherwise.
        """
        try:
            cmd = ["git", "-C", str(repo_path), "show", f"{latest_tag}:{file_path}"]
            self.logger.debug("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:  # File is new
                return True

            # Get current file content
            old_content = result.stdout
            current_path = repo_path / file_path
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


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(
        description="Analyze the impact of changes in a utility library on dependent packages."
    )
    parser.add_argument(
        "-u", "--utility-repo", required=True, help="Path to the utility repository (e.g., dsbase)"
    )
    parser.add_argument(
        "-d",
        "--dependent-repos",
        required=True,
        nargs="+",
        help="Paths to dependent repositories to analyze",
    )
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
        metavar="REPO",
        help="show detailed diffs for the specified repository",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to analyze impact of changes in a utility library."""
    env = EnvManager(add_debug=True)
    logger = LocalLogger().get_logger(simple=True, env=env)
    args = parse_args()

    # Create utility repo config
    utility_path = Path(args.utility_repo).resolve()
    if not utility_path.exists():
        logger.error("Utility repository path %s does not exist", utility_path)
        return

    utility_repo = RepoConfig(name=utility_path.name, path=utility_path)

    # Create dependent repo configs
    dependent_repos = []
    for repo_path_str in args.dependent_repos:
        repo_path = Path(repo_path_str).resolve()
        if not repo_path.exists():
            logger.warning("Dependent repository path %s does not exist, skipping", repo_path)
            continue

        dependent_repos.append(RepoConfig(name=repo_path.name, path=repo_path))

    if not dependent_repos:
        logger.error("No valid dependent repositories provided")
        return

    logger.debug("Analyzing utility repo: %s", utility_repo.name)
    logger.debug("Dependent repos: %s", ", ".join(repo.name for repo in dependent_repos))

    analyzer = ImpactAnalyzer(utility_repo, dependent_repos, args, logger)

    if args.diff:  # If a specific repo is specified for diff, just show that
        analyzer.show_repo_diffs(args.diff)
    else:  # Otherwise run the normal analysis
        analyzer.analyze()


if __name__ == "__main__":
    main()
