#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import ClassVar


class AppLauncher:
    """Class to handle app launching."""

    APP_LOCATIONS: ClassVar[list[str]] = [
        "/Applications",
        "/System/Applications",
    ]
    BASE_APPS: ClassVar[list[str]] = [
        "DEFAULT_BROWSER",
        "Telegram",
        "Drafts",
        "Bear",
    ]
    WORK_APPS: ClassVar[list[str]] = [
        "Teams",
        "Outlook",
    ]
    MUSIC_APPS: ClassVar[list[str]] = [
        "Logic Pro",
        "Adobe Audition",
    ]

    def launch(self, query: str) -> None:
        """Launch apps based on the query."""
        apps_to_open: list[str] = self.BASE_APPS[:]

        if query == "work":
            apps_to_open.extend(self.WORK_APPS)
        elif query == "music":
            apps_to_open.extend(self.MUSIC_APPS)

        with Pool() as pool:
            try:
                results = pool.map_async(self.open_app, apps_to_open).get(timeout=30)

                launched_apps = sum(results)
                if launched_apps != len(apps_to_open):
                    failed_apps = len(apps_to_open) - launched_apps
                    sys.stdout.write(
                        f"Failed to launch {failed_apps} {'apps' if failed_apps != 1 else 'app'}.\n"
                    )
            except Exception as e:
                sys.stdout.write(f"Error launching apps: {e}\n")

    def open_app(self, app_name: str) -> bool:
        """Find and open the app with the given name."""
        try:
            if app_name == "DEFAULT_BROWSER":
                subprocess.Popen(["open", "x-choosy://best.all/"])
                return True

            app_path = self.identify_app(app_name)
            if app_path and app_path.exists():
                subprocess.Popen(["open", str(app_path)])
                return True
            return False
        except Exception as e:
            sys.stdout.write(f"Error opening {app_name}: {e}\n")
            return False

    def identify_app(self, app_name: str) -> Path:
        """Find the full path of an app given its name."""
        app_name_lower = app_name.lower()
        exact_match: Path | None = None
        substring_match: Path | None = None

        for location in self.APP_LOCATIONS:
            location_path = Path(location)

            # Only get immediate children of the location directory
            for item in location_path.iterdir():
                if item.is_dir() and item.name.lower().endswith(".app"):
                    dir_name_lower = item.name.lower()

                    # Exact match including ".app"
                    if dir_name_lower == f"{app_name_lower}.app":
                        return item

                    # Exact match without ".app"
                    if dir_name_lower == app_name_lower:
                        exact_match = item

                    # Substring match
                    if not exact_match and app_name_lower in dir_name_lower:
                        substring_match = item

        if exact_match:
            return exact_match
        if substring_match:
            return substring_match

        sys.stdout.write(f"Warning: Could not find app '{app_name}'\n")
        return Path()


def main() -> None:
    """Open the apps based on the query."""
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    AppLauncher().launch(query)


if __name__ == "__main__":
    main()
