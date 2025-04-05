from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from typing import TYPE_CHECKING, Any

import pexpect
from polykit.log.types import LogLevel
from polykit.shell import handle_interrupt

from .output_processor import OutputProcessor

if TYPE_CHECKING:
    from logging import Logger

    from .updater import Updater


class ShellHandler:
    """Helper class for shell interactions."""

    def __init__(self, updater: Updater):
        self.updater: Updater = updater
        self.logger: Logger = updater.logger
        self.debug: bool = updater.debug

    @handle_interrupt()
    def run_shell_command(
        self,
        command: str,
        sudo: bool = False,
        capture_output: bool = False,
        filter_output: bool = False,
        raise_error: bool = False,
    ) -> tuple[str | None, bool]:
        """Run a shell command and return its output and success status.

        Args:
            command: The shell command to run.
            sudo: If True, run the command with sudo.
            capture_output: If True, capture the command output and return it. Otherwise, print the
                            output to the console.
            filter_output: If True, filter the command output to remove any lines that contain
                           phrases defined in FILTER_PHRASES.
            raise_error: If True, don't print the error to the log, since it will be raised.

        Returns:
            A tuple containing the output of the command (if capture_output is True) and a boolean
            indicating whether the command was successful.
        """
        self.logger.debug("Running shell command: %s", command)
        self.logger.debug("capture_output: %s, filter_output: %s", capture_output, filter_output)

        if platform.system() != "Windows" and sudo and os.geteuid() != 0:  # type: ignore
            self.updater.privileges.acquire_sudo_if_needed()
            command_parts = command.split("&&")
            command = " && ".join(f"sudo {part.strip()}" for part in command_parts)

        try:
            if platform.system() == "Windows" or (not capture_output and not filter_output):
                return self._run_simple_command(command)

            processor = OutputProcessor(
                logger=self.logger, filter_output=filter_output, capture_output=capture_output
            )
            return self._run_processed_command(command, processor)

        except Exception as e:
            if not raise_error:
                self.logger.error("Command failed: %s", str(e))
            return str(e), False

    def _run_simple_command(self, command: str) -> tuple[None, bool]:
        process = subprocess.Popen(
            command,
            shell=True,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        process.communicate()
        return None, process.returncode == 0

    def _run_processed_command(
        self, command: str, processor: OutputProcessor
    ) -> tuple[str | None, bool]:
        child = self._spawn_process(command)

        try:
            success = self._process_output(child, processor)
            return self._get_command_result(processor, success)
        except Exception as e:
            self.logger.debug("Command error: %s", str(e))
            return str(e), False

    def _spawn_process(self, command: str) -> pexpect.spawn[Any]:
        """Create and return a pexpect spawn instance."""
        return pexpect.spawn(
            "/bin/sh",
            ["-c", command],
            encoding="utf-8",
            maxread=1024,
        )

    def _process_output(self, child: pexpect.spawn[Any], processor: OutputProcessor) -> bool:
        """Process output from the child process, handling interactive prompts."""
        output_seen = False
        consecutive_timeouts = 0

        while True:
            try:
                if not self._handle_output(child, processor):
                    break

                output_seen = True
                consecutive_timeouts = 0
            except pexpect.TIMEOUT:
                consecutive_timeouts += 1
                if output_seen and consecutive_timeouts >= 2:
                    self._handle_interactive_prompt(child, processor)
                    break

            except Exception as e:
                self.logger.debug("pexpect error: %s", str(e))
                break

        child.close(force=True)
        return (child.exitstatus or 0) == 0

    def _handle_output(self, child: pexpect.spawn[Any], processor: OutputProcessor) -> bool:
        """Handle a single chunk of output. Returns True if output was processed."""
        index = child.expect(["\r\n", "\n", pexpect.EOF], timeout=0.5)

        if child.before:
            cleaned = processor.clean_control_sequences(child.before)
            processor.process_raw_output(cleaned, child.after, index == 2)  # type: ignore
            return True

        if index == 2:  # EOF
            self.logger.debug("EOF reached.")
            if processor.line_buffer.strip():
                processor.process_line(processor.line_buffer.strip())
            return False

        return True

    def _handle_interactive_prompt(
        self, child: pexpect.spawn[Any], processor: OutputProcessor
    ) -> None:
        """Handle an interactive prompt by switching to interactive mode."""
        self.logger.debug("Process appears to be waiting for input.")
        self.logger.debug("Process info - pid: %s, command: %s", child.pid, child.args)

        while True:
            try:
                current = self._read_interactive_output(child)
                if not current:
                    continue

                self.logger.debug("Raw interactive output: %r", current)
                cleaned = processor.clean_control_sequences(current)
                self.logger.debug("Cleaned interactive output: %r", cleaned)

                self._process_interactive_output(cleaned, processor)

            except pexpect.EOF:
                break
            except Exception as e:
                self.logger.debug("Interactive mode error: %s", str(e))
                break

    def _read_interactive_output(self, child: pexpect.spawn[Any]) -> str | None:
        """Read output from an interactive process."""
        try:
            # Increase buffer size and timeout to try to get complete lines
            output = child.read_nonblocking(size=4096, timeout=0.5)
            return output.decode("utf-8") if isinstance(output, bytes) else output
        except pexpect.TIMEOUT:
            return None

    def _process_interactive_output(self, cleaned: str, processor: OutputProcessor) -> None:
        """Process and optionally filter interactive output."""
        # Only process complete lines
        lines = [line for line in cleaned.splitlines() if line.strip()]
        if not lines:
            return

        if processor.filter_output:
            for line in lines:
                processor.process_line(line)
        else:
            sys.stdout.write(cleaned)
            sys.stdout.flush()

    def _get_command_result(
        self, processor: OutputProcessor, success: bool
    ) -> tuple[str | None, bool]:
        """Get the final command result based on success and capture settings."""
        if processor.capture_output:
            return "\n".join(processor.output), success
        return None if success else processor.last_error, success

    def check_output_for_string(
        self,
        output: str | None,
        search_string: str,
        log_message: str,
        log_level: LogLevel = LogLevel.ERROR,
    ) -> bool:
        """Check command output to see if it contains a specified string. Used to handle specific
        conditions identified within the output of an updater.

        Args:
            output: The output of the command to check.
            search_string: The string to search for in the output.
            log_message: The message to log if the string is found.
            log_level: The log level to use for the message.

        Returns:
            True if the string is found in the output, False otherwise.
        """
        if not output:
            return False
        if re.search(search_string, output):
            getattr(self.logger, log_level)(log_message)
            return True
        return False
