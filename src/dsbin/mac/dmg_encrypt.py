#!/usr/bin/env python3

"""Encrypts DMG files with AES-256 encryption.

Creates an encrypted copy of a DMG file, preserving all contents and metadata. The encrypted
copy is created alongside the original by default, with '_encrypted' appended to the filename.

Examples:
    dmg-encrypt archive.dmg                 # Creates 'archive_encrypted.dmg'
    dmg-encrypt -o secure.dmg archive.dmg   # Creates 'secure.dmg'
"""

from __future__ import annotations

import getpass
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from dsutil import LocalLogger, configure_traceback
from dsutil.argparser import ArgParser
from dsutil.progress import halo_progress

if TYPE_CHECKING:
    import argparse

configure_traceback()
logger = LocalLogger().get_logger(simple=True)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(
        description="Creates an encrypted copy of an existing DMG file.",
        arg_width=32,
    )
    parser.add_argument("dmg_file", help="DMG file to encrypt")
    parser.add_argument(
        "-o",
        "--output",
        help="output filename (default: adds '_encrypted' to original name)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite output file if it exists",
    )
    return parser.parse_args()


def encrypt_dmg(source_dmg: Path, output_dmg: Path, passphrase: str) -> None:
    """Create an encrypted copy of a DMG file.

    Args:
        source_dmg: Path to the source DMG file.
        output_dmg: Path where the encrypted DMG should be created.
        passphrase: Password for the encrypted DMG.

    Raises:
        subprocess.CalledProcessError: If a command fails.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        mount_point = temp_path / "mount"
        mount_point.mkdir()

        with halo_progress(
            filename=source_dmg.name,
            start_message="Mounting DMG",
            end_message="Mounted DMG",
            fail_message="Failed to mount DMG",
        ):
            subprocess.run(
                [
                    "hdiutil",
                    "attach",
                    source_dmg,
                    "-mountpoint",
                    mount_point,
                    "-nobrowse",
                ],
                check=True,
            )

        try:
            with halo_progress(
                filename=output_dmg.name,
                start_message="Creating encrypted DMG",
                end_message="Created encrypted DMG",
                fail_message="Failed to create encrypted DMG",
            ):
                # Create process with both stdin and stdout pipes
                process = subprocess.Popen(
                    [
                        "hdiutil",
                        "create",
                        "-fs",
                        "Case-sensitive APFS",
                        "-encryption",
                        "AES-256",
                        "-stdinpass",
                        "-srcfolder",
                        mount_point,
                        "-volname",
                        source_dmg.stem,
                        output_dmg,
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                # Send password without newline and wait for completion
                stdout, stderr = process.communicate(input=passphrase.encode())
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode, "hdiutil create", stdout, stderr
                    )

        finally:
            with halo_progress(
                filename=source_dmg.name,
                start_message="Unmounting DMG",
                end_message="Unmounted DMG",
                fail_message="Failed to unmount DMG",
            ):
                subprocess.run(
                    ["hdiutil", "detach", mount_point, "-force"],
                    check=True,
                )


def main() -> None:
    """Encrypt a DMG file."""
    try:
        args = parse_arguments()
        source_dmg = Path(args.dmg_file)

        if not source_dmg.exists():
            logger.error("DMG file not found: %s", source_dmg)
            return

        output_dmg = (
            Path(args.output)
            if args.output
            else source_dmg.with_stem(f"{source_dmg.stem}_encrypted")
        )

        if output_dmg.exists():
            if args.force:
                logger.warning("%s already exists; overwriting.", output_dmg.name)
                output_dmg.unlink()
            else:
                logger.error("Output file already exists: %s", output_dmg)
                return

        # Get password securely
        password = getpass.getpass("Enter password for encrypted DMG: ")
        verify = getpass.getpass("Verify password: ")

        if password != verify:
            logger.error("Passwords do not match.")
            return

        if not password:
            logger.error("Password cannot be empty.")
            return

        encrypt_dmg(source_dmg, output_dmg, password)
        logger.info("Successfully created encrypted DMG: %s", output_dmg.name)

    except KeyboardInterrupt:
        logger.error("Process interrupted by user.")
    except Exception as e:
        logger.error("An error occurred: %s", str(e))


if __name__ == "__main__":
    main()
