from __future__ import annotations

import functools
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from logician import Logician

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


def deprecated(reason: str = "") -> Callable[[T], T]:
    """Mark a function or class as deprecated by emitting a warning when used."""

    def decorator(obj: T) -> T:
        """Decorate a function or class with a warning message."""
        message = f"{obj.__name__} is deprecated and will be removed in the future. {reason}"  # type: ignore[attr-defined]
        if isinstance(obj, type):
            return _decorate_class(obj, message, DeprecationWarning)  # type: ignore[return-value]
        return _decorate_function(obj, message, DeprecationWarning)  # type: ignore[return-value]

    return decorator


def not_yet_implemented(reason: str = "") -> Callable[[T], T]:
    """Mark a function or class as not yet implemented by raising a NotImplementedError."""

    def decorator(obj: T) -> T:
        """Decorate a function or class with a warning message."""
        message = f"{obj.__name__} is not yet implemented and cannot be used. {reason}"  # type: ignore[attr-defined]
        if isinstance(obj, type):
            return _decorate_class(obj, message, UserWarning)  # type: ignore[return-value]
        return _decorate_function(obj, message, UserWarning)  # type: ignore[return-value]

    return decorator


def _decorate_function(
    func: Callable[..., Any], message: str, category: type[Warning]
) -> Callable[..., Any]:
    """Decorate a function with a warning message and optional category."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Log a message and emit a warning."""
        frame = inspect.currentframe()
        frame_back = frame.f_back if frame is not None else None
        if frame is None or frame_back is None:
            return func(*args, **kwargs)

        filename = frame_back.f_code.co_filename
        line_num = frame_back.f_lineno
        function = frame_back.f_code.co_name

        _log_and_warn(message, category, filename, line_num, function)

        if category is UserWarning:
            raise NotImplementedError(message)
        return func(*args, **kwargs)

    return wrapper


def _decorate_class[T](cls: type[T], message: str, warn_type: type[Warning]) -> type[T]:
    """Decorate a class with a warning message and optional category."""

    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message and emit a warning."""
        frame = inspect.currentframe()
        frame_back = frame.f_back if frame is not None else None
        if frame is None or frame_back is None:
            orig_init(self, *args, **kwargs)
            return

        filename = frame_back.f_code.co_filename
        line_num = frame_back.f_lineno
        function = frame_back.f_code.co_name

        _log_and_warn(message, warn_type, filename, line_num, function)

        if warn_type is UserWarning:
            raise NotImplementedError(message)
        orig_init(self, *args, **kwargs)

    setattr(cls, "__init__", new_init)
    return cls


def _log_and_warn(
    message: str,
    warn_type: type[Warning],
    filename: str | None = None,
    line_num: int | None = None,
    function: str | None = None,
) -> None:
    """Log a message and emit a warning using Logician."""

    # Create a context-aware message with location information
    short_name = Path(filename).name if filename else "unknown"
    location = f"{short_name}:{line_num} in {function}" if filename and line_num else ""

    # Create a logger and log the warning
    logger = Logician.get_logger(simple=True)
    log_level = logging.WARNING if warn_type is DeprecationWarning else logging.ERROR
    logger.log(log_level, "%s (%s)", message, location)
