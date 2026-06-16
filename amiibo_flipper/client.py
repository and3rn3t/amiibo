from __future__ import annotations

import json
from urllib.request import urlopen

from amiibo_flipper.models import Amiibo, amiibo_from_api

AMIIBO_API_URL = "https://www.amiiboapi.com/api/amiibo/"



def fetch_amiibos(url: str = AMIIBO_API_URL) -> list[Amiibo]:
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    payload = json.loads(raw)
    items = payload.get("amiibo")
    if not isinstance(items, list):
        raise ValueError("Unexpected API response: missing 'amiibo' list")

    amiibos = [amiibo_from_api(item) for item in items if isinstance(item, dict)]
    amiibos.sort(key=lambda a: (a.name.lower(), a.amiibo_id.lower()))
    return amiibos
