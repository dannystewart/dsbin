from __future__ import annotations

import sys
import traceback
import types

try:
    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers import PythonTracebackLexer

    pygments_available = True
except ImportError:
    pygments_available = False

# Type alias for exception info tuple
type ExcInfo = tuple[type[BaseException], BaseException, types.TracebackType | None]


def log_traceback(exc_info: ExcInfo | None = None, trim_levels: int = 0) -> None:
    """Log a traceback, optionally trimming unwanted levels."""
    # Unpack traceback info
    exc_type, exc_value, exc_traceback = exc_info or sys.exc_info()

    # Trim traceback to set number of levels
    for _ in range(trim_levels):
        if exc_traceback is not None:
            exc_traceback = exc_traceback.tb_next

    # Log traceback and exception details
    if exc_value is not None and exc_traceback is not None:
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb = "".join(tb_list)
        if pygments_available:
            tb = highlight(tb, PythonTracebackLexer(), TerminalFormatter())
        else:
            print("Can't colorize traceback because Pygments is not installed.")
        sys.stderr.write(tb)
