from __future__ import annotations

import json
import os

import requests

rest_url = "https://dnst.me/rest/v2/short-urls"


def generate_short_url(long_url: str) -> str:
    """Generate a short URL using the dnst.me Shlink API."""
    params = {"longUrl": long_url, "shortCodeLength": 4}
    data = {"longUrl": "", "findIfExists": True, "shortCodeLength": 4}
    headers = {
        "Accept": "text/plain ",
        "X-Api-Key": "0cfedd66-9aea-491b-8c37-d63320bd5b5b",
        "Content-Type": "application/json",
    }

    response = requests.post(url=rest_url, params=params, headers=headers, data=json.dumps(data))
    return response.text


if input_url := os.getenv("URL"):
    generate_short_url(input_url)
