from __future__ import annotations

import subprocess
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from halo import Halo
from textparse import print_color

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable, Coroutine

T = TypeVar("T")
P = ParamSpec("P")


def with_retries[T](operation_func: Callable[..., T]) -> Callable[..., T]:
    """Retry operations with a spinner."""

    def wrapper(
        *args: Any,
        retries: int = 3,
        wait_time: float = 3,
        spinner: str | None = None,
        **kwargs: Any,
    ) -> T:
        last_exception = None
        for attempt in range(retries):
            try:
                if spinner:
                    with Halo(spinner, color="blue"):
                        return operation_func(*args, **kwargs)
                else:
                    return operation_func(*args, **kwargs)
            except subprocess.CalledProcessError as e:
                last_exception = e

                print_color(
                    f"Failed to complete: {operation_func.__name__}, retrying... ({attempt + 1} out of {retries})",
                    "yellow",
                )
                time.sleep(wait_time)
        msg = f"Operation failed after {retries} attempts: {operation_func.__name__}"
        raise RuntimeError(msg) from last_exception

    return wrapper


def retry_on_exception(
    exception_to_check: type[Exception],
    tries: int = 4,
    delay: int = 3,
    backoff: int = 2,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function if a specified exception occurs.

    Args:
        exception_to_check: The exception to check for retries.
        tries: Maximum number of retries.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to delay each retry.
        logger: Logger for logging retries. If None, print to stdout instead.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal tries, delay
            while tries > 1:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as e:
                    if logger:
                        logger.warning("%s. Retrying in %s seconds...", str(e), delay)
                    else:
                        print_color(f"{e}. Retrying in {delay} seconds...", "yellow")
                    time.sleep(delay)
                    tries -= 1
                    delay *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator


def async_retry_on_exception(
    exception_to_check: type[Exception],
    tries: int = 4,
    delay: float = 3,
    backoff: float = 2,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Retry a function if a specified exception occurs.

    Args:
        exception_to_check: The exception to check for retries.
        tries: Maximum number of retries.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to delay each retry.
        logger: Logger for logging retries. If None, print to stdout instead.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            """Wrap the function with retry logic."""
            nonlocal tries, delay
            while tries > 1:
                try:
                    return await func(*args, **kwargs)
                except exception_to_check as e:
                    if logger:
                        logger.warning("%s. Retrying in %s seconds...", str(e), delay)
                    else:
                        print_color(f"{e}. Retrying in {delay} seconds...", "yellow")
                    time.sleep(delay)
                    tries -= 1
                    delay *= backoff
            return await func(*args, **kwargs)

        return wrapper

    return decorator
