#!/usr/bin/env python

"""
Does an IP lookup using multiple sources.

This script is designed to do an IP lookup using multiple sources. It can be used to get
more information about an IP address, including the country, region, city, ISP, and
organization. It collates the information and combines sources that say the same thing.

It uses the sources from https://www.iplocation.net, because I totally just scraped the
API code from their site. But hey, it works great!
"""

from __future__ import annotations

import argparse
import json

import requests

from .ip_sources import IP_SOURCES

from dsutil.shell import handle_keyboard_interrupt
from dsutil.text import color

TIMEOUT = 2
MAX_RETRIES = 3


class IPLookup:
    """Perform an IP lookup using multiple sources."""

    def __init__(self, ip_address: str, do_lookup: bool = True):
        self.ip_address = ip_address

        if do_lookup:
            self.perform_ip_lookup()

    def perform_ip_lookup(self) -> None:
        """Fetch and print IP data from all sources."""
        print(color(f"\nIP lookup results for {self.ip_address}:", "blue"))

        for source, config in IP_SOURCES.items():
            result = self.get_ip_info(source)
            if not result:
                continue

            data = result
            for key in config["data_path"]:
                data = data.get(key, {})
            if not data:
                print(f"\n{color(f'[{source}]', 'blue')} No data available.")
                continue

            print_data = {}
            for key, value in config["fields"].items():
                if isinstance(value, tuple):
                    value, _ = value
                retrieved_value = data.get(value, f"Unknown {key.capitalize()}")
                if key == "country":
                    retrieved_value = self._get_full_country_name(retrieved_value)

                print_data[key] = retrieved_value

            self.print_ip_data(source, **print_data)

    def get_ip_info(self, source: str) -> dict | None:
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

    @staticmethod
    def print_ip_data(
        source: str, country: str, region: str, city: str, isp: str, org: str
    ) -> None:
        """Print the IP data."""
        header = f"{color(f'[{source}]', 'blue')}"
        print(f"\n{header} {color('Location:', 'green')} {city}, {region}, {country}")
        if isp and org and isp not in ["Unknown ISP", ""] and org not in ["Unknown Org", ""]:
            print(f"{header} {color('ISP/Org:', 'green')} {isp} / {org}")

    @staticmethod
    def get_external_ip() -> str | None:
        """Get the external IP address using ipify.org."""
        try:
            response = requests.get("https://api.ipify.org", timeout=TIMEOUT)
            if response.status_code == 200:
                external_ip = response.text
                print(color(f"Your external IP address is: {external_ip}", "blue"))
                return external_ip
        except requests.exceptions.RequestException as e:
            print(color(f"Failed to get external IP: {e}", "red"))

    @staticmethod
    def _get_full_country_name(country_code: str) -> str:
        try:
            import pycountry

            return pycountry.countries.get(alpha_2=country_code.upper()).name
        except (ImportError, AttributeError):
            return country_code


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="IP address lookup tool")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "ip_address", type=str, nargs="?", default=None, help="the IP address to look up"
    )
    group.add_argument("--me", action="store_true", help="get your external IP address")
    group.add_argument(
        "--me-lookup", action="store_true", help="get lookup results for your IP address"
    )
    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Main function."""
    args = parse_arguments()
    if args.me_lookup:
        args.me = True

    if args.me:
        ip_address = IPLookup.get_external_ip()
        if not ip_address or not args.me_lookup:
            return
    else:
        ip_address = args.ip_address or input("Please enter the IP address to look up: ")

    IPLookup(ip_address)


if __name__ == "__main__":
    main()
