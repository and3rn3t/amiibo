from __future__ import annotations

import shutil
from pathlib import Path

SUPPORTED_NFC_SUFFIXES = {".nfc", ".bin"}



def import_nfc_files(source_dir: Path, target_dir: Path, overwrite: bool = False) -> int:
    if not source_dir.exists():
        raise FileNotFoundError(f"NFC source path not found: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"NFC source path is not a directory: {source_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_NFC_SUFFIXES:
            continue

        relative = path.relative_to(source_dir)
        out_path = target_dir / relative
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists() and not overwrite:
            continue

        shutil.copy2(path, out_path)
        count += 1

    return count
