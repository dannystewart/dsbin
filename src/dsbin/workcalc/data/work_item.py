from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


@dataclass
class WorkItem:
    """Represents a single unit of work (commit, bounce, etc.)."""

    timestamp: datetime
    source_path: Path | None = None
    description: str | None = None
    metadata: dict[str, str | int | datetime] | None = None
