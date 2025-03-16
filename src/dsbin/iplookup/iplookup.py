#!/usr/bin/env python

"""Does an IP lookup using multiple sources.

This script is designed to do an IP lookup using multiple sources. It can be used to get
more information about an IP address, including the country, region, city, ISP, and
organization. It collates the information and combines sources that say the same thing.

It uses the sources from https://www.iplocation.net, because I totally just scraped the
API code from their site. But hey, it works!
"""

from __future__ import annotations

import argparse
import json
import operator
from collections import Counter
from typing import Any, ClassVar

import pycountry
import requests

from dsbase.progress import halo_progress
from dsbase.shell import handle_keyboard_interrupt
from dsbase.text import color, print_colored

from .ip_sources import CITY_NAMES, IP_SOURCES, REGION_NAMES, USA_NAMES

TIMEOUT = 2
MAX_RETRIES = 3


class IPLookup:
    """Perform an IP lookup using multiple sources."""

    # Omit these values entirely if they start with "Unknown"
    OMIT_UNKNOWN: ClassVar[set[str]] = {"region", "isp", "org"}

    def __init__(self, ip_address: str, do_lookup: bool = True):
        self.ip_address: str = ip_address
        self.missing_sources: list[str] = []

        if do_lookup:
            self.perform_ip_lookup()

    def perform_ip_lookup(self) -> None:
        """Fetch and print IP data from all sources."""
        results = []

        with halo_progress(
            start_message=f"Getting results for {self.ip_address}",
            end_message="Lookup complete!",
            fail_message=f"Failed to get results for {self.ip_address}",
        ) as spinner:
            for source, config in IP_SOURCES.items():
                if spinner:
                    spinner.text = color(f"Querying {source}...", "cyan")

                result = self.process_source(source, config)
                if result:
                    results.append(result)

        self.display_results(results)

    def process_source(self, source: str, config: dict[str, Any]) -> dict[str, str] | None:
        """Process a single IP data source. Returns formatted data or None if no data."""
        result = self.get_ip_info(source)
        if not result:
            return None

        data = result
        for key in config["data_path"]:
            data = data.get(key, {})
        if not data:
            self.missing_sources.append(source)
            return None

        formatted_data = self.extract_field_data(data, config["fields"])
        return self.format_ip_data(source, **formatted_data)

    def extract_field_data(
        self, data: dict[str, Any], fields: dict[str, str | tuple[str, Any]]
    ) -> dict[str, str]:
        """Extract and format field data from source response."""
        formatted_data = {}
        for key, value in fields.items():
            if isinstance(value, tuple):
                value, _ = value

            # Get the value from the data
            retrieved_value = data.get(value, "")

            # If empty or starts with "Unknown", set it to an empty string for formatting
            if not retrieved_value or retrieved_value.startswith("Unknown"):
                retrieved_value = "" if key in self.OMIT_UNKNOWN else f"Unknown {key.capitalize()}"

            formatted_data[key] = retrieved_value

        return formatted_data

    def display_results(self, results: list[dict[str, str]]) -> None:
        """Display the consolidated results and any sources with no data."""
        if results:
            print_colored(f"\n{color(f'Results for {self.ip_address}:', 'cyan')}", "blue")
            self.print_consolidated_results(results)

        if self.missing_sources:
            print_colored(f"\nNo data available from: {', '.join(self.missing_sources)}", "blue")

    def get_ip_info(self, source: str) -> dict[str, Any] | None:
        """Get the IP information from the source."""
        site_url = "https://www.iplocation.net/"
        url = f"{site_url}get-ipdata"
        payload = {"ip": self.ip_address, "source": source, "ipv": 4}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, data=payload, headers=headers, timeout=TIMEOUT)
                if response.status_code == 200:
                    return json.loads(response.text)
            except requests.exceptions.Timeout:
                print(f"\n{color(f'[{source}]', 'blue')} Timeout ({attempt + 1}/{MAX_RETRIES})")
            except requests.exceptions.RequestException as e:
                print(
                    f"\n{color(f'[{source}]', 'blue')} {color(f'Failed to get data: {e}', 'red')}"
                )
                break

        return None

    def format_ip_data(
        self, source: str, country: str, region: str, city: str, isp: str, org: str
    ) -> dict[str, str]:
        """Standardizes and formats the IP data."""
        country = self.standardize_country(country)
        region, city = self.standardize_region_and_city(region, city)
        isp_org = self.standardize_isp_and_org(isp, org)

        # Build location string based on available data
        location_parts = []
        if city:
            location_parts.append(city)
        if region:
            location_parts.append(region)
        if country:
            location_parts.append(country)

        location = ", ".join(location_parts) if location_parts else "Unknown Location"

        formatted_data = {"source": source, "location": location}
        if isp_org:
            formatted_data["ISP_Org"] = isp_org

        return formatted_data

    def print_consolidated_results(self, results: list[dict[str, str]]) -> None:
        """Print consolidated results with sources that report the same data grouped together."""
        # Count occurrences of each location
        location_count = Counter()
        for result in results:
            location = result["location"]
            isp_org = result.get("ISP_Org", "")
            line = f"{location}" + (f" ({isp_org})" if isp_org else "")
            location_count[line] += 1

        # Sort by count (descending)
        sorted_locations = sorted(location_count.items(), key=operator.itemgetter(1), reverse=True)

        # Print consolidated results
        for line, count in sorted_locations:
            if count > 1:
                print(f"• {color(f'{count} sources:', 'blue')} {line}")
            else:  # Find the source for this unique result
                source = next(
                    r["source"]
                    for r in results
                    if f"{r['location']}"
                    + (f" ({r.get('ISP_Org', '')})" if r.get("ISP_Org") else "")
                    == line
                )
                print(f"• {color(source + ':', 'blue')} {line}")

    def standardize_country(self, country: str) -> str:
        """Standardize the country name."""
        if len(country) == 2 and country.upper() != "US":
            try:
                country_obj = pycountry.countries.get(alpha_2=country.upper())
                return country_obj.name if country_obj is not None else country
            except (AttributeError, KeyError):
                return country
        return "US" if country.lower() in USA_NAMES else country

    def standardize_region_and_city(self, region: str, city: str) -> tuple[str, str]:
        """Standardize the region and city names."""
        if region.lower() in REGION_NAMES:
            region = "DC"
        if city.lower() in CITY_NAMES:
            city = "Washington" if "washington" in city.lower() else "New York"
        return region, city

    def standardize_isp_and_org(self, isp: str, org: str) -> str | None:
        """Standardize the ISP and organization names."""
        if "comcast" in isp.lower():
            isp = "Comcast"
        if "comcast" in org.lower():
            org = "Comcast"

        if isp and isp not in {"Unknown ISP", ""}:
            if org and org not in {"Unknown Org", ""}:
                return isp if isp == org else f"{isp} / {org}"
            return isp
        return org if org and org not in {"Unknown Org", ""} else None

    @staticmethod
    def get_external_ip() -> str | None:
        """Get the external IP address using ipify.org."""
        try:
            response = requests.get("https://api.ipify.org", timeout=TIMEOUT)
            if response.status_code == 200:
                external_ip = response.text
                print_colored(f"Your external IP address is: {external_ip}", "blue")
                return external_ip
        except requests.exceptions.RequestException as e:
            print_colored(f"Failed to get external IP: {e}", "red")
        return None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="IP address lookup tool")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("ip_address", type=str, nargs="?", help="the IP address to look up")
    group.add_argument("-m", "--me", action="store_true", help="get your external IP address")
    group.add_argument("-l", "--lookup", action="store_true", help="get lookup for your IP address")
    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Main function."""
    args = parse_args()
    if args.lookup:
        args.me = True

    if args.me:
        ip_address = IPLookup.get_external_ip()
        if not args.lookup:
            return
    else:
        ip_address = args.ip_address or input("Please enter the IP address to look up: ")

    if not ip_address:
        print_colored("No IP address provided.", "red")
        return

    IPLookup(ip_address)


if __name__ == "__main__":
    main()
