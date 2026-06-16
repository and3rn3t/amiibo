from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

NTAG215_PAGES = 135
NTAG215_PAGE_SIZE = 4
NTAG215_EXPECTED_SIZE = NTAG215_PAGES * NTAG215_PAGE_SIZE  # 540 bytes

ATQA = "44 00"
SAK = "00"
# Standard NTAG215 IC version response
MIFARE_VERSION = "00 04 04 02 01 00 11 03"
SIGNATURE_ZERO = " ".join(["00"] * 32)


@dataclass(frozen=True)
class ConversionSummary:
    source_root: Path
    output_root: Path
    scanned: int
    converted: int
    skipped_existing: int
    skipped_invalid_size: int

    @property
    def skipped_total(self) -> int:
        return self.skipped_existing + self.skipped_invalid_size



def bin_to_nfc(data: bytes) -> str:
    if len(data) != NTAG215_EXPECTED_SIZE:
        raise ValueError(
            f"Expected {NTAG215_EXPECTED_SIZE} bytes (NTAG215), got {len(data)}"
        )

    pages = [data[i * 4 : (i + 1) * 4] for i in range(NTAG215_PAGES)]

    # UID is bytes 0-2 of page 0, then all 4 bytes of page 1
    uid_bytes = list(pages[0][:3]) + list(pages[1])
    uid = " ".join(f"{b:02X}" for b in uid_bytes)

    lines: list[str] = [
        "Filetype: Flipper NFC device",
        "Version: 2",
        "# Nfc device type can be UID, Mifare Ultralight, Bank card",
        "Device type: NTAG215",
        "# UID, ATQA and SAK are common for all formats",
        f"UID: {uid}",
        f"ATQA: {ATQA}",
        f"SAK: {SAK}",
        "# Mifare Ultralight specific data",
        f"Signature: {SIGNATURE_ZERO}",
        f"Mifare version: {MIFARE_VERSION}",
        "Counter 0: 0",
        "Tearing 0: 00",
        "Counter 1: 0",
        "Tearing 1: 00",
        "Counter 2: 0",
        "Tearing 2: 00",
        f"Pages total: {NTAG215_PAGES}",
    ]

    for i, page in enumerate(pages):
        hex_page = " ".join(f"{b:02X}" for b in page)
        lines.append(f"Page {i}: {hex_page}")

    lines.append("")
    return "\n".join(lines)



def convert_directory(
    source_dir: Path,
    output_dir: Path,
    overwrite: bool = False,
    flatten: bool = False,
) -> ConversionSummary:
    scanned = 0
    converted = 0
    skipped_existing = 0
    skipped_invalid_size = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    for bin_path in sorted(path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() == ".bin"):
        scanned += 1
        rel = Path(bin_path.name) if flatten else bin_path.relative_to(source_dir)
        out_path = (output_dir / rel).with_suffix(".nfc")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists() and not overwrite:
            skipped_existing += 1
            logger.debug("Skipping existing output %s", out_path)
            continue

        data = bin_path.read_bytes()
        if len(data) != NTAG215_EXPECTED_SIZE:
            skipped_invalid_size += 1
            logger.warning("Skipping %s because it is %s bytes, not %s", bin_path, len(data), NTAG215_EXPECTED_SIZE)
            continue

        out_path.write_text(bin_to_nfc(data), encoding="utf-8")
        converted += 1
        logger.info("Converted %s -> %s", bin_path, out_path)

    summary = ConversionSummary(
        source_root=source_dir,
        output_root=output_dir,
        scanned=scanned,
        converted=converted,
        skipped_existing=skipped_existing,
        skipped_invalid_size=skipped_invalid_size,
    )
    logger.debug("Conversion summary: %s", summary)
    return summary
