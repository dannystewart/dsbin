#!/usr/bin/env python3

"""Removes MP3 files if there is an AIFF or WAV file with the same name.

This script removes MP3 files if there is an AIFF or WAV file with the same name. Used for
cleaning up old Logic bounces, because MP3 sucks and if I still have the original bounce I
can get rid of the MP3 to save space (and people's ears).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from polykit.core import polykit_setup
from polykit.files import PolyFile

polykit_setup()


def delete_mp3(directory: Path, dry_run: bool = False) -> None:
    """Removes MP3 files if there is an AIFF or WAV file with the same name.

    Args:
        directory: The directory to search for MP3 files.
        dry_run: If True, will list the files that would be deleted without actually deleting them.
    """
    files = PolyFile()
    mp3_files = files.list(directory, extensions="mp3", recursive=True)

    files_to_delete = []
    for mp3_file in mp3_files:
        mp3_path = Path(mp3_file)
        base_path = mp3_path.with_suffix("")
        aif_file = base_path.with_suffix(".aif")
        wav_file = base_path.with_suffix(".wav")

        if aif_file.exists() or wav_file.exists():
            files_to_delete.append(mp3_file)

    files.delete(files_to_delete, dry_run=dry_run)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Remove MP3 files if there is an AIFF or WAV file with the same name."
    )
    parser.add_argument(
        "directory", nargs="?", default=".", help="directory to search for MP3 files"
    )
    parser.add_argument("--dry-run", action="store_true", help="list files without deleting them")

    args = parser.parse_args()
    directory = Path(args.directory)
    delete_mp3(directory, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
