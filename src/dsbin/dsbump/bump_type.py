from __future__ import annotations

from enum import StrEnum
from functools import total_ordering


@total_ordering
class BumpType(StrEnum):
    """Version bump types following PEP 440.

    Progression:
    - Pre-release: dev -> alpha -> beta -> rc
    - Release: patch -> minor -> major
    - Post-release: post (only after final release)
    """

    DEV = "dev"
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    POST = "post"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

    @property
    def is_prerelease(self) -> bool:
        """Whether this is a pre-release version type."""
        return self in {self.DEV, self.ALPHA, self.BETA, self.RC}

    @property
    def is_release(self) -> bool:
        """Whether this is a regular release version type."""
        return self in {self.PATCH, self.MINOR, self.MAJOR}

    @property
    def version_suffix(self) -> str:
        """Get the suffix used in version strings."""
        match self:
            case self.DEV:
                return ".dev"
            case self.ALPHA:
                return "a"
            case self.BETA:
                return "b"
            case self.RC:
                return "rc"
            case self.POST:
                return ".post"
            case _:
                return ""

    def sort_value(self) -> int:
        """Get numeric sort value for comparison."""
        order = {
            self.DEV: -1,
            self.ALPHA: 0,
            self.BETA: 1,
            self.RC: 2,
            self.POST: 10,
            self.PATCH: 3,
            self.MINOR: 4,
            self.MAJOR: 5,
        }
        return order[self]

    def __lt__(self, other: BumpType | str) -> bool:
        """Compare bump types for ordering."""
        try:
            other = BumpType(other)
        except ValueError:
            return NotImplemented
        return self.sort_value() < other.sort_value()

    def can_progress_to(self, other: BumpType) -> bool:
        """Check if this version type can progress to another."""
        # Can't go backwards in pre-release chain
        if self.is_prerelease and other.is_prerelease:
            return self.sort_value() < other.sort_value()

        # Can't add post-release to pre-release
        if self.is_prerelease and other == self.POST:
            return False

        # Can always go to a release version
        if other.is_release:
            return True

        # Can add post-release to release versions
        return bool(self.is_release and other == self.POST)
