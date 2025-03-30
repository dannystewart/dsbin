"""Version management tool for Python projects.

Handles version bumping, pre-releases, development versions, and git operations following PEP 440.
Supports major.minor.patch versioning with dev/alpha/beta/rc prerelease (and post-release) versions.

Usage:
    # Regular version bumping
    dsbump                # 1.2.3    -> 1.2.4
    dsbump minor          # 1.2.3    -> 1.3.0
    dsbump major          # 1.2.3    -> 2.0.0

    # Pre-release versions
    dsbump dev            # 1.2.3    -> 1.2.4.dev0
    dsbump alpha          # 1.2.3    -> 1.2.4a1
    dsbump beta           # 1.2.4a1  -> 1.2.4b1
    dsbump rc             # 1.2.4b1  -> 1.2.4rc1
    dsbump patch          # 1.2.4rc1 -> 1.2.4

    # Post-release version
    dsbump post           # 1.2.4    -> 1.2.4.post1

All operations include git tagging and pushing changes to remote repository.
"""

from __future__ import annotations

from .main import PyBumper
