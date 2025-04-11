from __future__ import annotations

import contextlib
import platform
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from polykit.cli import handle_interrupt

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger


class PrivilegeHelper:
    """Helper class for checking and acquiring sudo privileges."""

    SUDO_REQUIRED_TEXT: ClassVar[str] = "Sudo is required for some operations."
    FORCE_SUDO_TEXT: ClassVar[str] = "Forcing sudo due to command-line argument."
    INSTALL_WRAPPER_TEXT: ClassVar[str] = (
        "Avoid unnecessary password prompts by using the Bash wrapper. "
        "Install with 'dsupdater-install' and then run 'updater' instead."
    )

    def __init__(self, args: Namespace | None, logger: Logger):
        """Initialize the PrivilegeHelper class."""
        self.logger: Logger = logger
        self.force_sudo = args.sudo if args else False
        self.check_sudo_only = args.check_sudo if args else False
        self.test_sudo_only = args.test_sudo if args else False

        self.needs_sudo = False
        self.has_sudo = False

    def handle_startup(self) -> None:
        """Handle sudo requirements on startup."""
        if platform.system() == "Windows":
            return

        if self.check_sudo_only:  # Exit and return whether sudo is needed
            self.return_whether_sudo_is_needed_then_exit()
        else:  # Otherwise check for sudo and run the updater
            self.check_for_sudo_in_active_shell()
            self.acquire_sudo_if_needed()

    def check_for_sudo_in_active_shell(self) -> None:
        """Check whether the script has sudo privileges in the active shell."""
        pipe = Path("/tmp/update_sudo_pipe")
        try:
            status = pipe.read_text().strip()

            if status == "sudo_available":
                self.has_sudo = True
                self.needs_sudo = True
            elif status == "sudo_unavailable":
                self.has_sudo = False
                self.needs_sudo = True
            else:  # 'sudo_not_needed'
                self.has_sudo = False
                self.needs_sudo = False

        except FileNotFoundError:
            if not self.force_sudo:
                self.logger.warning(self.INSTALL_WRAPPER_TEXT)
            self.needs_sudo = False

        # If sudo is forced, we need it regardless
        if self.force_sudo:
            self.needs_sudo = True
            if not self.has_sudo:
                # Check if we actually have sudo
                with contextlib.suppress(subprocess.CalledProcessError):
                    subprocess.run(["sudo", "-n", "true"], check=True, stderr=subprocess.DEVNULL)
                    self.has_sudo = True

        self.log_sudo_status()
        if self.test_sudo_only:
            self.return_whether_sudo_is_needed_then_exit(exit_ok=self.has_sudo)

    @handle_interrupt()
    def acquire_sudo_if_needed(self) -> None:
        """Acquire sudo privileges."""
        if self.has_sudo or not self.needs_sudo:
            return  # If we don't need sudo or already have it, we're good

        if not self.force_sudo:  # Inform user before acquiring (unless forced)
            self.logger.info(self.SUDO_REQUIRED_TEXT)

        try:  # If we don't have sudo privileges, try to acquire them
            subprocess.run(["sudo", "-v"], check=True)
            self.has_sudo = True  # Acquiring sudo worked
        except subprocess.CalledProcessError:
            self.has_sudo = False  # Acquiring sudo failed

        self.log_sudo_status()
        if self.test_sudo_only:
            self.return_whether_sudo_is_needed_then_exit(exit_ok=True)

    def log_sudo_status(self) -> None:
        """Log all sudo conditions currently in effect."""
        self.logger.debug(
            "Has sudo: %s, Needs sudo: %s, Forcing sudo: %s",
            self.has_sudo,
            self.needs_sudo,
            self.force_sudo,
        )

        if self.force_sudo:
            self.logger.info(self.FORCE_SUDO_TEXT)

        if self.needs_sudo and not self.force_sudo:
            self.logger.debug(self.SUDO_REQUIRED_TEXT)

    def return_whether_sudo_is_needed_then_exit(self, exit_ok: bool = False) -> None:
        """Return whether the script requires sudo privileges and then exit."""
        sys.exit(0 if self.needs_sudo or exit_ok else 1)
