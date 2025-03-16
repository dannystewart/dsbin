#!/usr/bin/env python3

"""Quick and easy timestamp getting/setting for macOS.

If only a filename is specified, it will print the timestamps for that file. If a -c/--creation
and/or -m/--modification argument is provided, it will set those timestamps. If only one timestamp
is specified, the other will be left unchanged. Timestamps can be copied from the output and used to
set with -c/--creation and/or -m/--modification.

It supports a --copy argument, in conjunction with --from and --to, that will copy the timestamps
directly from one file to another. It also supports copying timestamps for entire directories with
--src-dir and --dst-dir. It will only copy timestamps for files that have identical names (minus
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
    timestamps --src-dir ./folder1 --dst-dir ./folder2
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase import configure_traceback
from dsbase.argparser import ArgParser
from dsbase.macos import get_timestamps, set_timestamps
from dsbase.shell import catch_errors
from dsbase.text import ColorName, color

if TYPE_CHECKING:
    import argparse

configure_traceback()


@catch_errors()
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
        current_ctime, current_mtime = get_timestamps(file)
    if mtime_to_ctime:
        ctime = current_mtime
    if ctime_to_mtime:
        mtime = current_ctime

    get_times(file, "Old timestamps", "yellow")
    set_timestamps(file, ctime=ctime, mtime=mtime)
    get_times(file, "New timestamps", "green")


@catch_errors()
def get_times(
    file: Path,
    message: str = "File timestamps",
    color_name: ColorName = "yellow",
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
        ctime, mtime = get_timestamps(file)
    if not ctime or not mtime:
        msg = "You must specify both a creation and modification time or neither."
        raise ValueError(msg)

    print(color(f"\n{message} for {file}:", color_name))
    print(color("  Creation time:", color_name), ctime)
    print(color("  Modification time:", color_name), mtime)


@catch_errors()
def copy_times(from_file: Path, to_file: Path) -> None:
    """Copy timestamps from one file to another.

    Args:
        from_file: The file to copy timestamps from.
        to_file: The file to copy timestamps to.
    """
    ctime, mtime = get_timestamps(from_file)
    set_timestamps(to_file, ctime=ctime, mtime=mtime)
    get_times(from_file, f"Timestamps copied for {from_file}:", "green")


@catch_errors()
def copy_times_between_directories(src_dir: Path, dst_dir: Path) -> None:
    """Copy timestamps from files in a directory to matching files in another directory with
    identical names (minus extension).

    Args:
        src_dir: The source directory to copy timestamps from.
        dst_dir: The destination directory to copy timestamps to.
    """
    src_path = Path(src_dir)
    dst_path = Path(dst_dir)

    for src_file in src_path.iterdir():
        if src_file.is_file():
            base_name = src_file.stem
            for dst_file in dst_path.iterdir():
                if dst_file.is_file() and dst_file.stem == base_name:
                    copy_times(str(src_file), str(dst_file))


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the timestamp utility."""
    parser = ArgParser(
        description="Get or set file timestamps on macOS, or copy them between files.",
        arg_width=30,
        max_width=120,
    )
    parser.add_argument("file", help="File to get or set timestamps for", nargs="?")
    parser.add_argument("creation", help="Creation timestamp to set", default=None)
    parser.add_argument("modification", help="Modification timestamp to set", default=None)
    parser.add_argument(
        "copy", help="Copy timestamps from one file to another", action="store_true"
    )
    parser.add_argument(
        "copy_from", help="Source file to copy timestamps from", default=None, dest="from_file"
    )
    parser.add_argument(
        "copy_to", help="Destination file to copy timestamps to", default=None, dest="to_file"
    )
    parser.add_argument(
        "src_dir", help="Source directory for copying timestamps from", default=None
    )
    parser.add_argument(
        "dst_dir", help="Destination directory for copying timestamps to", default=None
    )
    parser.add_argument(
        "ctime_to_mtime", help="Copy creation time to modification time", action="store_true"
    )
    parser.add_argument(
        "mtime_to_ctime", help="Copy modification time to creation time", action="store_true"
    )
    return parser.parse_args()


@catch_errors()
def main() -> None:
    """Copy, set, or get file timestamps."""
    args = parse_arguments()

    if args.file:
        file = Path(args.file)

    if args.src_dir and args.dst_dir:
        copy_times_between_directories(args.src_dir, args.dst_dir)
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
