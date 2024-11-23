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
from typing import Any

import requests
from termcolor import colored

from dsutil.text import remove_html_tags
from dsutil.shell import handle_keyboard_interrupt

SOURCES: dict[str, dict[str, Any]] = {
    "ip2location": {
        "data_path": ["res"],
        "fields": {
            "country": "countryName",
            "region": "regionName",
            "city": "cityName",
            "isp": "isp",
            "org": "organization",
        },
    },
    "ipinfo": {
        "data_path": ["res"],
        "fields": {
            "country": "country",
            "region": "region",
            "city": "city",
            "isp": ("isp", remove_html_tags),
            "org": ("organization", remove_html_tags),
        },
    },
    "dbip": {
        "data_path": ["res"],
        "fields": {
            "country": "country",
            "region": "stateprov",
            "city": "city",
            "isp": "isp",
            "org": "organization",
        },
    },
    "ipregistry": {
        "data_path": ["res", "location", "connection", "company"],
        "fields": {
            "country": ("location", "country", "name"),
            "region": ("location", "region", "name"),
            "city": ("location", "city"),
            "isp": ("connection", "organization"),
            "org": ("company", "name"),
        },
    },
    "ipgeolocation": {
        "data_path": ["res", "data"],
        "fields": {
            "country": "country_name",
            "region": "state_prov",
            "city": "city",
            "isp": "isp",
            "org": "organization",
        },
    },
    "ipapico": {
        "data_path": ["res"],
        "fields": {
            "country": "country",
            "region": "region",
            "city": "city",
            "isp": "org",
            "org": "org",
        },
    },
    "ipbase": {
        "data_path": ["res", "data", "location", "connection"],
        "fields": {
            "country": ("location", "country", "name"),
            "region": ("location", "region", "name"),
            "city": ("location", "city", "name"),
            "isp": ("connection", "isp"),
            "org": ("connection", "organization"),
        },
    },
    "criminalip": {
        "data_path": ["res"],
        "fields": {
            "country": "country_code",
            "region": "region",
            "city": "city",
            "isp": "as_name",
            "org": "org_name",
        },
    },
}


TIMEOUT = 2
MAX_RETRIES = 3


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="IP address lookup tool.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "ip_address",
        type=str,
        nargs="?",
        default=None,
        help="The IP address to look up",
    )
    group.add_argument(
        "--me",
        action="store_true",
        help="Look up your own external IP address",
    )
    group.add_argument(
        "--me-with-lookup",
        action="store_true",
        help="Include your IP lookup in the output",
    )
    return parser.parse_args()


def get_ip_info(ip_address: str, source: str) -> dict | None:
    """Get the IP information from the source."""
    site_url = "https://www.iplocation.net/"
    url = f"{site_url}get-ipdata"
    payload = {"ip": ip_address, "source": source, "ipv": 4}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=TIMEOUT)
            if response.status_code == 200:
                return json.loads(response.text)
        except requests.exceptions.Timeout:
            print(f"\n{colored(f'[{source}]', 'blue')} Timeout ({attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            print(
                f"\n{colored(f'[{source}]', 'blue')} {colored(f'Failed to get data: {e}', 'red')}"
            )
            break

    return None


def print_ip_data(source: str, country: str, region: str, city: str, isp: str, org: str) -> None:
    """Print the IP data."""
    header = f"{colored(f'[{source}]', 'blue')}"
    print(f"\n{header} {colored('Location:', 'green')} {city}, {region}, {country}")
    if isp and org and isp not in ["Unknown ISP", ""] and org not in ["Unknown Org", ""]:
        print(f"{header} {colored('ISP/Org:', 'green')} {isp} / {org}")


def fetch_and_print_ip_data(ip_address: str) -> None:
    """Fetch and print IP data from all sources."""
    for source, config in SOURCES.items():
        result = get_ip_info(ip_address, source)
        if not result:
            continue

        data = result
        for key in config["data_path"]:
            data = data.get(key, {})
        if not data:
            print(f"\n{colored(f'[{source}]', 'blue')} No data available.")
            continue

        print_data = {}
        for key, value in config["fields"].items():
            if isinstance(value, tuple):
                value, _ = value
            retrieved_value = data.get(value, f"Unknown {key.capitalize()}")
            if key == "country":
                retrieved_value = _get_full_country_name(retrieved_value)

            print_data[key] = retrieved_value

        print_ip_data(source, **print_data)


def _get_full_country_name(country_code: str) -> str:
    try:
        import pycountry

        return pycountry.countries.get(alpha_2=country_code.upper()).name
    except (ImportError, AttributeError):
        return country_code


def get_external_ip() -> str | None:
    """Get the external IP address using ipify.org."""
    try:
        response = requests.get("https://api.ipify.org", timeout=TIMEOUT)
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException as e:
        print(colored(f"Failed to get external IP: {e}", "red"))
    return None


@handle_keyboard_interrupt()
def main() -> None:
    """Main function."""
    args = parse_arguments()
    if args.me_with_lookup:
        args.me = True

    if args.me:
        ip_address = get_external_ip()
        if not ip_address:
            return
        print(colored(f"Your external IP address is: {ip_address}", "blue"))
        if not args.me_with_lookup:
            return
    else:
        ip_address = args.ip_address or input("Please enter the IP address to look up: ")

    print(colored(f"\nIP lookup results for {ip_address}:", "blue"))
    fetch_and_print_ip_data(ip_address)


if __name__ == "__main__":
    main()
