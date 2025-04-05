# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

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
[unreleased]: https://github.com/dannystewart/dsbin/compare/v0.7.1...HEAD
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
