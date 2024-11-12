# ruff: noqa: C901,T201

from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime

from dsutil.log import LocalLogger
from dsutil.tz import TZ

CALENDAR_APPLESCRIPT = """
    tell application "Calendar"
        set startDate to current date
        set endDate to (current date) + (7 * days)

        set allEvents to {}
        repeat with calendarAccount in calendars
            set eventList to (every event of calendarAccount whose start date ≥ startDate and start date ≤ endDate)
            set allEvents to allEvents & eventList
        end repeat

        set outputText to ""
        repeat with theEvent in allEvents
            set eventDate to start date of theEvent
            set eventTitle to summary of theEvent
            set outputText to outputText & (date string of eventDate) & " " & (time string of eventDate) & ": " & eventTitle & return
        end repeat

        set tempFile to (path to temporary items as text) & "calendar_export.txt"
        set fileRef to open for access tempFile with write permission
        write outputText to fileRef
        close access fileRef

        return (POSIX path of tempFile)
    end tell
"""


class EventRetriever:
    """Retrieve and process calendar events."""

    def __init__(self, debug: bool = False) -> None:
        self.logger = LocalLogger.setup_logger(level="DEBUG" if debug else "INFO")

    def get_events(self) -> str:
        """Get calendar events and return them as a string."""
        raw_events = self.get_calendar_events()
        formatted_events = self.process_calendar_output(raw_events)
        self.logger.debug("Formatted calendar events:\n%s", formatted_events)
        return formatted_events

    def get_calendar_events(self) -> str:
        """Run AppleScript to get calendar events and return contents of temp file."""
        self.logger.debug("Running AppleScript to get calendar events...")
        result = subprocess.run(
            ["osascript", "-e", CALENDAR_APPLESCRIPT], capture_output=True, text=True
        )
        if result.returncode != 0:
            msg = f"AppleScript failed: {result.stderr}"
            raise RuntimeError(msg)

        # Result.stdout will contain the path to the temp file
        temp_file_path = result.stdout.strip()
        self.logger.debug("Calendar events saved to temp file: %s", temp_file_path)

        with open(temp_file_path) as f:
            contents = f.read()
            self.logger.debug("Raw calendar events:\n%s", contents)

        with contextlib.suppress(OSError):  # Clean up temp file
            os.remove(temp_file_path)

        return contents

    def parse_calendar_line(self, line: str) -> tuple[datetime, str]:
        """Parse a single line for a calendar event."""
        datetime_str, event = line.split(": ", 1)

        # Replace any non-standard whitespace with a regular space
        datetime_str = re.sub(r"\s+", " ", datetime_str)
        # Remove any non-alphanumeric characters except spaces, commas, and colons
        datetime_str = re.sub(r"[^A-Za-z0-9:, ]", " ", datetime_str)
        # Normalize whitespace
        datetime_str = " ".join(datetime_str.split())

        dt = datetime.strptime(datetime_str, "%A, %B %d, %Y %I:%M:%S %p").astimezone(TZ)
        return dt, event.strip()

    def format_time(self, dt: datetime) -> str:
        """Format a datetime object as a string in the format "9:30 AM"."""
        # Format time as "9:30 AM" instead of "09:30:00 AM"
        return dt.strftime("%-I:%M %p")

    def format_date(self, dt: datetime) -> str:
        """Format a datetime object as a string in the format "Thursday, November 7, 2024"."""
        # Format date as "Thursday, November 7, 2024"
        return dt.strftime("%A, %B %-d, %Y")

    def process_calendar_output(self, raw_text: str) -> str:
        """Process raw calendar output into a formatted string."""
        # Parse all lines into (datetime, event) tuples
        events = []
        for line in raw_text.strip().split("\n"):
            if line.strip():
                dt, event = self.parse_calendar_line(line)
                events.append((dt, event))

        # Remove duplicates while preserving order
        seen = set()
        events = [x for x in events if not (x in seen or seen.add(x))]

        # Sort by datetime
        events.sort(key=lambda x: x[0])

        # Group by date
        events_by_date = defaultdict(list)
        for dt, event in events:
            date_key = dt.date()
            events_by_date[date_key].append((dt, event))

        # Format output
        output = []
        for date in sorted(events_by_date.keys()):
            day_events = events_by_date[date]

            # Add date header
            output.append(self.format_date(day_events[0][0]))

            # Add events for this day
            for dt, event in day_events:
                output.append(f"{self.format_time(dt)}: {event}")

            # Add blank line between days
            output.append("")

        return "\n".join(output).strip()


def main() -> None:
    """Get and process calendar events."""
    parser = argparse.ArgumentParser(description="Get and process calendar events")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    event_retriever = EventRetriever(args.debug)
    events = event_retriever.get_events()

    print(events)


if __name__ == "__main__":
    main()
