# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

### Changed

- Renamed `code-configs` script to `codeconfigs`.
- Added support for subdirectories, and added additional config files.

## [0.6.1] - 2025-04-03

### Changed

- Now using `parseutil` (new combined library) for text and time parsing.
- Renamed remaining references to `dsbase` to `dsbin`.

### Removed

- Removed `textparse` and `timecapsule` from dependencies.

## [0.6.0] - 2025-04-02

### Added

- Merged `dsbase` into `dsbin` since this was my last package still using it.

<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/dannystewart/dsbin/compare/v0.6.1...HEAD
[0.6.1]: https://github.com/dannystewart/dsbin/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dannystewart/dsbin/releases/tag/v0.6.0
