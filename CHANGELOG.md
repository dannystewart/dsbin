# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

## [0.6.2] - 2025-04-03

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
[unreleased]: https://github.com/dannystewart/dsbin/compare/v0.6.2...HEAD
[0.6.2]: https://github.com/dannystewart/dsbin/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/dannystewart/dsbin/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dannystewart/dsbin/releases/tag/v0.6.0
