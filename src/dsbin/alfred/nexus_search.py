# ruff: noqa: T201
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("America/New_York")


@dataclass
class GameData:
    """Dataclass to hold game data from Nexus Mods API."""

    name: str
    genre: str
    mods: int
    domain_name: str


@dataclass
class CacheData:
    """Dataclass to hold cached games data."""

    timestamp: str
    games: list[GameData]


class NexusGamesFetcher:
    """Fetch Nexus Mods games list and generate Alfred JSON for autocomplete."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("NEXUS_API_KEY", "")
        self.cache_file = Path.home() / ".cache" / "nexus_games.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(days=7)

        if not self.api_key:
            msg = "NEXUS_API_KEY environment variable is required."
            raise ValueError(msg)

    def get_games(self) -> CacheData:
        """Get games list, either from cache or API."""
        if self._should_use_cache():
            return self._read_cache()
        return self._fetch_and_cache_games()

    def _should_use_cache(self) -> bool:
        """Check if cache exists and is fresh."""
        if not self.cache_file.exists():
            return False

        cache_data = self._read_cache()
        cache_time = datetime.fromisoformat(cache_data.timestamp)
        return datetime.now(tz=TZ) - cache_time < self.cache_duration

    def _read_cache(self) -> CacheData:
        """Read cached games data."""
        with Path(self.cache_file).open("r", encoding="utf-8") as f:
            data = json.load(f)
            return CacheData(
                timestamp=data["timestamp"], games=[GameData(**game) for game in data["games"]]
            )

    def _fetch_and_cache_games(self) -> CacheData:
        """Fetch games from API and cache results."""
        headers = {"apikey": self.api_key}
        response = requests.get("https://api.nexusmods.com/v1/games.json", headers=headers)
        response.raise_for_status()

        games_data = response.json()
        cache_data = CacheData(
            timestamp=datetime.now(tz=TZ).isoformat(),
            games=[GameData(**game) for game in games_data],
        )

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        with Path(self.cache_file).open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": cache_data.timestamp,
                    "games": [game.__dict__ for game in cache_data.games],
                },
                f,
            )

        return cache_data

    def generate_alfred_json(self) -> dict[str, object]:
        """Generate Alfred-compatible JSON for autocomplete."""
        games_data = self.get_games()

        alfred_items = [
            {
                "title": game.name,
                "subtitle": f"Genre: {game.genre} | Mods: {game.mods:,}",
                "arg": game.domain_name,
                "autocomplete": game.name,
                "icon": {"path": "icon.png"},
            }
            for game in games_data.games
        ]

        return {
            "cache": {
                "seconds": 86400,
                "loosereload": "true",
            },
            "items": alfred_items,
        }


def main() -> None:
    """Fetch Nexus Mods games list and generate Alfred JSON for autocomplete."""
    fetcher = NexusGamesFetcher()
    alfred_json = fetcher.generate_alfred_json()
    sys.stdout.write(json.dumps(alfred_json))


if __name__ == "__main__":
    main()
