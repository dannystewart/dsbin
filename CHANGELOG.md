# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

## [0.6.8] - 2025-04-04

### Fixed

- Fixes a duplicate entry for `parseutil` in the `PACKAGES` list of `repo_run.py`.

## [0.6.7] - 2025-04-04

### Added

- Implements dynamic repository name generation for changelog links.

### Changed

- Updates `pyproject.toml` to include classifiers for improved package metadata.

## [0.6.6] - 2025-04-03

### Fixed

- Fixes incorrect post-release version string to use `post0` in `VersionHelper`.
- Fixes incorrect module path in the `repo-run` entry of `pyproject.toml`.
- Corrects the `repo-run` description in the README.
- Updates license to LGPL as it was intended to be.

## [0.6.5] - 2025-04-03

### Added

- Adds `changelog` script to automate changelog updates and version management.
- Adds Git repository check and pre-commit hook handling to `ConfigManager`.

### Changed

- Renames the package management utility for managing multiple Poetry projects from `updatedeps` to `repo-run`.
- Updates documentation to include a description for `codeconfigs` in README and initialization files.
- Updates README to improve style by adding a newline after the category header in content generation.

## [0.6.4] - 2025-04-03

### Fixed

- Updates color formatting to use `style` instead of `attrs` for `parseutil` update.
- Simplify package name extraction to fix the documentation generation process.

## [0.6.3] - 2025-04-03

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

## [0.6.1] - 2025-04-03

### Changed

- Replaces `textparse` and `timecapsule` libraries with `parseutil` for streamlined parsing functionality.
- Updates all remaining references from `dsbase` to `dsbin` to ensure consistency across the codebase.

### Internal

- Refactors `package_analyzer` by updating type hints for dependency analysis functions to improve code maintainability.

## [0.6.0] - 2025-04-02

### Added

- Merged `dsbase` into `dsbin` since this was my last package still using it.

<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/dannystewart/dsbin/compare/v0.6.8...HEAD
[0.6.8]: https://github.com/dannystewart/dsbin/compare/v0.6.7...v0.6.8
[0.6.7]: https://github.com/dannystewart/dsbin/compare/v0.6.6...v0.6.7
[0.6.6]: https://github.com/dannystewart/dsbin/compare/v0.6.5...v0.6.6
[0.6.5]: https://github.com/dannystewart/dsbin/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/dannystewart/dsbin/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/dannystewart/dsbin/compare/v0.6.1...v0.6.3
[0.6.1]: https://github.com/dannystewart/dsbin/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dannystewart/dsbin/releases/tag/v0.6.0
