"""BounceParser is a utility for parsing and managing Logic bounces. It provides tools for parsing,
sorting, and grouping audio bounce files based on a specific naming convention.

It's designed to work with filenames in the following format:
    "Title YY.MM.DD_Version[MinorVersion][Suffix].extension"

Example:
    "My Song 24.5.1_0a No Vocals.wav"

Key Features:
- Parse bounce filenames into structured Bounce objects
- Find and parse all bounce files in a directory
- Sort bounces by various criteria
- Group bounces by title, date, version, and suffix
- Filter bounces by suffix or file format

Usage Examples:
- Find and parse all bounces in a directory, returning a list:
    bounces = BounceParser.find_bounces("/path/to/bounces")
- Get the latest bounce for each day:
    latest_bounces = BounceParser.get_latest_per_day("/path/to/bounces")
- Sort a list of bounces:
    sorted_bounces = BounceParser.sort_bounces(bounces)
- Group a list of bounces:
    grouped_bounces = BounceParser.group_bounces(bounces)
- Filter a list of bounces by suffix:
    no_vocals = BounceParser.filter_by_suffix("/path/to/bounces", "No Vocals")
- Filter a list of bounces by file format:
    wav_bounces = BounceParser.filter_by_format("/path/to/bounces", "wav")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from polykit.formatters import TZ
from polykit.log import Logician

from dsbin.files import FileManager


@dataclass
class Bounce:
    """Dataclass to store information about a bounce.

    Attributes:
        title: The title of the bounce.
        year: The year of the bounce (last two digits).
        month: The month of the bounce.
        day: The day of the bounce.
        version: The major version number of the bounce.
        minor_version: The minor version of the bounce (e.g., 'a', 'b', 'c').
        suffix: Any additional suffix in the filename (e.g., 'No Vocals').
        created_at: The creation timestamp of the file.
        modified_at: The last modification timestamp of the file.
        file_path: The full path to the bounce file.
        file_format: The file format (extension) of the bounce.

    Properties:
        date: Returns the full date of the bounce as a datetime object.
        full_version: Returns the full version string (e.g., '1a').
    """

    title: str
    year: int
    month: int
    day: int
    version: int
    minor_version: str
    suffix: str | None
    created_at: datetime
    modified_at: datetime
    file_path: Path
    file_format: str

    @property
    def date(self) -> datetime:
        """Return the date of the bounce as a datetime object."""
        return datetime(self.year + 2000, self.month, self.day, tzinfo=TZ)

    @property
    def full_version(self) -> str:
        """Return the full version string (e.g., '1a')."""
        return f"{self.version}{self.minor_version}"


class BounceParser:
    """Methods for parsing, finding, sorting, and grouping bounce files by naming convention."""

    BOUNCE_PATTERN = r"(.+) (\d{2})\.(\d{1,2})\.(\d{1,2})(?:_(\d+)([a-z]?))?(?: (.+))?"

    logger = Logician.get_logger()

    @classmethod
    def get_bounce(cls, file_path: Path) -> Bounce:
        """Parse a bounce filename and return a Bounce object.

        This method extracts information from the filename based on the expected pattern:
        "Title YY.MM.DD_Version[MinorVersion][Suffix].extension"

        Args:
            file_path: The path to the bounce file.

        Returns:
            A Bounce object containing parsed information from the filename.

        Raises:
            ValueError: If the filename doesn't match the expected pattern.

        Example:
            bounce = BounceParser.get_bounce("My Song 24.5.1_0a No Vocals.wav")

            # Result:
            # Bounce(
            #     title="My Song",
            #     year=24,
            #     month=5,
            #     day=1,
            #     version=0,
            #     minor_version="a",
            #     suffix="No Vocals",
            #     file_format="wav",
            #     ...
            # )

        Note:
            - If no minor version is present, it will be set to an empty string.
            - If no suffix is present, it will be set to None.
        """
        path = Path(file_path)
        filename = path.stem
        match = re.match(cls.BOUNCE_PATTERN, filename)

        if not match:
            msg = f"Invalid bounce filename format: {filename}"
            raise ValueError(msg)

        title, year, month, day, version, minor_version, suffix = match.groups()
        ctime, mtime = FileManager.get_timestamps(path)

        return Bounce(
            title=title,
            year=int(year),
            month=int(month),
            day=int(day),
            version=int(version) if version else 0,
            minor_version=minor_version or "",
            suffix=suffix,
            created_at=datetime.strptime(ctime, "%m/%d/%Y %H:%M:%S").replace(tzinfo=TZ),
            modified_at=datetime.strptime(mtime, "%m/%d/%Y %H:%M:%S").replace(tzinfo=TZ),
            file_path=path,
            file_format=path.suffix.lower()[1:],
        )

    @classmethod
    def find_bounces(cls, directory: Path, recursive: bool = False) -> list[Bounce]:
        """Find all bounce files in a directory and return a list of Bounce objects.

        This method searches the given directory for files that match the bounce filename pattern.

        Args:
            directory: The directory to search for bounce files.
            recursive: If True, search recursively through subdirectories. Defaults to False.

        Returns:
            A list of Bounce objects for all matching files in the directory.

        Example:
            # Non-recursive search
            bounces = BounceParser.find_bounces("/path/to/bounces")

            # Recursive search
            bounces_recursive = BounceParser.find_bounces("/path/to/bounces", recursive=True)

            # If the directory contains:
            # - /path/to/bounces/Song A 24.5.1_0.wav
            # - /path/to/bounces/Song A 24.5.1_1 No Vocals.wav
            # - /path/to/bounces/subdir/Song B 24.5.2_0.wav

            # Non-recursive search will return Bounce objects for the first two files.
            # Recursive search will return Bounce objects for all three files.

        Note:
            - This method will not return files that don't match the bounce filename pattern.
            - By default, only searches specified directory. Set recursive=True for subdirectories.
            - Be cautious when using recursive search in directories with many subdirectories, as it
                may be slower and include unwanted files.
        """
        path = Path(directory)
        glob_pattern = "**/*" if recursive else "*"
        bounce_files = []

        for file in path.glob(glob_pattern):
            if not file.is_file():
                continue
            if file.is_file() and re.match(cls.BOUNCE_PATTERN, file.stem):
                bounce_files.append(file)

        return [cls.get_bounce(file) for file in bounce_files]

    @classmethod
    def get_latest_bounce(cls, bounces: list[Bounce], include_suffixed: bool = False) -> Bounce:
        """Get the latest bounce from a list of bounces.

        "Latest" is determined by sorting the bounces and returning the last one. The sorting is
        done by title, date, version, and minor version.

        Args:
            bounces: A list of Bounce objects.
            include_suffixed: If False, only consider bounces without a suffix.

        Returns:
            The latest Bounce object from the list.

        Example:
            bounces = [
                Bounce(title="Song A", year=24, month=5, day=1, version=0, minor_version="", ...),
                Bounce(title="Song A", year=24, month=5, day=1, version=1, suffix="No Vocals", ...),
                Bounce(title="Song A", year=24, month=5, day=1, version=1, minor_version="", ...),
                Bounce(title="Song A", year=24, month=5, day=2, version=0, minor_version="", ...),
            ]
            latest = BounceParser.get_latest_bounce(bounces)
            # Result: Bounce object representing "Song A 24.5.2_0"

            latest_with_suffix = BounceParser.get_latest_bounce(bounces, include_suffixed=True)
            # Result: Same as above, since the latest bounce has no suffix.

        Note:
            If there are multiple bounces with the same latest date and version, the one with the
            latest minor version will be returned.

            If include_suffixed is False and there are no bounces without a suffix, this method will
            return the latest bounce regardless of suffix.
        """
        if not include_suffixed:
            # Filter out suffixed bounces, but keep all if that would leave nothing
            non_suffixed = [b for b in bounces if not b.suffix]
            if non_suffixed:
                bounces = non_suffixed

        return cls.sort_bounces(bounces)[-1]

    @classmethod
    def get_from_day(cls, directory: Path, year: int, month: int, day: int) -> list[Bounce]:
        """Get bounces from a specific day in the given directory.

        This method finds all bounce files in the directory and filters them to include only those
        from the specified date.

        Args:
            directory: The directory to search for bounce files.
            year: The year (last two digits, 00-99 for 2000-2099).
            month: The month (1-12).
            day: The day (1-31).

        Returns:
            A list of Bounce objects from the specified day, sorted by version and minor version.

        Example:
            day_bounces = BounceParser.get_from_day("/path/to/bounces", 24, 5, 1)

            # If the directory contains:
            # - Song A 24.5.1_0.wav
            # - Song A 24.5.1_1.wav
            # - Song B 24.5.1_0.wav
            # - Song C 24.5.2_0.wav

            # The result will be a list of Bounce objects for the first three files,
            # sorted by title, version, and minor version.

        Note:
            - The year should be given as the last two digits (e.g., 24 for 2024).
            - If no bounces are found for the specified day, an empty list is returned.
        """
        bounces = cls.find_bounces(directory)
        target_date = datetime(year + 2000, month, day, tzinfo=TZ)
        return [bounce for bounce in bounces if bounce.date == target_date]

    @classmethod
    def get_latest_per_day(cls, directory: Path, include_suffixed: bool = False) -> list[Bounce]:
        """Get the latest bounce per day from the given directory.

        This method considers the 'latest' bounce to be the one with the highest version number,
        regardless of the creation or modification time of the file. If there are multiple bounces
        with the same highest version number on a given day, it returns the one with the latest
        minor version (e.g., 'b' is considered later than 'a').

        Args:
            directory: The directory to search for bounce files.
            include_suffixed: If False, only consider bounces without a suffix.

        Returns:
            A list of the latest Bounce objects for each day, sorted by date.

        Example:
            Assume the directory contains:
            - Song A 24.05.15_0.wav
            - Song A 24.05.15_1.wav
            - Song A 24.05.15_1 No Vocals.wav
            - Song B 24.05.16_0.wav
            - Song B 24.05.16_1.wav
            - Song A 24.05.17_0.wav

            latest_per_day = BounceParser.get_latest_per_day("/path/to/bounces")

            # Result will be a list of Bounce objects:
            # [
            #     Bounce(title="Song A", year=24, month=5, day=1, version=1, minor_version="" ...),
            #     Bounce(title="Song B", year=24, month=5, day=2, version=1, minor_version="" ...),
            #     Bounce(title="Song A", year=24, month=5, day=3, version=0, minor_version="" ...)
            # ]

        Note:
            If include_suffixed is False and there are no non-suffixed bounces for a particular day,
            this method will use the latest suffixed bounce for that day.
        """
        bounces = cls.find_bounces(directory)

        # Group bounces by day
        by_day: dict[tuple[int, int, int], list[Bounce]] = {}
        for bounce in bounces:
            key = (bounce.year, bounce.month, bounce.day)
            if key not in by_day:
                by_day[key] = []
            by_day[key].append(bounce)

        # Get the latest bounce for each day
        latest_bounces = [
            cls.get_latest_bounce(day_bounces, include_suffixed) for day_bounces in by_day.values()
        ]

        return sorted(latest_bounces, key=lambda x: x.date)

    @classmethod
    def sort_bounces(cls, bounces: list[Bounce]) -> list[Bounce]:
        """Sort bounces by title, date, version, minor version, and suffix.

        The sorting order is as follows:
        1. Title (alphabetically)
        2. Date (chronologically)
        3. Version (numerically)
        4. Minor version (alphabetically, empty string before 'a')
        5. Suffix (alphabetically, None before any suffix)

        Args:
            bounces: A list of Bounce objects to sort.

        Returns:
            A sorted list of Bounce objects.

        Example:
            bounces = [
                Bounce(title="Song A", year=24, month=5, day=1, version=1, suffix="No Vocals", ...),
                Bounce(title="Song A", year=24, month=5, day=1, version=1, suffix=None, ...),
                Bounce(title="Song B", year=24, month=5, day=1, version=1, minor_version="b"...),
                Bounce(title="Song A", year=24, month=5, day=2, version=1, minor_version=""...),
            ]
            sorted_bounces = BounceParser.sort_bounces(bounces)

            # Result order:
            # 1. Song A, 2024-05-01, version 1, no minor version, no suffix
            # 2. Song A, 2024-05-01, version 1, no minor version, "No Vocals" suffix
            # 3. Song A, 2024-05-02, version 1, no minor version, no suffix
            # 4. Song B, 2024-05-01, version 1, minor version 'b', no suffix
        """
        return sorted(
            bounces,
            key=lambda x: (x.title, x.date, x.version, x.minor_version or " ", x.suffix or ""),
        )

    @classmethod
    def group_bounces(
        cls, bounces: list[Bounce]
    ) -> dict[tuple[str, datetime, int], dict[str, list[Bounce]]]:
        """Group bounces by title, date, major version, and suffix.

        This method creates a nested dictionary structure that groups Bounce objects first by their
        title, date, and major version, and then by their suffix.

        Args:
            bounces: A list of Bounce objects to group.

        Returns:
            A nested dictionary with the following structure:
            {
                (title, date, version): {
                    suffix1: [Bounce1, Bounce2, ...],
                    suffix2: [Bounce3, Bounce4, ...],
                    ...
                },
                ...
            }
            Where:
            - The outer dictionary key is a tuple of (title, date, version)
            - The inner dictionary key is the suffix (or an empty string if no suffix)
            - The inner dictionary value is a list of Bounce objects

        Example:
            bounces = [
               Bounce(title="Song A", year=24, month=5, day=1, version=1, suffix="No Vocals", ...),
               Bounce(title="Song A", year=24, month=5, day=1, version=1, suffix=None, ...),
               Bounce(title="Song B", year=24, month=5, day=2, version=2, suffix=None, ...)
            ]
            grouped_bounces = BounceParser.group_bounces(bounces)

            # Result structure:
            # {
            #     ("Song A", datetime(2024, 5, 1), 1): {
            #         "No Vocals": [Bounce(title="Song A", ...)],
            #         "": [Bounce(title="Song A", ...)]
            #     },
            #     ("Song B", datetime(2024, 5, 2), 2): {
            #         "": [Bounce(title="Song B", ...)]
            #     }
            # }
        """
        groups = {}
        for bounce in bounces:
            key = (bounce.title, bounce.date, bounce.version)
            if key not in groups:
                groups[key] = {}
            suffix = bounce.suffix or ""
            if suffix not in groups[key]:
                groups[key][suffix] = []
            groups[key][suffix].append(bounce)
        return groups

    @classmethod
    def filter_by_suffix(cls, directory: Path, suffix: str) -> list[Bounce]:
        """Filter bounces by suffix.

        This method is case-sensitive and matches the suffix exactly. If you need case-insensitive
        matching or partial matching, you'll need to implement that separately.

        Args:
            directory: The directory to search for bounce files.
            suffix: The suffix to filter by. Pass an empty string to find bounces with no suffix.

        Returns:
            A list of Bounce objects with the specified suffix, sorted by date and version.

        Example:
            Assume the directory contains:
            - Song A 24.5.1_0 No Vocals.wav
            - Song A 24.5.1_1.wav
            - Song B 24.5.2_0 no vocals.wav
            - Song B 24.5.2_1 No Vocals.wav

            no_vocals = BounceParser.filter_by_suffix("/path/to/bounces", "No Vocals")

            # Result will be a list of Bounce objects:
            # [
            #    Bounce(title="Song A", year=24, month=5, day=1, version=0, suffix="No Vocals" ...),
            #    Bounce(title="Song B", year=24, month=5, day=2, version=1, suffix="No Vocals" ...)
            # ]

        Note:
            - This method will not match "no vocals" or "NO VOCALS" when filtering for "No Vocals".
            - To find bounces with no suffix, pass an empty string as the suffix argument.
        """
        bounces = cls.find_bounces(directory)
        return [bounce for bounce in bounces if bounce.suffix == suffix]

    @classmethod
    def filter_by_format(cls, directory: Path, file_format: str) -> list[Bounce]:
        """Filter bounces by file format.

        This method finds all bounce files in the directory and filters them to include only those
        with the specified file format.

        Args:
            directory: The directory to search for bounce files.
            file_format: The file format to filter by (e.g., 'wav', 'm4a').

        Returns:
            A list of Bounce objects with the specified file format, sorted by date and version.

        Example:
            wav_bounces = BounceParser.filter_by_format("/path/to/bounces", "wav")

            # If the directory contains:
            # - Song A 24.5.1_0.wav
            # - Song A 24.5.1_1.m4a
            # - Song B 24.5.2_0.wav
            # - Song C 24.5.3_0.mp3

            # The result will be a list of Bounce objects for "Song A 24.5.1_0.wav"
            # and "Song B 24.5.2_0.wav", sorted by date and version.

        Note:
            - The file_format comparison is case-insensitive ('wav' will match 'WAV' or 'wav').
            - The file_format should be specified without the leading dot (use 'wav', not '.wav').
            - If no bounces are found with the specified format, an empty list is returned.
        """
        bounces = cls.find_bounces(directory)
        return [bounce for bounce in bounces if bounce.file_format.lower() == file_format.lower()]
