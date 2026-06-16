from __future__ import annotations

import shutil
from pathlib import Path

from amiibo_flipper.exporter import slugify_filename
from amiibo_flipper.models import Amiibo
from amiibo_flipper.nfc import SUPPORTED_NFC_SUFFIXES



def organize_nfc_files(
    source_dir: Path,
    output_dir: Path,
    amiibos: list[Amiibo],
    overwrite: bool = False,
) -> tuple[int, int]:
    name_map = _build_name_map(amiibos)
    output_dir.mkdir(parents=True, exist_ok=True)

    renamed = 0
    copied_as_is = 0

    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_NFC_SUFFIXES:
            continue

        match = _find_match(path.stem, name_map)
        if match:
            series_dir = output_dir / slugify_filename(match.amiibo_series)
            series_dir.mkdir(parents=True, exist_ok=True)
            dest = series_dir / (slugify_filename(match.name) + path.suffix.lower())
            renamed += 1
        else:
            dest = output_dir / "unsorted" / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            copied_as_is += 1

        if dest.exists() and not overwrite:
            continue

        shutil.copy2(path, dest)

    return renamed, copied_as_is



def _build_name_map(amiibos: list[Amiibo]) -> dict[str, Amiibo]:
    mapping: dict[str, Amiibo] = {}
    for amiibo in amiibos:
        mapping[_normalize(amiibo.name)] = amiibo
        mapping[_normalize(amiibo.amiibo_id)] = amiibo
        mapping[_normalize(slugify_filename(f"{amiibo.name}-{amiibo.amiibo_id}"))] = amiibo
    return mapping



def _find_match(stem: str, name_map: dict[str, Amiibo]) -> Amiibo | None:
    return name_map.get(_normalize(stem))



def _normalize(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ").strip()
