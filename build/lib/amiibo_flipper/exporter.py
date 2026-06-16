from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from amiibo_flipper.models import Amiibo



def export_entries(amiibos: list[Amiibo], output_dir: Path, file_format: str = "txt") -> int:
    entries_dir = output_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)

    if file_format not in {"txt", "json"}:
        raise ValueError("file_format must be 'txt' or 'json'")

    for amiibo in amiibos:
        safe_name = slugify_filename(f"{amiibo.name}-{amiibo.amiibo_id}")
        out_path = entries_dir / f"{safe_name}.{file_format}"
        if file_format == "txt":
            out_path.write_text(render_text_entry(amiibo), encoding="utf-8")
        else:
            out_path.write_text(
                json.dumps(asdict(amiibo), ensure_ascii=True, indent=2),
                encoding="utf-8",
            )

    write_index(amiibos, output_dir)
    return len(amiibos)



def write_index(amiibos: list[Amiibo], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.json"
    index_payload = {
        "count": len(amiibos),
        "entries": [
            {
                "name": a.name,
                "id": a.amiibo_id,
                "character": a.character,
                "gameSeries": a.game_series,
                "amiiboSeries": a.amiibo_series,
                "type": a.type,
            }
            for a in amiibos
        ],
    }
    index_path.write_text(json.dumps(index_payload, ensure_ascii=True, indent=2), encoding="utf-8")



def render_text_entry(amiibo: Amiibo) -> str:
    return "\n".join(
        [
            f"Name: {amiibo.name}",
            f"ID: {amiibo.amiibo_id}",
            f"Character: {amiibo.character}",
            f"Type: {amiibo.type}",
            f"Amiibo Series: {amiibo.amiibo_series}",
            f"Game Series: {amiibo.game_series}",
            f"Release (JP): {amiibo.release_jp or '-'}",
            f"Release (NA): {amiibo.release_na or '-'}",
            f"Release (EU): {amiibo.release_eu or '-'}",
            f"Release (AU): {amiibo.release_au or '-'}",
            f"Image: {amiibo.image}",
            "",
        ]
    )



def slugify_filename(text: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "-", text.strip())
    sanitized = re.sub(r"-+", "-", sanitized)
    sanitized = sanitized.strip("-._")
    return sanitized or "amiibo"
