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

from polykit.cli import PolyArgs, halo_progress
from polykit.core import polykit_setup
from polykit.log import PolyLog

if TYPE_CHECKING:
    import argparse

polykit_setup()

logger = PolyLog.get_logger(simple=True)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(
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
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace the original DMG file with the encrypted version",
    )
    args = parser.parse_args()

    if args.replace and args.output:
        parser.error("Cannot specify both --replace and --output.")

    return args


def encrypt_dmg(source_dmg: Path, output_dmg: Path, passphrase: str, replace: bool) -> None:
    """Create an encrypted copy of a DMG file.

    Args:
        source_dmg: Path to the source DMG file.
        output_dmg: Path where the encrypted DMG should be created.
        passphrase: Password for the encrypted DMG.
        replace: Whether the original DMG is being replaced. For logging only.

    Raises:
        subprocess.CalledProcessError: If a command fails.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        mount_point = temp_path / "mount"
        mount_point.mkdir()

        with halo_progress(
            source_dmg.name,
            start_message="Mounting DMG:",
            end_message="Mounted DMG:",
            fail_message="Failed to mount DMG:",
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
                output_dmg.name,
                start_message="Encrypting DMG:" if replace else "Creating encrypted DMG:",
                end_message="Encrypted DMG:" if replace else "Created encrypted DMG:",
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
                output_dmg.name if replace else source_dmg.name,
                start_message="Unmounting DMG:",
                end_message="Unmounted DMG:",
                fail_message="Failed to unmount DMG",
            ):
                subprocess.run(
                    ["hdiutil", "detach", mount_point, "-force"],
                    check=True,
                )


def get_password() -> str:
    """Get password securely.

    Raises:
        ValueError: If passwords do not match or are empty.
    """
    password = getpass.getpass("Enter password for encrypted DMG: ")
    verify = getpass.getpass("Verify password: ")

    if password != verify:
        msg = "Passwords do not match"
        raise ValueError(msg)

    if not password:
        msg = "Password cannot be empty"
        raise ValueError(msg)

    return password


def main() -> None:
    """Encrypt a DMG file."""
    try:
        args = parse_arguments()
        source_dmg = Path(args.dmg_file)

        if not source_dmg.exists():
            logger.error("DMG file not found: %s", source_dmg)
            return

        if args.replace:
            logger.info("Replacing original DMG with encrypted version.")

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

        password = get_password()
        encrypt_dmg(source_dmg, output_dmg, password, args.replace)
        logger.info("Successfully created encrypted DMG: %s", output_dmg.name)

        if args.replace:
            source_dmg.unlink()
            output_dmg.rename(source_dmg)
            logger.info("Replaced DMG with encrypted version: %s", source_dmg.name)

    except KeyboardInterrupt:
        logger.error("Process interrupted by user.")
    except Exception as e:
        logger.error("An error occurred: %s", str(e))


if __name__ == "__main__":
    main()
