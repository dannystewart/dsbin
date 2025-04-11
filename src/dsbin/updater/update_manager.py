from __future__ import annotations

import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from polykit.cli import handle_interrupt

from .shell_handler import ShellHandler

if TYPE_CHECKING:
    from logging import Logger

    from .privilege_helper import PrivilegeHelper
    from .updater import Updater


@dataclass
class UpdateStage:
    """Represents a stage in the update process.

    Attributes:
        command: The command to run for this stage.
        start_message: The message to display before this stage begins. If None, skip it.
        end_message: The message to display after this stage completes. If None, skip it.
        error_message: The message to display if this stage fails. If None, skip it.
        requires_sudo: Whether this stage requires sudo to run.
        capture_output: If True, capture command output for processing, which will skip logging.
        filter_output: If true, filter output for specific phrases. NOTE: Loses color output.
        raise_error: If True, raise errors to allow for special handling. NOTE: Captures output.
    """

    command: str
    start_message: str | None = None
    end_message: str | None = None
    error_message: str | None = None
    requires_sudo: bool = False
    capture_output: bool = False
    filter_output: bool = False
    raise_error: bool = False

    def __post_init__(self):
        # Windows doesn't support pexpect properly, so we can't do much with output
        if platform.system() == "Windows":
            self.requires_sudo = False
            self.capture_output = False
            self.filter_output = False

        # Output must be captured to raise errors
        if self.raise_error:
            self.capture_output = True


@dataclass
class UpdateManager(ABC):
    """Abstract base class for a package manager.

    Attributes:
        updater: The Updater instance that this UpdateManager belongs to.
        display_name: The display name that will be used at the start of this updater's log output.
        description: The description that appears when using `-l` or `--list` from the command line.
        prerequisite: Updater will only be included in the run if this command is found.
        requires_sudo: Whether this updater may require sudo at any point during its run.
        start_message: The message to log before the update process begins. If None, skip it.
        end_message: The message to log after the update process completes. If None, skip it.
        error_message: The message to log if an error occurs during the update process.
        skip_auto_add: If True, this updater requires special handling and will not be added to the
            run automatically during dynamic discovery.
        sort_order: Optional value to adjust this updater's run order (set higher to run later).
        update_successful: This is automatically set to True if the update was successful.
        system_updater: If True, this updater is considered OS-level rather than third-party.
        update_stages: List of UpdateStage instances with update commands, defined in subclasses.
    """

    updater: Updater

    display_name: str
    description: str
    prerequisite: str | None = None
    requires_sudo: bool = False

    start_message: str | None = None
    end_message: str | None = None
    error_message: str | None = "Update failed: %s"

    sort_order: int = 0
    skip_auto_add: bool = False
    update_successful: bool = field(default=False, init=False)

    system_updater: ClassVar[bool] = False
    update_stages: ClassVar[dict[str, UpdateStage]] = {}

    def __post_init__(self) -> None:
        self.logger: Logger = self.updater.logger
        self.debug: bool = self.updater.debug
        self.privileges: PrivilegeHelper = self.updater.privileges
        self.shell: ShellHandler = ShellHandler(self.updater)

    @handle_interrupt()
    def update(self) -> None:
        """Run the requested updates. This is a wrapper for perform_update_stages with start and end
        messages, as well as consistent handling for various exceptions and error conditions.
        """
        if self.start_message:
            self.logger.info("[%s] %s", self.display_name, self.start_message)

        try:
            self.perform_update_stages()
            self.update_successful = True
            if self.end_message:
                self.logger.info("[%s] %s", self.display_name, self.end_message)

        except SudoNotAvailableError:
            self._handle_sudo_not_available()

        except Exception as e:
            if self.error_message:
                self.logger.error("[%s] %s", self.display_name, self.error_message % str(e))
            self.update_successful = False

    @handle_interrupt()
    @abstractmethod
    def perform_update_stages(self) -> None:
        """Perform the stages needed to complete the update process."""
        raise NotImplementedError

    @handle_interrupt()
    def run_stage(
        self,
        stage_name: str,
        capture_output: bool = False,
        filter_output: bool | None = None,
        raise_error: bool | None = None,
    ) -> tuple[bool, str | None]:
        """Run a package update stage. Supports capturing and filtering output, as well as raising
        errors as an UpdateStageFailedError if specified. Configuration for capture_output,
        filter_output, and raise_error are generally set at the UpdateStage level, but can be
        overridden for individual calls to run_stage.

        Args:
            stage_name: The name of the stage to run, as defined in the update_stages dictionary.
            capture_output: If True, captures the command output and returns it. Otherwise, prints
                the output to the console. If None, uses the value set in the UpdateStage.
            filter_output: If True, filters the command output to remove any lines that contain
                phrases defined in FILTER_PHRASES. If None, uses the value set in the UpdateStage.
            raise_error: If True, raises an exception if the command returns a non-zero exit code.
                If None, uses the value set in the UpdateStage.

        Raises:
            SudoNotAvailableError: If the stage requires sudo but it is not available.
            UpdateStageFailedError: If command returns non-zero exit code when raise_error=True.

        Returns:
            A tuple containing a boolean indicating whether the command was successful, and the
            output of the command if capture_output is True (otherwise None).
        """
        # Disable output processing on Windows
        if platform.system() == "Windows":
            capture_output = False
            filter_output = False

        # Identify the appropriate stage to be run and ensure it exists
        stage = self.update_stages.get(stage_name)
        if not stage:
            self.logger.error("[%s] Unknown stage: %s", self.display_name, stage_name)
            return False, None

        # If sudo is required but not available, we can't proceed further
        if self.requires_sudo and not self.privileges.has_sudo:
            raise SudoNotAvailableError

        if stage.start_message:  # Show the start message if there is one
            self.logger.info("[%s] %s", self.display_name, stage.start_message)

        # Run the shell command for the stage and handle output appropriately
        output, success = self.shell.run_shell_command(
            stage.command,
            sudo=stage.requires_sudo,
            capture_output=capture_output or stage.capture_output,
            filter_output=filter_output or stage.filter_output,
            raise_error=raise_error or stage.raise_error,
        )
        self.logger.debug("Command output: %s", output)

        if success and stage.end_message:  # Show the end message if present and successful
            self.logger.info("[%s] %s", self.display_name, stage.end_message)

        elif not success:
            # If we want to raise an error, do so now
            if (raise_error or stage.raise_error) and stage.error_message:
                error_message = self._append_output_to_error(stage.error_message, output)
                final_message = (
                    error_message % (output or "Unknown error.")
                    if "%s" in error_message
                    else error_message
                )
                raise UpdateStageFailedError(final_message)

            # Otherwise, log the error and proceed
            if stage.error_message:
                error_message = self._append_output_to_error(stage.error_message, output)

                self.logger.error(
                    "[%s] %s",
                    self.display_name,
                    error_message % (output or "Unknown error.")
                    if "%s" in error_message
                    else error_message,
                )

        return success, output

    def _append_output_to_error(self, error_message: str, output: str | None) -> str:
        """Append command output to an error message if it does not already contain %s."""
        if output and "%s" not in error_message:
            error_message = error_message.rstrip(".")
            return f"{error_message}: %s"
        return error_message

    def _handle_sudo_not_available(self) -> None:
        self.logger.warning(
            "[%s] Skipping operation because sudo privileges are required but not available.",
            self.display_name,
        )


class SudoNotAvailableError(Exception):
    """Exception for when sudo is needed but not available."""


class UpdateStageFailedError(Exception):
    """Exception for when an update stage fails to complete successfully."""
