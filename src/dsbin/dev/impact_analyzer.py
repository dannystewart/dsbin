"""Analyze the impact of changes in repositories and their dependencies."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import PolyArgs, WalkingMan, walking_man
from polykit.env import PolyEnv
from polykit.files import PolyDiff
from polykit.formatters import print_color
from polykit.log import PolyLog

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
    """Analyzes the impact of changes in repositories and their dependencies."""

    def __init__(
        self,
        base_repo: RepoConfig | None,
        repos: list[RepoConfig],
        args: argparse.Namespace,
        logger: Logger,
    ) -> None:
        self.base_repo = base_repo
        self.repos = repos
        self.logger = logger
        self.commit = args.commit
        self.staged_only = args.staged_only
        self.verbose = args.verbose
        self.hide_untagged = args.hide_untagged
        self.include_pyproject = args.include_pyproject

        # Initialize empty lists for changes
        self.changed_files: list[str] = []
        self.changed_modules: set[str] = set()
        self.impacted_repos: dict[str, set[str]] = {}

        # Cache for imports to avoid rescanning
        self._imports_cache: dict[str, dict[str, set[str]]] = {}

    def analyze(self) -> None:
        """Run the analysis and display results."""
        # Analyze base library changes and their impact (if base repo is specified)
        if self.base_repo:
            self.analyze_base_changes()

        # Analyze repo changes since last release
        self.analyze_repo_changes()
        self.display_repo_changes()

        # Determine which repos need releases
        self.display_release_recommendations()

    def analyze_base_changes(self) -> None:
        """Analyze changes in base library and their impact on dependent repos."""
        if not self.base_repo:
            return

        # Get changed files in base repo
        self.changed_files = self.find_changed_files(
            self.base_repo.path, self.commit, self.staged_only
        )

        if not self.changed_files:
            self.logger.info("✓ No Python files changed in %s.", self.base_repo.name)
            return

        print_color("\n=== Current Changes Detected ===\n", "yellow")

        print_color(f"Changed files in {self.base_repo.name}:", "blue")
        for file in self.changed_files:
            print(f"  {file}")

        # Convert to module paths
        self.changed_modules = self.get_changed_modules(self.changed_files, self.base_repo.path)
        print_color("\nChanged modules:", "blue")
        for module in sorted(self.changed_modules):
            print(f"  {module}")

        # Analyze impact
        self.impacted_repos = self.analyze_impact(self.changed_modules)

        if self.impacted_repos:
            print_color("\n=== Current Impacted Repositories ===", "yellow")
            for repo_name, imports in self.impacted_repos.items():
                print_color(f"\n{repo_name} (uses {len(imports)} affected modules):", "cyan")
                for import_path in sorted(imports):
                    print(f"  - {import_path}")
        else:
            self.logger.info("No repositories are directly impacted by these changes.")

    def display_repo_changes(self) -> None:
        """Display changes in repositories since their last release."""
        WalkingMan.clear(line_above=True)
        if self.base_repo:
            print_color("\n=== Repository Changes Since Last Release (Independent) ===", "yellow")
        else:
            print_color("\n=== Repository Changes Since Last Release ===", "yellow")

        for repo in self.repos:
            if repo.latest_tag:
                if repo.changes:
                    print_color(f"\n{repo.name} (last release: {repo.latest_tag}):", "cyan")

                    # Group changes by directory to reduce noise
                    self._display_grouped_changes(repo)
            elif not self.hide_untagged:
                print_color(f"\nNo release tags found: {repo.name}", "red")

    def _display_grouped_changes(self, repo: RepoConfig) -> None:
        """Display changes grouped by directory to reduce output noise."""
        # Find common prefix to strip
        src_prefix = "src/"
        has_src_prefix = all(change.startswith(src_prefix) for change in repo.changes if change)

        # Group changes by first-level directory
        grouped_changes: dict[str, list[str]] = {}

        for file_path in repo.changes:
            # Skip empty paths
            if not file_path:
                continue

            # Strip src/ prefix if all files have it
            if has_src_prefix and file_path.startswith(src_prefix):
                file_path = file_path[len(src_prefix) :]

            # Further strip the repo name if it's a prefix
            repo_prefix = f"{repo.name}/"
            file_path = file_path.removeprefix(repo_prefix)

            # Group by first directory
            parts = file_path.split("/")

            if len(parts) > 1:
                group = parts[0]
                remainder = "/".join(parts[1:])
                if group not in grouped_changes:
                    grouped_changes[group] = []
                grouped_changes[group].append(remainder)
            else:
                # Top-level files
                if "root" not in grouped_changes:
                    grouped_changes["root"] = []
                grouped_changes["root"].append(file_path)

        # Display the grouped changes
        for group, files in sorted(grouped_changes.items()):
            if group == "root":
                print_color(f"    Root directory ({len(files)} files):", "blue")
            else:
                print_color(f"    {group}/ ({len(files)} files):", "blue")

            for file in sorted(files):
                print(f"      - {file}")

    def display_release_recommendations(self) -> None:
        """Display recommendations for repos that need new releases."""
        print_color("\nRepositories requiring new releases:", "yellow")

        if self.base_repo:
            self._display_base_repo_impact()
            self._display_repos_with_changes()
            self._display_release_summary()
        else:
            self._display_simple_release_recommendations()

    def _display_base_repo_impact(self) -> None:
        """Display repositories impacted by changes in the base repo."""
        if not self.base_repo:
            print_color("No base repository specified.", "red")
            return

        if self.impacted_repos:
            print_color(f"\n  Impacted by changes in {self.base_repo.name}:", "magenta")
            for repo_name in self.impacted_repos:
                print_color(f"    - {repo_name}", "green")
        elif self.changed_files:
            print_color(
                f"\n  No repositories impacted by changes in {self.base_repo.name}", "magenta"
            )

    def _display_repos_with_changes(self) -> None:
        """Display repositories with their own independent changes since last release."""
        print_color("\n  With independent changes:", "magenta")

        repos_with_changes = [repo for repo in self.repos if repo.needs_release]

        if repos_with_changes:
            for repo in repos_with_changes:
                if repo.name in self.impacted_repos:
                    print_color(f"    - {repo.name} (also impacted by base changes)", "green")
                else:
                    print_color(f"    - {repo.name}", "green")
        else:
            print_color("    None", "green")

    def _display_release_summary(self) -> None:
        """Display a summary of repositories requiring releases and the reasons."""
        release_repos = self._get_release_repos_with_reasons()

        if release_repos:
            print_color("\n  Summary of required releases:", "magenta")
            for repo_name, reasons in sorted(release_repos.items()):
                print_color(f"    - {repo_name}:", "green")
                for reason in reasons:
                    print(f"        {reason}")
        elif self.changed_files and self.base_repo:
            print_color(
                f"\n  No dependent repositories need releases, but consider releasing {self.base_repo.name}.",
                "yellow",
            )
        else:
            print_color("\n  No releases required", "green")

    def _get_release_repos_with_reasons(self) -> dict[str, list[str]]:
        """Get a dictionary mapping repo names to reasons for release."""
        release_repos = {}

        # Add repos impacted by base changes
        if self.base_repo:
            for repo_name in self.impacted_repos:
                release_repos[repo_name] = [f"Affected by changes in {self.base_repo.name}"]

        # Add repos with their own changes
        for repo in self.repos:
            if repo.needs_release:
                if repo.name in release_repos:
                    release_repos[repo.name].append(
                        f"Has changes since last release ({repo.latest_tag})"
                    )
                else:
                    release_repos[repo.name] = [
                        f"Has changes since last release ({repo.latest_tag})"
                    ]

        return release_repos

    def _display_simple_release_recommendations(self) -> None:
        """Display simple release recommendations when no base repo is specified."""
        release_repos = {}

        # Add repos with their own changes
        for repo in self.repos:
            if repo.needs_release:
                release_repos[repo.name] = [f"Has changes since last release ({repo.latest_tag})"]

        if release_repos:
            for repo_name, reasons in sorted(release_repos.items()):
                print_color(f"  - {repo_name}:", "green")
                for reason in reasons:
                    print(f"      {reason}")
        else:
            print_color("  None", "green")

    def find_imports_in_file(self, file_path: Path, base_name: str) -> set[str]:
        """Find all imports from the base library in a given file."""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            self.logger.warning("Couldn't read %s: %s", file_path, str(e))
            return set()

        imports = set()
        base_prefix = f"{base_name}."

        try:  # Parse the Python file
            tree = ast.parse(content)

            # Look for imports
            for node in ast.walk(tree):
                # Regular imports: import base.xyz
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.startswith(base_prefix):
                            imports.add(name.name)

                # From imports: from base import xyz
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith(base_name)
                ):
                    imports.update(f"{node.module}.{name.name}" for name in node.names)
        except SyntaxError:
            self.logger.warning("Couldn't parse %s as a valid Python file.", file_path)

        return imports

    def find_latest_tag(self, repo_path: Path) -> str | None:
        """Return the most recent version tag in the Git history, or None if not found."""
        try:
            # First, check if this is even a git repository
            check_git_cmd = ["git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree"]
            result = subprocess.run(check_git_cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                self.logger.warning("%s is not a git repository, skipping tag search.", repo_path)
                return None

            # Get all tags matching version pattern (v*.*.*)
            cmd = ["git", "-C", str(repo_path), "tag", "--sort=-v:refname", "-l", "v[0-9]*"]
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
                # Try without 'v' prefix as fallback
                cmd = [
                    "git",
                    "-C",
                    str(repo_path),
                    "tag",
                    "--sort=-v:refname",
                    "-l",
                    "[0-9]*.[0-9]*.[0-9]*",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                tags = result.stdout.strip().splitlines()
                self.logger.debug(
                    "Fallback search found %d tags: %s",
                    len(tags),
                    tags[:5] if len(tags) > 5 else tags,
                )

            if not tags:
                return None

            latest_tag = tags[0]
            self.logger.debug("Latest tag: %s", latest_tag)
            return latest_tag

        except subprocess.CalledProcessError as e:
            self.logger.debug("Git error for %s: %s", repo_path, str(e))
            return None

        except Exception as e:
            self.logger.debug("Unexpected error for %s: %s", repo_path, str(e))
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

            # Filter for Python files only (and pyproject.toml if requested)
            included_files = [f for f in changed_files if f.endswith(".py")]
            if self.include_pyproject:
                pyproject_files = [f for f in changed_files if Path(f).name == "pyproject.toml"]
                included_files.extend(pyproject_files)

            self.logger.debug(
                "Found %d files changed in %s since %s.", len(included_files), repo_path, tag
            )
            return included_files

        except subprocess.CalledProcessError as e:
            self.logger.debug("Error checking changes for %s since %s: %s", repo_path, tag, str(e))
            return []

        except Exception as e:
            self.logger.debug("Unexpected error for %s: %s", repo_path, str(e))
            return []

    def analyze_repo_changes(self) -> None:
        """Analyze changes to repositories since their last release tag."""
        for repo in self.repos:
            latest_tag = self.find_latest_tag(repo.path)
            repo.latest_tag = latest_tag

            if latest_tag:
                changes = self.get_changes_since_tag(repo.path, latest_tag)
                repo.changes = changes
                repo.needs_release = len(changes) > 0

                if self.verbose and changes:
                    print_color(
                        f"\nDetected {len(changes)} files changed in {repo.name} since {latest_tag}",
                        "blue",
                    )

    def scan_repo_for_imports(self, repo_path: Path, base_name: str) -> dict[str, set[str]]:
        """Scan a repo for all base library imports."""
        repo_key = str(repo_path)

        # Use cached results if available
        if repo_key in self._imports_cache:
            return self._imports_cache[repo_key]

        imports_by_file = {}

        if self.verbose:
            print_color(f"Scanning {repo_path} for imports...", "blue")

        # Find all Python files
        for py_file in repo_path.glob("**/*.py"):
            if imports := self.find_imports_in_file(py_file, base_name):
                imports_by_file[str(py_file)] = imports
                if self.verbose:
                    print_color(
                        f"  Found {len(imports)} imports in {py_file.relative_to(repo_path)}",
                        "cyan",
                    )

        # Cache the results
        self._imports_cache[repo_key] = imports_by_file
        return imports_by_file

    def find_changed_files(
        self, repo_path: Path, commit: str = "HEAD", staged_only: bool = False
    ) -> list[str]:
        """Find Python files changed in the repo compared to the given commit."""
        try:
            changed_files = []

            # Get unstaged changes if requested
            if not staged_only:
                cmd = ["git", "-C", str(repo_path), "diff", "--name-only", commit]
                self.logger.debug("Running: %s", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                unstaged = result.stdout.splitlines()
                self.logger.debug("Found %d unstaged changes: %s", len(unstaged), unstaged)
                changed_files.extend(unstaged)

            # Get staged changes
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
            self.logger.debug("Git error for %s: %s", repo_path, str(e))
            return []

        except Exception as e:
            self.logger.debug("Unexpected error for %s: %s", repo_path, str(e))
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
        base_name = self.base_repo.name if self.base_repo else ""

        for repo in self.repos:
            imports_by_file = self.scan_repo_for_imports(repo.path, base_name)
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
        repo = next((r for r in self.repos if r.name == repo_name), None)
        if not repo:
            self.logger.error("Repository %s not found.", repo_name)
            return

        # Get or refresh the latest tag if needed
        if not repo.latest_tag:
            repo.latest_tag = self.find_latest_tag(repo.path)

        if not repo.latest_tag:
            self.logger.error("No release tags found for repository %s.", repo_name)
            return

        # Get changed files
        changed_files = self.get_changes_since_tag(repo.path, repo.latest_tag)

        if not changed_files:
            self.logger.info("No changes detected in %s since %s.", repo_name, repo.latest_tag)
            return

        print_color(f"\n=== Detailed Changes in {repo_name} since {repo.latest_tag} ===", "yellow")

        # Track new files separately
        new_files = []

        for file_path in changed_files:
            is_new = self._process_file_diff(repo.path, file_path, repo.latest_tag)
            if is_new:
                new_files.append(file_path)

        # Display new files separately
        if new_files:
            print_color("\nNew files:", "green")
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
            print_color(f"\nChanges in {file_path}:", "cyan")
            diff_result = PolyDiff.content(old=old_content, new=new_content)

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


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def count_valid_repos(
    args: argparse.Namespace, logger: Logger, excluded_paths: list[Path] | None = None
) -> tuple[list[RepoConfig], int, int]:
    """Count valid repositories in the list."""
    repos = []
    valid_repos_count = 0
    skipped_repos_count = 0

    if args.repos is None:
        return repos, valid_repos_count, skipped_repos_count

    excluded_paths = excluded_paths or []

    for repo_path_str in args.repos:
        repo_path = Path(repo_path_str).resolve()

        # Skip excluded paths
        if repo_path in excluded_paths:
            logger.debug("Path %s is excluded, skipping.", repo_path)
            skipped_repos_count += 1
            continue

        # Skip non-existent paths
        if not repo_path.exists():
            logger.warning("Path %s does not exist, skipping.", repo_path)
            skipped_repos_count += 1
            continue

        # Skip non-directories
        if not repo_path.is_dir():
            logger.debug("Path %s is not a directory, skipping.", repo_path)
            skipped_repos_count += 1
            continue

        # Check if it's a git repository (but don't error, just skip)
        if not is_git_repo(repo_path):
            logger.debug("%s is not a git repository, skipping.", repo_path)
            skipped_repos_count += 1
            continue

        repos.append(RepoConfig(name=repo_path.name, path=repo_path))
        valid_repos_count += 1

    return repos, valid_repos_count, skipped_repos_count


def setup_base_repo(args: argparse.Namespace, logger: Logger) -> RepoConfig | None:
    """Set up the base repository if specified."""
    if not args.base:
        return None

    base_path = Path(args.base).resolve()
    if not base_path.exists():
        logger.error("Base repository path %s does not exist.", base_path)
        return None

    # Check if it's a git repository
    if not is_git_repo(base_path):
        logger.error("%s is not a git repository.", base_path)
        return None

    return RepoConfig(name=base_path.name, path=base_path)


def create_repo_config(repo_str: str, logger: Logger) -> RepoConfig | None:
    """Create a repository config from a repository string."""
    repo_path = Path(repo_str).resolve()

    # Skip non-existent paths
    if not repo_path.exists():
        logger.warning("Path %s does not exist, skipping.", repo_path)
        return None

    # Skip non-directories
    if not repo_path.is_dir():
        logger.debug("Path %s is not a directory, skipping.", repo_path)
        return None

    # Check if it's a git repository
    if not is_git_repo(repo_path):
        logger.debug("%s is not a git repository, skipping.", repo_path)
        return None

    return RepoConfig(name=repo_path.name, path=repo_path)


def determine_diff_repo(
    repos: list[RepoConfig], base_repo: RepoConfig | None, args: argparse.Namespace, logger: Logger
) -> tuple[str | None, RepoConfig | None]:
    """Determine which repository to show diffs for.

    Returns:
        A tuple of (repo_name, repo_config) where repo_name is the name of the repository
        and repo_config is the corresponding RepoConfig object, or None if not found.
    """
    if args.diff_repo:
        # If a specific repo was mentioned with --diff-repo, use that
        diff_repo_name = Path(args.diff_repo).name if "/" in args.diff_repo else args.diff_repo

        # First, check if it's already in our repos list
        diff_repo_config = next((r for r in repos if r.name == diff_repo_name), None)

        # If not found in repos list but it's a path, try to create a config for it
        if not diff_repo_config and "/" in args.diff_repo:
            diff_repo_config = create_repo_config(args.diff_repo, logger)
            if diff_repo_config:
                diff_repo_name = diff_repo_config.name

        return diff_repo_name, diff_repo_config

    if len(repos) == 1:
        # If only one repo was specified with -r, use that
        return repos[0].name, repos[0]

    if base_repo and not repos:
        # If only a base repo was specified with -b, use that
        return base_repo.name, base_repo

    if len(repos) > 1:
        # If multiple repos were specified, use the first one but warn the user
        repo_name = repos[0].name
        logger.warning(
            "Multiple repositories specified with -r but no --diff-repo. "
            "Showing diffs for the first one: %s",
            repo_name,
        )
        return repo_name, repos[0]

    # This shouldn't happen due to earlier validation
    logger.error("No repository specified for diffs.")
    return None, None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__, arg_width=34)
    parser.add_argument(
        "-b", "--base", metavar="REPO", help="path to the base repository for impact analysis"
    )
    parser.add_argument(
        "-r",
        "--repos",
        metavar="REPO",
        nargs="+",
        help="paths to package repos to analyze (accepts multiple)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        metavar="REPO",
        nargs="+",
        help="paths to package repos to exclude from analysis (accepts multiple)",
    )
    parser.add_argument(
        "-c", "--commit", default="HEAD", help="Git reference to compare against (default: HEAD)"
    )
    parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="show detailed diffs for the specified repository",
    )
    parser.add_argument(
        "--diff-repo",
        metavar="REPO",
        help="specify which repository to show diffs for (optional with --diff)",
    )
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="show only staged changes rather than working directory",
    )
    parser.add_argument(
        "--hide-untagged",
        action="store_true",
        help="hide repositories with no release tags in the output",
    )
    parser.add_argument(
        "--include-pyproject",
        action="store_true",
        help="consider pyproject.toml changes as well",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show detailed output")

    # Ensure at least one repo is specified
    args = parser.parse_args()
    if not args.base and not args.repos:
        parser.error("At least one repository must be specified with -b or -r")

    return args


def main() -> None:
    """Analyze repository changes and impact."""
    env = PolyEnv(add_debug=True)
    logger = PolyLog.get_logger(simple=True, level=env.log_level)
    args = parse_args()

    with walking_man(speed=0.12):
        # Create base repo config if specified
        base_repo = setup_base_repo(args, logger)

        # Process exclusions - normalize paths for accurate comparison
        excluded_paths = []
        if args.exclude:
            excluded_paths = [Path(path).resolve() for path in args.exclude]
            logger.debug("Excluding %d repositories from analysis.", len(excluded_paths))

        repos, valid_repos_count, _ = count_valid_repos(args, logger, excluded_paths)

        # Validate we have something to work with
        if not args.diff_repo and valid_repos_count == 0 and not base_repo:
            logger.error("No valid repositories found to analyze.")
            return

        # Create analyzer with updated arguments
        analyzer = ImpactAnalyzer(base_repo, repos, args, logger)

        # Always analyze repo changes to get latest tags
        analyzer.analyze_repo_changes()

        if args.diff:  # If diff flag is set
            repo_name, diff_repo_config = determine_diff_repo(repos, base_repo, args, logger)

            if repo_name and diff_repo_config:
                # If the diff repo wasn't in our original list, add it temporarily for analysis
                if diff_repo_config not in analyzer.repos:
                    analyzer.repos.append(diff_repo_config)
                    # Get its latest tag
                    diff_repo_config.latest_tag = analyzer.find_latest_tag(diff_repo_config.path)

                analyzer.show_repo_diffs(repo_name)
            elif repo_name:  # We have a name but no config
                logger.error("Could not find repository configuration for %s.", repo_name)
        else:  # Otherwise run the normal analysis
            analyzer.analyze()


if __name__ == "__main__":
    main()
