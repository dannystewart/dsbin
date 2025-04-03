from __future__ import annotations

from typing import Any, TypeGuard, get_args


def is_literal(value: Any, literal_type: Any) -> TypeGuard[Any]:
    """Verify if a value is of a specific Literal type."""
    return value in get_args(literal_type)
