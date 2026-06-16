from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from amiibo_flipper.exporter import slugify_filename
from amiibo_flipper.models import Amiibo



@dataclass
class InventoryReport:
    have: list[Amiibo]
    missing: list[Amiibo]
    unmatched_files: list[Path]



def build_inventory(amiibos: list[Amiibo], nfc_dirs: list[Path]) -> InventoryReport:
    nfc_stems = _collect_stems(nfc_dirs)

    have: list[Amiibo] = []
    missing: list[Amiibo] = []

    for amiibo in amiibos:
        if _matches_any(amiibo, nfc_stems):
            have.append(amiibo)
        else:
            missing.append(amiibo)

    known_slugs: set[str] = set()
    for amiibo in amiibos:
        known_slugs.add(_normalize(amiibo.name))

    unmatched: list[Path] = []
    for nfc_dir in nfc_dirs:
        if not nfc_dir.exists():
            continue
        for path in nfc_dir.rglob("*.nfc"):
            if _normalize(path.stem) not in known_slugs:
                unmatched.append(path)

    return InventoryReport(have=have, missing=missing, unmatched_files=unmatched)



def _collect_stems(nfc_dirs: list[Path]) -> set[str]:
    stems: set[str] = set()
    for nfc_dir in nfc_dirs:
        if not nfc_dir.exists():
            continue
        for path in nfc_dir.rglob("*.nfc"):
            stems.add(_normalize(path.stem))
        for path in nfc_dir.rglob("*.bin"):
            stems.add(_normalize(path.stem))
    return stems



def _matches_any(amiibo: Amiibo, stems: set[str]) -> bool:
    candidates = {
        _normalize(amiibo.name),
        _normalize(slugify_filename(f"{amiibo.name}-{amiibo.amiibo_id}")),
        _normalize(amiibo.amiibo_id),
    }
    return bool(candidates & stems)



def _normalize(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ").strip()



def render_inventory_report(report: InventoryReport) -> str:
    lines: list[str] = []
    lines.append(f"Have ({len(report.have)}):")
    for a in sorted(report.have, key=lambda x: x.name):
        lines.append(f"  [x] {a.name}  ({a.amiibo_series})")

    lines.append("")
    lines.append(f"Missing ({len(report.missing)}):")
    for a in sorted(report.missing, key=lambda x: (x.amiibo_series, x.name)):
        lines.append(f"  [ ] {a.name}  ({a.amiibo_series})")

    if report.unmatched_files:
        lines.append("")
        lines.append(f"Unrecognized files ({len(report.unmatched_files)}):")
        for p in sorted(report.unmatched_files):
            lines.append(f"  ?  {p.name}")

    return "\n".join(lines)
