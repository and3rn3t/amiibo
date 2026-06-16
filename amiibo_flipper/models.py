from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Amiibo:
    head: str
    tail: str
    name: str
    amiibo_series: str
    game_series: str
    character: str
    type: str
    image: str
    release_au: str | None
    release_eu: str | None
    release_jp: str | None
    release_na: str | None

    @property
    def amiibo_id(self) -> str:
        return f"{self.head}{self.tail}"



def amiibo_from_api(payload: dict[str, Any]) -> Amiibo:
    release_raw = payload.get("release") or {}
    return Amiibo(
        head=str(payload.get("head", "")).strip(),
        tail=str(payload.get("tail", "")).strip(),
        name=str(payload.get("name", "")).strip(),
        amiibo_series=str(payload.get("amiiboSeries", "")).strip(),
        game_series=str(payload.get("gameSeries", "")).strip(),
        character=str(payload.get("character", "")).strip(),
        type=str(payload.get("type", "")).strip(),
        image=str(payload.get("image", "")).strip(),
        release_au=_normalize_nullable(release_raw.get("au")),
        release_eu=_normalize_nullable(release_raw.get("eu")),
        release_jp=_normalize_nullable(release_raw.get("jp")),
        release_na=_normalize_nullable(release_raw.get("na")),
    )



def _normalize_nullable(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None
