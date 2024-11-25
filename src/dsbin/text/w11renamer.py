#!/usr/bin/env python3

"""
Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

Microsoft names files with a stupid incomprehensible meaningless name like
`22631.3007.240102-1451.23H2_NI_RELEASE_SVC_PROD1_CLIENTPRO_OEMRET_X64FRE_EN-US.ISO`, so
this turns that into `Win11_22631.3007_Pro_x64.iso` because it's not stupid.

You can enter it with or without `.iso`. It'll output without it for easier copying.
"""

from __future__ import annotations

import re
import sys

from dsutil.text import color


def destupify_filename(filename: str) -> str:
    """Turn a stupid Windows 11 ISO filename into a non-stupid one."""
    if filename.upper().endswith(".ISO"):
        filename = filename[:-4]

    segments = re.split(r"[._-]", filename)

    build = segments[0]
    revision = segments[1]

    arch = None
    for segment in segments:
        if "X64FRE" in segment.upper():
            arch = "x64"
            break
        if "ARM64FRE" in segment.upper() or "A64FRE" in segment.upper():
            arch = "ARM64"
            break

    return f"Win11_{build}.{revision}_Pro_{arch}"


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print(
            color("w11renamer: ", "green")
            + "turns stupid Windows 11 ISO names into non-stupid ones"
        )
        print(
            color("NOTE: ", "yellow")
            + "Doesn't actually rename, just outputs the name. Works with or without '.iso'."
        )
        print()
        print(
            color("Usage: ", "blue")
            + 'w11renamer "22631.3007.240102-1451.23H2_NI_RELEASE_SVC_PROD1_CLIENTPRO_OEMRET_X64FRE_EN-US.ISO"'
        )
        print(color("Outputs: ", "green") + "Win11_22631.3007_Pro_x64")
        return
    input_text = sys.argv[1]
    output_text = destupify_filename(input_text)
    print(output_text)


if __name__ == "__main__":
    main()
