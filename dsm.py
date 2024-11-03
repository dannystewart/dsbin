#!/usr/bin/env python3

"""
Consolidated music and audio scripts.

You can use either the full name or the shortcut as the command name.
For more information on each command, run `dsm <command> -h`.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass
from typing import Callable

from dsmusiclib import alacrity, awa, azmusic, bipclean, bounceprune, calc, filer, hpfilter, wpmusic
from dsutil.text import ColorName, color, print_colored


@dataclass
class Command:
    """Dataclass for a command handler and any associated metadata."""

    handler: Callable
    alias: str | list[str] | None = None
    description: str | None = None


class DSMusic:
    """Command router for the music and audio scripts."""

    def __init__(self) -> None:
        self.commands: dict = {
            "aif2wav": Command(
                lambda args: awa.main(["--to", "wav"] + args),
                "a2w",
                "Convert AIFF to WAV",
            ),
            "wav2aif": Command(
                lambda args: awa.main(["--to", "aif"] + args),
                "w2a",
                "Convert WAV to AIFF",
            ),
            "alacrity": Command(
                alacrity.ALACrity,
                "alac",
                "Convert to ALAC for archival",
            ),
            "bounceprune": Command(
                bounceprune.main,
                ["bp", "prune"],
                "Prune obsolete Logic bounces",
            ),
            "azmusic": Command(
                azmusic.main,
                "az",
                "Upload remixes to Azure",
            ),
            "bipclean": Command(
                bipclean.main,
                "bip",
                "Clean up Logic bounces-in-place",
            ),
            "calc": Command(
                calc.main,
                "calc",
                "Calculate time spent on project",
            ),
            "filer": Command(
                filer.main,
                "filer",
                "Sort into folders by suffix",
            ),
            "hpfilter": Command(
                hpfilter.main,
                "hp",
                "Apply a high-pass filter",
            ),
            "wpmusic": Command(
                wpmusic.WPMusic,
                "wp",
                "Upload remixes to WordPress",
            ),
        }

        self.aliases = {}
        for name, cmd in self.commands.items():
            for alias in self.get_aliases(cmd, as_list=True):
                self.aliases[alias] = name

    def get_aliases(
        self, cmd: Command, as_list: bool = False, color_name: ColorName | None = None
    ) -> str | list[str]:
        """
        Get aliases for a command.

        Args:
            cmd: The Command object.
            as_list: If True, return a list of aliases instead of a formatted string.
            color_name: Optional color name for coloring aliases.

        Returns:
            A formatted string of aliases or a list of aliases.
        """
        if not cmd.alias:
            return [] if as_list else ""

        aliases = [cmd.alias] if isinstance(cmd.alias, str) else cmd.alias

        if as_list:
            return aliases

        colored_aliases = [color(a, color_name) if color_name else a for a in aliases]
        return f" or {' or '.join(colored_aliases)}"

    def route_command(self, user_command: str, command_args: list[str]) -> None:
        """
        Resolve any aliases to their original command handler, then route the command and its
        arguments to the appropriate function or class method.

        Args:
            user_command: The command to execute.
            command_args: The arguments to pass to the command.
        """
        # Resolve any aliases
        user_command = self.aliases.get(user_command, user_command)

        # Check if the command is a function or a class and call it accordingly
        if user_command in self.commands:
            command = self.commands[user_command]
            if callable(command.handler):
                command.handler(command_args)
            else:
                instance = command.handler(command_args)
                instance.main()
        else:
            print(f"Unknown command: {color(user_command, "yellow")}")
            if close_matches := self.find_close_matches(user_command):
                print("Did you mean one of these?")
                for match in close_matches:
                    print(f"  {color(match, "green")}")
            else:
                print(f"Available commands: {', '.join(self.commands.keys())}")
            sys.exit(1)

    def find_close_matches(self, user_command: str, n: int = 3) -> list[str]:
        """Find the closest command matches to the user command with n being the max number of matches."""
        return difflib.get_close_matches(user_command, self.commands.keys(), n=n)

    def show_help_and_exit(self, user_command: str | None = None) -> None:
        """Print the docstring for the class or the module and then exit."""
        if user_command and user_command in self.commands:
            command = self.commands[user_command]
            print_colored(f"{user_command}: {command.handler.__doc__}", "blue")
        else:
            cmd_color: ColorName = "cyan"
            print("\nAvailable commands:")
            for name, cmd in self.commands.items():
                colored_name = color(name, cmd_color)
                aliases = self.get_aliases(cmd, color_name=cmd_color)
                description = f": {cmd.description}" if cmd.description else ""
                print(f"  dsm {colored_name}{aliases}{description}")
        sys.exit()

    def parse_arguments(self) -> argparse.Namespace:
        """
        Create an argument parser for the main script. Assume the first argument will always be the
        command, and subsequent arguments are what should be passed to the command.
        """
        parser = argparse.ArgumentParser(
            description="unified music handling tool",
            usage="dsm <command> [<args>] (-h|--help)",
        )
        parser.add_argument(
            "command",
            help="the command to execute",
            nargs="?",
        )
        return parser.parse_args(sys.argv[1:2])

    def main(self) -> None:
        """Run the selected command and pass through any arguments."""
        args = self.parse_arguments()

        # If a command is provided, pass the remaining args to it
        if args.command:
            if args.command not in ["-h", "--help"]:
                self.route_command(args.command, sys.argv[2:])
            else:
                self.route_command(args.command, ["-h"])
        else:
            self.show_help_and_exit()


if __name__ == "__main__":
    dsmusic = DSMusic()
    dsmusic.main()
