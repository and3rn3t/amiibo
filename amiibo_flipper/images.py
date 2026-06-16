from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

from amiibo_flipper.exporter import slugify_filename
from amiibo_flipper.models import Amiibo



def download_images(amiibos: list[Amiibo], output_dir: Path, overwrite: bool = False) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0

    for amiibo in amiibos:
        if not amiibo.image:
            skipped += 1
            continue

        suffix = Path(amiibo.image).suffix or ".png"
        filename = slugify_filename(f"{amiibo.name}-{amiibo.amiibo_id}") + suffix
        out_path = output_dir / filename

        if out_path.exists() and not overwrite:
            skipped += 1
            continue

        try:
            with urlopen(amiibo.image, timeout=30) as response:
                out_path.write_bytes(response.read())
            downloaded += 1
        except (URLError, OSError):
            skipped += 1

    return downloaded, skipped
