# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

*No documentation yet, but you can use the link above to see what's changing.*

## [0.7.17] (2025-04-14)

### Changed

- Restructures documentation with more logical organization, prioritizing development scripts and system tools.
- Reorganizes project scripts in `pyproject.toml` to match the new documentation layout.
- Simplifies TOML encoding operations in `pyprojector` to ensure consistent types.
- Updates dependencies for Pillow (11.1.0 → 11.2.1) and Polykit (0.10.1.dev → 0.10.2.dev).

### Removed

- Removes several obsolete scripts: `poetry_migrate.py`, `uvmigrate.py`, `pkginst.py`, `spacepurger.py`, and `ytdl.py`. These were unmaintained and potentially risky to use, so it was time to say goodbye.

## [0.7.16] (2025-04-13)

### Changed

- Upgrades documentation to a beautiful new [Tokyo Night](https://github.com/dannystewart/pdoc-tokyo-night) theme, created by yours truly, replacing the basic dark theme with improved typography, visual hierarchy, and enhanced syntax highlighting for a more polished, professional appearance.

## [0.7.15] (2025-04-13)

### Added

- Adds dark theme for pdoc documentation with Monokai syntax highlighting, dark background, and custom styling for better readability.

### Changed

- Updates Ruff configuration version from 22 to 23.
- Standardizes indentation in pre-commit config using spaces instead of that chaotic mix of tabs and spaces that keeps developers up at night.

### Fixed

- Adds specific rule exceptions for Sphinx configuration files.

## [0.7.14] (2025-04-13)

### `pybumper`

#### Added

- Adds dedicated commit for development version changes after releases, creating a cleaner separation between release commits and development preparation.

#### Changed

- Changes release commit message format from "chore(version)" to "chore(release)" for actual version bump, while keeping "chore(version)" for dev bump.

## [0.7.13] (2025-04-11)

### Fixed

- Fixes `changehostname` by correcting the `Path.open()` parameters for `/etc/hosts`.

### Changed

- Updates dependency versions:
  - Bumps `polykit` from 0.10.0.dev to 0.10.1.dev and increases minimum requirement from >=0.9.1 to >=0.10.0

## [0.7.12] (2025-04-11)

### Added

- Adds `pyprojector`, a new CLI tool for interactively creating and managing `pyproject.toml` files with fuzzy search for PyPI classifiers and smart defaults.
- Enhances `dsver` with command-line options to show all packages (`--all`) or just the deprecated ones (`--deprecated`).

### Changed

- Improves editor selection for `changelogs` editing, trying VS Code first before falling back to system defaults or `nano`.
- Improves code organization in `backupsort` by using PolyArgs for better documentation handling.
- Moves shell utilities from `polykit.shell` to `polykit.cli` for a more logical module structure and to eliminate ongoing confusion.
- Updates parameter name in `PolyFile.list()` from `recurse` to `recursive` for consistency with changes in Polykit 0.10.
- Updates dependencies:
  - Upgrades `polykit` from 0.9.2.dev to 0.10.0.dev.
  - Updates `ruff` from 0.11.4 to 0.11.5.
  - Removes upper bound constraint on `rich` dependency.
  - Adds `prompt-toolkit` and `tomli-w`.

### Fixed

- Restructures version parsing logic in `pybumper` to fix handling of double-digit version numbers.
- Fixes development version display by adding a newline for better readability when showing both release and development versions.

### Chore

- Bumps version to 0.7.12.dev (we're not quite there yet, but we're getting closer!)

## [0.7.11] (2025-04-07)

### Fixed

- `pybumper`
  - Fixes punctuation placement in version update success message.

### Changed

- `dsver`
  - Reorders package list to place `polykit` before `dsbin`—a purely cosmetic change, but `dsbin` depends on `polykit`, so it should come after, damn it!
- `pybumper`
  - Improves logging by moving dev version setting to DEBUG level. More readable, less redundant.
- **Dependencies** (boring but important)
  - Updates `polykit` imports from `polykit.platform` to `polykit.core` for compatibility with changes in 0.8.0.
  - Removes upper bound constraint from `mysql-connector-python`. Freedom for databases!
  - Pins `rich` dependency to stay below v14.0, not because *my* code is incompatible, but because too many *other* people's code is incompatible, and managing dependency conflicts is annoying.

## [0.7.10] (2025-04-07)

### Added

- `pybumper`
  - Adds support for implicit `.dev0` handling when `.dev` suffix lacks a number.
  - Introduces automatic local development version setting after release pushes.
  - Improves logging to display both release and local dev version states.

### Changed

- `dsver`
  - Slows Walking Man speed for deprecated package checks, making the wait less distracting while still not being boring.
  - Simplifies tuple unpacking for type safety, because—as Python's Zen says—explicit is better than implicit.
- `CHANGELOG.md`
  - Standardizes formatting for consistency, because messy changelogs make developers cry. This developer, anyway.

### Fixed

- `backupsort`
  - Fixes type issue by ensuring `env.backupsort_path` is properly converted to a `Path` object.

### Removed

- Removes obsolete scripts (`fml`, `mvdmg`, `pyenversioner`, and `watchtower`).

## [0.7.9] (2025-04-06)

### Changed

- `pybumper`
  - Updates commit message format to align with Conventional Commits, including scoped prefixes for better clarity in monorepos and version bumps. Also refines CLI help text to reflect the new format.

## [0.7.8] (2025-04-06)

### Added

- `update_changelog`
  - Automates moving entries from the "Unreleased" section to a new version, further streamlining changelog updates and reducing manual effort.

### Changed

- Updates `polykit` dependency to version 0.7.4, ensuring compatibility with the latest features and improvements.
- `update_changelog`
  - Improves version insertion logic to handle content in the "Unreleased" section more effectively, ensuring proper ordering when adding new entries.

## [0.7.7] (2025-04-06)

### Added

- `dsver`
  - Flags deprecated packages and shows a warning and recommendation for removal.

### Changed

- Updates `polykit` dependency to v0.7.3 for compatibility with the latest features and fixes.
- `dsver`
  - Centralizes package definitions into a shared constant to reduce redundancy and improve maintainability.

### Removed

- `update_changelog`: Removes the redundant `add_version` argument from `PolyArgs` instantiation, aligning with changes in Polykit 0.7.3.

## [0.7.6] (2025-04-06)

### Added

- `lsbin`
  - Adds GitHub links for script entries in README generation to improve accessibility.
- `update_changelog`
  - Adds functionality to manage GitHub release changelogs, including opening release URLs, improved formatting, and better error handling.
  - Adds GitHub release synchronization for changelogs to streamline release management.

### Changed

- `update_changelog`
  - Improves changelog parsing with better error handling and logging, enhancing the release creation workflow.
  - Refines dry-run feedback for clearer and more user-friendly output.
- `lsbin`
  - Lowers log levels for update operations from `info` to `debug` to reduce log verbosity and enhance clarity during script execution.
- `workspace`
  - Updates commit scopes to include "update_changelog" and improve categorization for changelog updates.

## [0.7.5] (2025-04-06)

### Changed

- Consolidates README update logic into `lsbin` to streamline script management and remove redundancy.
- Improves version insertion logic in the changelog, ensuring proper semantic version ordering and better handling of edge cases.
- Enhances version link generation logic in the changelog, simplifying URL updates, improving maintainability, and adding smarter handling for the "unreleased" link.
- Updates the `polykit` dependency to version 0.7.2.

### Removed

- Removes the redundant `update_readme` script, as its functionality is now part of the `lsbin` script.
- Eliminates the legacy `scriptdep` tool in favor of modern replacements like `impactanalyzer` and `packageanalyzer`.
- Removes the runtime check for the `blessed` library, as it's now a guaranteed dependency.

### Fixed

- Fixes formatting in the changelog to ensure exactly one blank line at the end of the file.

## [0.7.4] (2025-04-06)

### Changed

- Removes obsolete packages from the default dependency list in `checkdeps`.

### Fixed

- Adds a main guard to `oldprojects` script, preventing unintended execution when imported as a library.

## [0.7.3] (2025-04-05)

### Changed

- Updates the `polykit` dependency to version 0.7.1 to ensure compatibility and include the latest improvements.
- Replaces `ArgParser` with `PolyArgs` in the CLI to align with updated naming conventions in the `polykit.cli` module.
- Improves code readability by renaming loop variable `_ispkg` to `_` in `pkgutil.walk_packages`.

## [0.7.2] (2025-04-05)

### Added

- Adds conventional commits scopes for `pre-commit-config`.

### Changed

- Updates all classes and modules for compatibility with Polykit 0.7.0.
- Changes file manager class names to avoid confusion from general-purpose file manager classes or classes for other features.
- Standardizes logging with `PolyLog` and file management with `PolyFile`, improving maintainability and aligning with the updated library structure.
- Loosens Python version constraints to `<4.0` and removes upper bounds for multiple dependencies to improve flexibility.

### Removed

- Removes unused file utility classes, now consolidated into `Polykit`.
- Removes `commitizen` hooks from `pre-commit-config`.
- Drops the `send2trash` and `types-send2trash` packages from dependencies.

### Fixed

- Fixes GitHub URL parsing in the `get_repo_url` function.
- Removes the `LOG001` ignore rule from the Ruff configuration.

## [0.7.1] (2025-04-04)

### Added

- Adds a new module for a text-based adventure game (`src/dsbin/fun/wm_adventure.py`) featuring Walking Man!

### Changed

- Enhances commit categorization logic to use the Conventional Commit format.
- Updates `polykit` import paths to use the `core` module across multiple files.
- Replaces `enviromancer` and `walking-man` imports with `polykit.env` and `polykit.cli` imports across multiple files.
- Updates imports from `logician` and `parser` to `formatter` across multiple files, including color and print formatting utilities.

### Fixed

- Fixes version entry format in the changelog and improves warning messages.

## [0.7.0] (2025-04-04)

### Added

- Adds a confirmation prompt in `GitHelper` to warn users about uncommitted changes before performing a version bump.

### Changed

- Refactors the codebase to integrate Polykit and remove deprecated utilities:
  - Replaces `dsbin_setup()` with `polykit_setup()` across modules.
  - Updates argument parsing from `Arguer` to `ArgParser`.
  - Switches imports from `shelper` and `parseutil` to Polykit modules.
  - Adjusts import paths for color and print functions to align with Polykit structure.
  - Ensures consistent logging and exception handling through Polykit integration.

### Fixed

- Updates `poetry.lock` and `pyproject.toml` to resolve package version issues for Enviromancer, Logician, and Polykit.

### Documentation

- Improves package name detection and validation in the documentation generation workflow.

## [0.6.8] (2025-04-04)

### Fixed

- Fixes a duplicate entry for `parseutil` in the `PACKAGES` list of `repo_run.py`.

## [0.6.7] (2025-04-04)

### Added

- Implements dynamic repository name generation for changelog links.

### Changed

- Updates `pyproject.toml` to include classifiers for improved package metadata.

## [0.6.6] (2025-04-03)

### Fixed

- Fixes incorrect post-release version string to use `post0` in `VersionHelper`.
- Fixes incorrect module path in the `repo-run` entry of `pyproject.toml`.
- Corrects the `repo-run` description in the README.
- Updates license to LGPL as it was intended to be.

## [0.6.5] (2025-04-03)

### Added

- Adds `changelog` script to automate changelog updates and version management.
- Adds Git repository check and pre-commit hook handling to `ConfigManager`.

### Changed

- Renames the package management utility for managing multiple Poetry projects from `updatedeps` to `repo-run`.
- Updates documentation to include a description for `codeconfigs` in README and initialization files.
- Updates README to improve style by adding a newline after the category header in content generation.

## [0.6.4] (2025-04-03)

### Fixed

- Updates color formatting to use `style` instead of `attrs` for `parseutil` update.
- Simplify package name extraction to fix the documentation generation process.

## [0.6.3] (2025-04-03)

**Hotfix for 0.6.2 using an invalid entrypoint.**

### Added

- Adds support for post-update commands and improves configuration management in `ConfigManager`.
- Adds an option to clear Poetry cache when running commands in all packages.
- Adds configuration files for Mypy, GitHub workflows, and code style guidelines.
- Adds a changelog file to document notable changes and versioning.

### Changed

- Changes the name of the `configs` directory and script to `code_configs` for consistency.
- Renames the script entry point to `codeconfigs`.
- Updates `ruff.toml` configuration to consolidate personal sections and reflect the latest version.

### Updated

- Updates `poetry.lock` to bump `ruff` to version 0.11.3 and `typing-extensions` to 4.13.1.
- Updates `poetry.lock` to bump `devpkg` version to 0.2.1 in dependencies.

### Fixed

- Improves GitHub Actions workflow to automatically determine the package name for `pdoc`.

## [0.6.1] (2025-04-03)

### Changed

- Replaces `textparse` and `timecapsule` libraries with `parseutil` for streamlined parsing functionality.
- Updates all remaining references from `dsbase` to `dsbin` to ensure consistency across the codebase.

### Internal

- Refactors `package_analyzer` by updating type hints for dependency analysis functions to improve code maintainability.

## [0.6.0] (2025-04-02)

### Added

- Merged `dsbase` into `dsbin` since this was my last package still using it.

<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/dannystewart/dsbin/compare/v0.7.17...HEAD
[0.7.17]: https://github.com/dannystewart/dsbin/compare/v0.7.16...v0.7.17
[0.7.16]: https://github.com/dannystewart/dsbin/compare/v0.7.15...v0.7.16
[0.7.15]: https://github.com/dannystewart/dsbin/compare/v0.7.14...v0.7.15
[0.7.14]: https://github.com/dannystewart/dsbin/compare/v0.7.13...v0.7.14
[0.7.13]: https://github.com/dannystewart/dsbin/compare/v0.7.12...v0.7.13
[0.7.12]: https://github.com/dannystewart/dsbin/compare/v0.7.11...v0.7.12
[0.7.11]: https://github.com/dannystewart/dsbin/compare/v0.7.10...v0.7.11
[0.7.10]: https://github.com/dannystewart/dsbin/compare/v0.7.9...v0.7.10
[0.7.9]: https://github.com/dannystewart/dsbin/compare/v0.7.8...v0.7.9
[0.7.8]: https://github.com/dannystewart/dsbin/compare/v0.7.7...v0.7.8
[0.7.7]: https://github.com/dannystewart/dsbin/compare/v0.7.6...v0.7.7
[0.7.6]: https://github.com/dannystewart/dsbin/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/dannystewart/dsbin/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/dannystewart/dsbin/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/dannystewart/dsbin/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/dannystewart/dsbin/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/dannystewart/dsbin/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/dannystewart/dsbin/compare/v0.6.8...v0.7.0
[0.6.8]: https://github.com/dannystewart/dsbin/compare/v0.6.7...v0.6.8
[0.6.7]: https://github.com/dannystewart/dsbin/compare/v0.6.6...v0.6.7
[0.6.6]: https://github.com/dannystewart/dsbin/compare/v0.6.5...v0.6.6
[0.6.5]: https://github.com/dannystewart/dsbin/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/dannystewart/dsbin/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/dannystewart/dsbin/compare/v0.6.1...v0.6.3
[0.6.1]: https://github.com/dannystewart/dsbin/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dannystewart/dsbin/releases/tag/v0.6.0
