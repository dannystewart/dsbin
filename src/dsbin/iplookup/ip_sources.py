from __future__ import annotations

from typing import Any

from dsutil.text import Text

IP_SOURCES: dict[str, dict[str, Any]] = {
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
            "isp": ("isp", Text.HTML.strip),
            "org": ("organization", Text.HTML.strip),
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
