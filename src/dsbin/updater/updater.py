#!/usr/bin/env python3

"""Comprehensive update installer for Linux and macOS."""

from __future__ import annotations

import inspect
import platform
import shutil
import time
from typing import TYPE_CHECKING

from polykit.cli import ArgParser
from polykit.core import polykit_setup
from polykit.formatters import Text, color, print_color
from polykit.log import Logician
from polykit.shell import handle_interrupt

from .privilege_helper import PrivilegeHelper
from .update_manager import UpdateManager
from .updaters.macos import MacOSSoftwareUpdate

if TYPE_CHECKING:
    from argparse import Namespace

polykit_setup()


class Updater:
    """Comprehensive update installer for Linux and macOS."""

    def __init__(self, args: Namespace | None = None) -> None:
        self.debug = args.debug if args else False
        self.logger = Logician.get_logger(level="debug" if self.debug else "info")

        # Start measuring total update time
        self.start_time = time.time()

        # Flag for whether anything has been updated during this run
        self.anything_updated = False

        # Initialize PrivilegeHelper and updater lists
        self.privileges = PrivilegeHelper(args, self.logger)
        self.system_updaters: list[UpdateManager] = []
        self.updaters: list[UpdateManager] = []
        self.updater_classes: list[type[UpdateManager]] = []

        # Get all available updaters
        self.discover_updaters()

        # If listing only, print the list and exit
        if args and args.list:
            self.list_updaters()
            return

        # Initialize updaters, then handle sudo
        self.initialize_updaters()
        self.privileges.handle_startup()

        if args and args.updater:
            # If an individual updater is specified, run that
            self.run_individual_updater(args.updater)
        else:
            # Handle system updaters
            self.run_updater_list(self.system_updaters)
            self.run_softwareupdate_on_macos()

            # Handle remaining updaters and log completion status
            self.run_updater_list(self.updaters)
            self._log_completion_status()

    def discover_updaters(self) -> None:
        """Dynamically discover all updater classes."""
        if platform.system() == "Windows":
            self.logger.warning("Output filtering is not supported on Windows.")

        self.updater_classes = []

        # Import all modules from updaters package
        from . import updaters

        # Get all modules in the updaters package
        for module_name in dir(updaters):
            module = getattr(updaters, module_name)

            # Get all classes from each module
            for _, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, UpdateManager) and obj != UpdateManager:
                    self.updater_classes.append(obj)

    def list_updaters(self) -> None:
        """List all available updaters."""
        available, unavailable = self._get_updaters_by_availability()

        print_color("\nAvailable updaters:", "green")
        for updater_class in available:
            print(f"- {color(updater_class.display_name, 'green')}: {updater_class.description}")

        if unavailable:
            print("\n" + color("Additional updaters (unavailable on this system):", "grey"))
            for updater_class in unavailable:
                print(
                    f"- {color(updater_class.display_name, 'grey')}: "
                    f"{updater_class.description} (missing {updater_class.prerequisite})"
                )

        print("\nRun an individual updater with ", end="")
        print_color("`updater <name>`", "cyan")

    def initialize_updaters(self) -> None:
        """Initialize all updaters and add them to the appropriate update list."""
        system_updaters = []
        other_updaters = []

        for updater_class in sorted(self.updater_classes, key=lambda x: x.sort_order):
            if not updater_class.skip_auto_add:
                if updater_class.system_updater:
                    self.add_updater_to_run(updater_class, system_updaters)
                else:
                    self.add_updater_to_run(updater_class, other_updaters)

        self.system_updaters = system_updaters
        self.updaters = other_updaters

        # Check if any updaters require sudo
        self.privileges.needs_sudo = any(updater.requires_sudo for updater in self.system_updaters)

    def add_updater_to_run(
        self, updater_class: type[UpdateManager], updater_list: list[UpdateManager]
    ) -> None:
        """Add an updater to the list for this run if its prerequisite is met."""
        if updater_class.prerequisite is None or shutil.which(updater_class.prerequisite):
            updater = self._create_updater(updater_class)

            # Check instance-specific skip_auto_add
            if not updater.skip_auto_add:
                updater_list.append(updater)

    @handle_interrupt()
    def run_updater_list(self, updater_list: list[UpdateManager]) -> None:
        """Run the provided list of updaters."""
        for updater in updater_list:
            updater.update()

            if updater.update_successful:
                self.anything_updated = True

    @handle_interrupt()
    def run_individual_updater(self, updater_name: str) -> None:
        """Run a specific individual updater by name."""
        for updater_class in self.updater_classes:
            if updater_class.display_name.lower() == updater_name.lower():
                updater = self._create_updater(updater_class)

                # Import all modules from updaters package
                from . import updaters

                if issubclass(updater_class, updaters.MacOSSoftwareUpdate):
                    self.run_softwareupdate_on_macos(manual=True)
                    return

                if updater.prerequisite is None or shutil.which(updater.prerequisite):
                    updater.update()
                    if updater.update_successful:
                        self.logger.info("[%s] Update complete!", updater.display_name)
                    return

                self.logger.error(
                    "Prerequisite command '%s' not found for updater '%s'.",
                    updater_class.prerequisite,
                    updater_name,
                )
                return
        self.logger.error("Updater '%s' not found.", updater_name)

    @handle_interrupt()
    def run_softwareupdate_on_macos(self, manual: bool = False) -> None:
        """Handle softwareupdate on macOS separately."""
        if platform.system() == "Darwin" and shutil.which("softwareupdate"):
            macos_updater = MacOSSoftwareUpdate(self)

            # Force install all available updates if requested manually
            if manual:
                macos_updater.force_install_now()

            # Otherwise run in the background, if we've got sudo
            elif self.privileges.has_sudo:
                macos_updater.update()

            self.anything_updated = True

    def _get_updaters_by_availability(
        self,
    ) -> tuple[list[type[UpdateManager]], list[type[UpdateManager]]]:
        """Get updaters in available and unavailable lists based on prerequisite checks."""
        available = []
        unavailable = []

        for updater_class in sorted(self.updater_classes, key=lambda x: x.display_name.lower()):
            if self._check_updater_availability(updater_class):
                available.append(updater_class)
            else:
                unavailable.append(updater_class)

        return available, unavailable

    def _check_updater_availability(self, updater_class: type[UpdateManager]) -> bool:
        return (
            updater_class.prerequisite is None
            or shutil.which(updater_class.prerequisite) is not None
        )

    def _create_updater(self, updater_class: type[UpdateManager]) -> UpdateManager:
        """Create an updater instance from its class."""
        return updater_class(self)  # type: ignore

    def _get_elapsed_time(self) -> str:
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        return Text.format_duration(0, minutes, seconds)

    def _log_completion_status(self) -> None:
        if not self.anything_updated:
            self.logger.error("No updates were performed. Either OS or tools are not supported.")
        else:
            self.logger.info("All updates completed in %s!", self._get_elapsed_time())


def parse_arguments() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description="Update system packages and applications.", arg_width=26)
    parser.add_argument("--list", "-l", action="store_true", help="list all available updaters")
    parser.add_argument("--sudo", "-s", action="store_true", help="force sudo even if not needed")
    parser.add_argument("--debug", "-d", action="store_true", help="enable debug logging")
    parser.add_argument("--check-sudo", action="store_true", help="check if sudo is needed")
    parser.add_argument("--test-sudo", action="store_true", help="test sudo then exit")
    parser.add_argument("updater", nargs="?", help="run a specific updater")
    return parser.parse_args()


def main() -> None:
    """Main entry point for the updater script."""
    args = parse_arguments()
    Updater(args)


if __name__ == "__main__":
    main()
