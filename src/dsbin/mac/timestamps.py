#!/usr/bin/env python3

"""Quick and easy timestamp getting/setting for macOS.

If only a filename is specified, it will print the timestamps for that file. If a -c/--creation
and/or -m/--modification argument is provided, it will set those timestamps. If only one timestamp
is specified, the other will be left unchanged. Timestamps can be copied from the output and used to
set with -c/--creation and/or -m/--modification.

It supports a --copy argument, in conjunction with --from and --to, that will copy the timestamps
directly from one file to another. It also supports copying timestamps for entire directories with
--src-dir and --dest-dir. It will only copy timestamps for files that have identical names (minus
extension) in the source and destination directories.

Usage for getting timestamps:
    timestamps file.txt

    Example output:
        Creation time: 11/18/2023 21:35:33
        Modification time: 11/18/2023 21:36:59

Usage for setting timestamps:
    timestamps file.txt -c "11/18/2023 21:35:33"
    timestamps file.txt -m "11/18/2023 21:36:59"
    timestamps file.txt -c "11/18/2023 21:35:33" -m "11/18/2023 21:36:59"

Usage for copying timestamps:
    timestamps --copy-from file1.txt --copy-to file2.txt

Usage for copying timestamps for directories:
    timestamps --src-dir ./folder1 --dest-dir ./folder2
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import PolyArgs
from polykit.core import polykit_setup
from polykit.files import PolyFile
from polykit.formatters import color

if TYPE_CHECKING:
    import argparse

    from polykit.formatters.types import TextColor

polykit_setup()


def set_times(
    file: Path,
    ctime: str | None = None,
    mtime: str | None = None,
    ctime_to_mtime: bool = False,
    mtime_to_ctime: bool = False,
) -> None:
    """Set one or both specified timestamps on the specified file.

    Args:
        file: The file to set timestamps for.
        ctime: The creation timestamp to set.
        mtime: The modification timestamp to set.
        ctime_to_mtime: Copy creation time to modification time.
        mtime_to_ctime: Copy modification time to creation time.

    Raises:
        ValueError: If both ctime_to_mtime and mtime_to_ctime are specified.
    """
    if ctime_to_mtime and mtime_to_ctime:
        msg = "You cannot copy creation time and modification time to each other."
        raise ValueError(msg)
    if ctime_to_mtime or mtime_to_ctime:
        current_ctime, current_mtime = PolyFile.get_timestamps(file)
    if mtime_to_ctime:
        ctime = current_mtime
    if ctime_to_mtime:
        mtime = current_ctime

    get_times(file, "Old timestamps", "yellow")
    PolyFile.set_timestamps(file, ctime=ctime, mtime=mtime)
    get_times(file, "New timestamps", "green")


def get_times(
    file: Path,
    message: str = "File timestamps",
    color_name: TextColor = "yellow",
    ctime: str | None = None,
    mtime: str | None = None,
) -> None:
    """Get and print timestamps for the specified file with a given message and color.

    If you supply a ctime and mtime as arguments, it will just print with those times instead of
    checking the file.

    Args:
        file: The file to get timestamps for.
        message: The message to display.
        color_name: The color for the message.
        ctime: The creation timestamp to display if you just want to print it.
        mtime: The modification timestamp to display if you just want to print it.

    Raises:
        ValueError: If only one of ctime or mtime is specified.
    """
    if not ctime and not mtime:
        ctime, mtime = PolyFile.get_timestamps(file)
    if not ctime or not mtime:
        msg = "You must specify both a creation and modification time or neither."
        raise ValueError(msg)

    print(color(f"\n{message} for {file}:", color_name))
    print(color("  Creation time:", color_name), ctime)
    print(color("  Modification time:", color_name), mtime)


def copy_times(from_file: Path, to_file: Path) -> None:
    """Copy timestamps from one file to another.

    Args:
        from_file: The file to copy timestamps from.
        to_file: The file to copy timestamps to.
    """
    ctime, mtime = PolyFile.get_timestamps(from_file)
    PolyFile.set_timestamps(to_file, ctime=ctime, mtime=mtime)
    get_times(from_file, f"Timestamps copied for {from_file}:", "green")


def copy_times_between_directories(src_dir: Path, dest_dir: Path) -> None:
    """Copy timestamps from files in a directory to matching files in another directory with
    identical names (minus extension).

    Args:
        src_dir: The source directory to copy timestamps from.
        dest_dir: The destination directory to copy timestamps to.
    """
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)

    for src_file in src_path.iterdir():
        if src_file.is_file():
            base_name = src_file.stem
            for dest_file in dest_path.iterdir():
                if dest_file.is_file() and dest_file.stem == base_name:
                    copy_times(src_file, dest_file)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the timestamp utility."""
    parser = PolyArgs(description=__doc__, lines=2)

    # Positional argument for the file
    parser.add_argument("file", help="File to get or set timestamps for", nargs="?")

    # Optional arguments for setting timestamps
    parser.add_argument("-c", "--creation", help="Creation timestamp to set", default=None)
    parser.add_argument("-m", "--modification", help="Modification timestamp to set", default=None)

    # Optional arguments for copying timestamps
    parser.add_argument(
        "--copy", help="Copy timestamps from one file to another", action="store_true"
    )
    parser.add_argument(
        "--copy-from", dest="from_file", help="Source file to copy timestamps from", default=None
    )
    parser.add_argument(
        "--copy-to", dest="to_file", help="Destination file to copy timestamps to", default=None
    )

    # Optional arguments for directory operations
    parser.add_argument(
        "--src-dir", help="Source directory for copying timestamps from", default=None
    )
    parser.add_argument(
        "--dest-dir", help="Destination directory for copying timestamps to", default=None
    )

    # Additional options
    parser.add_argument(
        "--ctime-to-mtime", help="Copy creation time to modification time", action="store_true"
    )
    parser.add_argument(
        "--mtime-to-ctime", help="Copy modification time to creation time", action="store_true"
    )

    return parser.parse_args()


def main() -> None:
    """Copy, set, or get file timestamps."""
    args = parse_arguments()

    if args.file:
        file = Path(args.file)

    if args.src_dir and args.dest_dir:
        copy_times_between_directories(args.src_dir, args.dest_dir)
    elif args.from_file and args.to_file:
        copy_times(args.from_file, args.to_file)
    elif args.from_file or args.to_file:
        print(color("Please specify a source and destination file for copying timestamps.", "red"))
        sys.exit(1)
    elif args.file is None:
        print(color("Please specify a file to get or set timestamps for.", "red"))
        sys.exit(1)
    elif (
        args.creation is not None
        or args.modification is not None
        or args.ctime_to_mtime
        or args.mtime_to_ctime
    ):
        set_times(
            file,
            ctime=args.creation,
            mtime=args.modification,
            ctime_to_mtime=args.ctime_to_mtime,
            mtime_to_ctime=args.mtime_to_ctime,
        )
    else:
        get_times(args.file)


if __name__ == "__main__":
    main()
