from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .filter_phrases import FILTER_PHRASES

if TYPE_CHECKING:
    from logging import Logger


@dataclass
class OutputProcessor:
    """Helper class for processing command output."""

    logger: Logger
    filter_output: bool = False
    capture_output: bool = False
    output: list[str] = field(default_factory=list)
    line_buffer: str = ""
    last_error: str = ""

    @staticmethod
    def clean_control_sequences(text: str) -> str:
        """Clean terminal control sequences."""
        patterns = [
            r"\x1b\[\?[0-9;]*[a-zA-Z]",  # Terminal mode sequences
            r"\x1b\[[0-9;]*[a-zA-Z]",  # CSI sequences
            r"\x1b\][^\x07\x1b]*[\x07\x1b\\]",  # OSC sequences
            r"\x1b[()][AB012]",  # Other escape sequences
            r"\x1b[^a-zA-Z]*[a-zA-Z]",  # Catch any other escape sequences
            r"[^\x08]\x08",  # Single backspace sequences
            r"\x08 \x08.",  # Spinner backspace sequences
        ]

        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned)

        # Clean up any remaining backspaces at the start
        return cleaned.lstrip("\x08")

    def process_line(self, line: str) -> None:
        """Process a single line of output."""
        if not line.strip():
            return

        if any(  # Store potential error messages
            error_indicator in line.lower()
            for error_indicator in ["error:", "fatal:", "failed", "exit status"]
        ):
            self.last_error = line

        if self.filter_output:
            if all(phrase not in line for phrase in FILTER_PHRASES):
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
        elif self.capture_output:
            self.output.append(line)
        else:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    def process_raw_output(self, before: str, after: str, is_eof: bool) -> None:
        """Process raw output from a pexpect child process."""
        self.logger.debug("Raw output: %r", before)
        self.logger.debug("Raw match: %r", after)

        cleaned = self.clean_control_sequences(before)
        self.logger.debug("Final output: %r", cleaned)

        self.line_buffer += cleaned

        if is_eof or after in {"\r\n", "\n"}:
            line = self.line_buffer.strip()
            self.line_buffer = ""
            if line:
                self.process_line(line)

    def process_timeout_buffer(self) -> None:
        """Process any remaining buffer when a timeout occurs."""
        if "\n" in self.line_buffer:
            lines = self.line_buffer.split("\n")
            self.line_buffer = lines[-1]  # Keep the last partial line
            for line in lines[:-1]:  # Process complete lines
                if line.strip():
                    self.logger.debug("Processing buffered line: %r", line)
                    self.process_line(line)
