#!/usr/bin/env python3

"""
Removes MP3 files if there is an AIFF or WAV file with the same name.

This script removes MP3 files if there is an AIFF or WAV file with the same name. Used for
cleaning up old Logic bounces, because MP3 sucks and if I still have the original bounce I
can get rid of the MP3 to save space (and people's ears).
"""

import argparse
import os
from dsutil.files import list_files, delete_files


def delete_mp3(directory: str, dry_run: bool = False) -> None:
    """
    Removes MP3 files if there is an AIFF or WAV file with the same name.

    Args:
        directory: The directory to search for MP3 files.
        dry_run: If True, will list the files that would be deleted without actually deleting them.
    """
    mp3_files = list_files(directory, extensions="mp3", recursive=True)

    files_to_delete = []
    for mp3_file in mp3_files:
        base_filename = os.path.splitext(mp3_file)[0]
        aif_file = f"{base_filename}.aif"
        wav_file = f"{base_filename}.wav"

        if os.path.exists(aif_file) or os.path.exists(wav_file):
            files_to_delete.append(mp3_file)

    delete_files(files_to_delete, dry_run=dry_run)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Remove MP3 files if there is an AIFF or WAV file with the same name."
    )
    parser.add_argument("directory", nargs="?", default=".", help="Directory to search for MP3 files.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be deleted without actually deleting them.",
    )

    args = parser.parse_args()

    delete_mp3(args.directory, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
