"""Fixes encoding issues in CSV files."""

# ruff: noqa: RUF003

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path
from typing import ClassVar

import chardet
from polykit import PolyLog
from polykit.cli import handle_interrupt

logger = PolyLog.get_logger("csvfix")


class CSVEncodingFixer:
    """Fixes encoding issues in CSV files."""

    # Common problematic encodings and their fixes
    ENCODING_FIXES: ClassVar[dict[str, str]] = {
        "utf-8-sig": "utf-8",  # Remove BOM
        "cp1252": "utf-8",  # Windows-1252 to UTF-8
        "iso-8859-1": "utf-8",  # Latin-1 to UTF-8
        "macroman": "utf-8",  # Mac Roman to UTF-8
    }

    # Character replacements for common mangled characters
    CHARACTER_FIXES: ClassVar[dict[str, str]] = {
        # Common UTF-8 encoding issues when viewed as Windows-1252
        "\xe2\x80\x99": "'",  # Right single quotation mark (â€™)
        "\xe2\x80\x9c": '"',  # Left double quotation mark (â€œ)
        "\xe2\x80\x9d": '"',  # Right double quotation mark (â€)
        "\xe2\x80\x93": "–",  # En dash (â€")
        "\xe2\x80\x94": "—",  # Em dash (â€")
        "\xc2\xa0": " ",  # Non-breaking space (Â )
        "\xc2": "",  # Standalone combining character artifacts
        "\xe2\x80\xa6": "...",  # Horizontal ellipsis (â€¦)
        "\xc3\xa1": "á",  # á with combining characters (Ã¡)
        "\xc3\xa9": "é",  # é with combining characters (Ã©)
        "\xc3\xad": "í",  # í with combining characters (Ã­)
        "\xc3\xb3": "ó",  # ó with combining characters (Ã³)
        "\xc3\xba": "ú",  # ú with combining characters (Ãº)
        "\xc3\xb1": "ñ",  # ñ with combining characters (Ã±)
        "\xc3\xbc": "ü",  # ü with combining characters (Ã¼)
        "\xe2\x82\xac": "€",  # Euro symbol (â‚¬)
        "\xc2\xa3": "£",  # Pound symbol (Â£)
        "\xc2\xa5": "¥",  # Yen symbol (Â¥)
        "\xe2\x80\x98": "'",  # Left single quotation mark (â€˜)
        "\xe2\x80\xa2": "•",  # Bullet point (â€¢)
        "\xe2\x80\xb0": "‰",  # Per mille sign (â€°)
        "\u202f": " ",  # Narrow no-break space (common in time formats)
    }

    def detect_encoding(self, file_path: str) -> tuple[str, float]:
        """Detect the encoding of a file."""
        file_path_obj = Path(file_path)
        raw_data = file_path_obj.read_bytes()
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        confidence = result["confidence"]

        if confidence < 0.99:
            logger.info("Detected encoding: %s (%d%% confidence)", encoding, int(confidence * 100))
        return encoding or "utf-8", confidence

    def has_bom(self, file_path: str) -> bool:
        """Check if file has UTF-8 BOM."""
        file_path_obj = Path(file_path)
        return file_path_obj.read_bytes()[:3] == b"\xef\xbb\xbf"

    def read_file_content(self, file_path: str, encoding: str) -> str:
        """Read file content with specified encoding."""
        file_path_obj = Path(file_path)
        try:
            return file_path_obj.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            logger.error("Error reading with %s: %s", encoding, e)
            content = file_path_obj.read_text(encoding=encoding, errors="replace")
            logger.warning("Some characters were replaced due to encoding errors")
            return content

    def fix_characters(self, content: str) -> str:
        """Fix common character encoding issues."""
        fixed_content = content
        fixes_applied = []

        for bad_char, good_char in self.CHARACTER_FIXES.items():
            if bad_char in fixed_content:
                fixed_content = fixed_content.replace(bad_char, good_char)
                fixes_applied.append(f"'{bad_char}' → '{good_char}'")

        if fixes_applied:
            logger.info("Applied character fixes: %s", ", ".join(fixes_applied))

        return fixed_content

    def validate_csv(self, content: str) -> bool:
        """Validate that the content is valid CSV."""
        try:
            # Try to parse a sample of the CSV
            lines = content.split("\n")[:10]  # Check first 10 lines
            sample = "\n".join(lines)

            # Try different dialects
            for dialect in [csv.excel, csv.excel_tab, csv.unix_dialect]:
                try:
                    reader = csv.reader(sample.splitlines(), dialect=dialect)
                    list(reader)  # Try to read all rows
                    return True
                except csv.Error:
                    continue

            return False
        except Exception:
            return False

    def fix_file(self, input_path: str, output_path: str | None = None) -> bool:
        """Fix encoding issues in a CSV file."""
        input_file = Path(input_path)

        if not input_file.exists():
            logger.error("Error: File '%s' does not exist", input_path)
            return False

        logger.debug("Fixing %s...", input_path)

        # Detect current encoding
        detected_encoding, confidence = self.detect_encoding(input_path)

        if confidence < 0.7:
            logger.warning(
                "Warning: Low confidence in encoding detection (%d%%). Creating backup first.",
                int(confidence * 100),
            )
            # Create backup if low confidence
            backup_path = str(input_file.stem + "_backup" + input_file.suffix)
            shutil.copy2(input_path, backup_path)
            logger.info("Created backup file: %s", backup_path)

        output_path = output_path or input_path

        # Check for BOM
        has_bom = self.has_bom(input_path)
        if has_bom:
            logger.info("UTF-8 BOM detected and will be removed.")

        # Determine the encoding to use for reading
        read_encoding = detected_encoding
        if detected_encoding in self.ENCODING_FIXES:
            logger.info(
                "Will convert from %s to %s.",
                detected_encoding,
                self.ENCODING_FIXES[detected_encoding],
            )

        # Handle UTF-8 with BOM
        if has_bom or detected_encoding == "utf-8-sig":
            read_encoding = "utf-8-sig"

        try:
            # Read the file content
            content = self.read_file_content(input_path, read_encoding)

            # Fix character encoding issues
            fixed_content = self.fix_characters(content)

            # Validate the result
            if not self.validate_csv(fixed_content):
                logger.warning("Warning: The fixed content may not be valid CSV")

            # Write the fixed content
            output_file = Path(output_path)
            output_file.write_text(fixed_content, encoding="utf-8", newline="")

            logger.info("%s fixed successfully!", output_path)

            # Show file size comparison
            original_size = input_file.stat().st_size
            fixed_size = output_file.stat().st_size
            logger.debug("File size: %d → %d bytes", original_size, fixed_size)

            return True

        except Exception as e:
            logger.error("Error processing file: %s", str(e))
            return False


@handle_interrupt()
def main() -> int:
    """Main entry point for the CSV encoding fixer."""
    parser = argparse.ArgumentParser(
        description="Fix encoding issues in CSV files mangled by Excel or PowerShell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  csvfix data.csv                    # Fix in place (creates backup)
  csvfix data.csv fixed_data.csv     # Save to new file
  csvfix *.csv                       # Fix multiple files
        """,
    )

    parser.add_argument("input_files", nargs="+", help="input CSV file(s) to fix")
    parser.add_argument("-o", "--output", help="output file (only for single input file)")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")

    args = parser.parse_args()

    # Handle the case where output file is specified as second positional argument
    if len(args.input_files) == 2 and not args.output:
        # Assume second argument is output file
        input_file = args.input_files[0]
        output_file = args.input_files[1]
        args.input_files = [input_file]
        args.output = output_file
    elif len(args.input_files) > 1 and args.output:
        print("Error: Cannot specify output file when processing multiple input files")
        return 1

    fixer = CSVEncodingFixer()
    success_count = 0

    for input_file in args.input_files:
        try:
            if fixer.fix_file(input_file, args.output):
                success_count += 1
            else:
                logger.error("Failed to fix: %s", input_file)
        except Exception as e:
            logger.error("Unexpected error processing %s: %s", input_file, str(e))

    if len(args.input_files) > 1:
        logger.info(
            "Successfully processed %s of %s file%s!",
            success_count,
            len(args.input_files),
            "s" if success_count != 1 else "",
        )

    return 0 if success_count == len(args.input_files) else 1


if __name__ == "__main__":
    main()
