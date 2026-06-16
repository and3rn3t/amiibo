from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FLIPPER_NFC_MAGIC = "Filetype: Flipper NFC device"



@dataclass
class ValidationResult:
    path: Path
    valid: bool
    reason: str = ""



def validate_nfc_file(path: Path) -> ValidationResult:
    try:
        with path.open("rb") as fh:
            header = fh.read(256).decode("utf-8", errors="replace")
    except OSError as error:
        return ValidationResult(path=path, valid=False, reason=str(error))

    if FLIPPER_NFC_MAGIC in header:
        return ValidationResult(path=path, valid=True)

    return ValidationResult(
        path=path,
        valid=False,
        reason="Missing Flipper NFC header — may be a raw binary dump, not a Flipper .nfc file",
    )



def validate_nfc_directory(source_dir: Path) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for path in sorted(source_dir.rglob("*.nfc")):
        results.append(validate_nfc_file(path))
    return results
