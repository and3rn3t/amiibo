from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from amiibo_flipper.client import fetch_amiibos
from amiibo_flipper.converter import convert_directory
from amiibo_flipper.exporter import export_entries
from amiibo_flipper.images import download_images
from amiibo_flipper.inventory import build_inventory, render_inventory_report
from amiibo_flipper.models import Amiibo, amiibo_from_api
from amiibo_flipper.nfc import import_nfc_files
from amiibo_flipper.organizer import organize_nfc_files
from amiibo_flipper.picker import pick_characters, pick_series
from amiibo_flipper.validator import validate_nfc_directory



DEFAULT_AMIIBO_JSON = Path("data/amiibo.json")
DEFAULT_EXPORT_DIR = Path("flipper-export/apps_data/amiibo_db")
DEFAULT_SD_NFC_DIR = Path("nfc/amiibo")
DEFAULT_DESKTOP_NAME = "flipper-amiibo"



def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    _configure_logging(args.verbose)
    return args.func(args)



def _configure_logging(verbosity: int) -> None:
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amiibo-flipper",
        description="Fetch amiibo metadata and export Flipper-friendly files.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Show extra info: pass -v for info logs, -vv for debug logs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Fetch amiibo API data into a local JSON cache")
    fetch_parser.add_argument("--output", type=Path, default=DEFAULT_AMIIBO_JSON)
    fetch_parser.set_defaults(func=run_fetch)

    # export
    export_parser = subparsers.add_parser("export", help="Export from cached JSON into Flipper-friendly files")
    export_parser.add_argument("--input", type=Path, default=DEFAULT_AMIIBO_JSON)
    export_parser.add_argument("--output", type=Path, default=DEFAULT_EXPORT_DIR)
    export_parser.add_argument("--format", choices=["txt", "json"], default="txt")
    export_parser.add_argument("--series", help="Only include this amiibo series (case-insensitive substring)")
    export_parser.add_argument("--character", help="Only include this character (case-insensitive substring)")
    export_parser.set_defaults(func=run_export)

    # sync
    sync_parser = subparsers.add_parser("sync", help="Fetch + export directly to a Flipper SD mount")
    sync_parser.add_argument("--sd-path", type=Path, required=True, help="Mounted Flipper SD root")
    sync_parser.add_argument("--format", choices=["txt", "json"], default="txt")
    sync_parser.add_argument("--nfc-source", type=Path, help="Directory of existing NFC dump files (.nfc/.bin)")
    sync_parser.add_argument("--overwrite-nfc", action="store_true", help="Overwrite NFC files that already exist")
    sync_parser.add_argument("--series", help="Only include this amiibo series")
    sync_parser.add_argument("--character", help="Only include this character")
    sync_parser.set_defaults(func=run_sync)

    # import-nfc
    nfc_parser = subparsers.add_parser(
        "import-nfc",
        help="Copy existing NFC dump files (.nfc/.bin) into a Flipper SD NFC directory",
    )
    nfc_parser.add_argument("--source", type=Path, required=True, help="Directory containing NFC files")
    nfc_parser.add_argument("--sd-path", type=Path, required=True, help="Mounted Flipper SD root")
    nfc_parser.add_argument("--target-subdir", default=str(DEFAULT_SD_NFC_DIR), help="Destination subfolder under the SD root")
    nfc_parser.add_argument("--overwrite", action="store_true", help="Overwrite files if they already exist")
    nfc_parser.set_defaults(func=run_import_nfc)

    # validate
    val_parser = subparsers.add_parser("validate", help="Check NFC files for valid Flipper format")
    val_parser.add_argument("--source", type=Path, required=True, help="Directory of NFC files to validate")
    val_parser.set_defaults(func=run_validate)

    # inventory
    inv_parser = subparsers.add_parser("inventory", help="Show which amiibo you have vs are missing")
    inv_parser.add_argument("--nfc-source", type=Path, action="append", dest="nfc_sources",
                            help="Directory of NFC dumps (repeat for multiple dirs)")
    inv_parser.add_argument("--series", help="Filter to a specific series")
    inv_parser.add_argument("--character", help="Filter to a specific character")
    inv_parser.add_argument("--output", type=Path, help="Write report to file instead of stdout")
    inv_parser.set_defaults(func=run_inventory)

    # organize
    org_parser = subparsers.add_parser("organize", help="Rename and sort NFC files into series subfolders")
    org_parser.add_argument("--source", type=Path, required=True, help="Source directory of NFC files")
    org_parser.add_argument("--output", type=Path, required=True, help="Output directory")
    org_parser.add_argument("--overwrite", action="store_true")
    org_parser.set_defaults(func=run_organize)

    # images
    img_parser = subparsers.add_parser("images", help="Download official amiibo artwork")
    img_parser.add_argument("--output", type=Path, default=Path("data/images"))
    img_parser.add_argument("--series", help="Only download images for this series")
    img_parser.add_argument("--character", help="Only download images for this character")
    img_parser.add_argument("--overwrite", action="store_true")
    img_parser.set_defaults(func=run_images)

    # stage-desktop
    stage_parser = subparsers.add_parser(
        "stage-desktop",
        help="Stage NFC files in a Desktop folder ready for the Flipper desktop app",
    )
    stage_parser.add_argument("--nfc-source", type=Path, required=True, help="Directory of NFC dump files")
    stage_parser.add_argument("--name", default=DEFAULT_DESKTOP_NAME, help="Desktop folder name")
    stage_parser.set_defaults(func=run_stage_desktop)

    # pick (interactive)
    pick_parser = subparsers.add_parser("pick", help="Interactively choose series/characters to export")
    pick_parser.add_argument("--by", choices=["series", "character"], default="series")
    pick_parser.add_argument("--output", type=Path, default=DEFAULT_EXPORT_DIR)
    pick_parser.add_argument("--format", choices=["txt", "json"], default="txt")
    pick_parser.set_defaults(func=run_pick)

    # convert-bin
    conv_parser = subparsers.add_parser(
        "convert-bin",
        help="Convert raw NTAG215 .bin dumps to Flipper .nfc text format",
    )
    conv_parser.add_argument("--source", type=Path, required=True, help="Directory of .bin files")
    conv_parser.add_argument("--output", type=Path, required=True, help="Destination directory for .nfc files")
    conv_parser.add_argument("--overwrite", action="store_true")
    conv_parser.add_argument(
        "--flatten",
        action="store_true",
        help="Write all converted files into one folder instead of mirroring the source tree",
    )
    conv_parser.set_defaults(func=run_convert_bin)

    return parser



def _apply_filters(amiibos: list[Amiibo], series: str | None, character: str | None) -> list[Amiibo]:
    if series:
        key = series.lower()
        amiibos = [a for a in amiibos if key in a.amiibo_series.lower()]
    if character:
        key = character.lower()
        amiibos = [a for a in amiibos if key in a.character.lower()]
    return amiibos



def _load_remote_amiibos(series: str | None = None, character: str | None = None) -> list[Amiibo]:
    amiibos = fetch_amiibos()
    return _apply_filters(amiibos, series, character)



def run_fetch(args: argparse.Namespace) -> int:
    amiibos = fetch_amiibos()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"amiibo": [asdict(item) for item in amiibos]}
    args.output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Fetched {len(amiibos)} amiibo entries -> {args.output}")
    return 0



def run_export(args: argparse.Namespace) -> int:
    if not args.input.exists():
        print(f"Input file not found: {args.input}")
        return 2

    raw_payload = json.loads(args.input.read_text(encoding="utf-8"))
    raw_amiibos = raw_payload.get("amiibo")
    if not isinstance(raw_amiibos, list):
        print("Invalid input JSON: expected top-level 'amiibo' list")
        return 2

    amiibos = [amiibo_from_api(item) for item in raw_amiibos if isinstance(item, dict)]
    amiibos = _apply_filters(amiibos, getattr(args, "series", None), getattr(args, "character", None))
    count = export_entries(amiibos, args.output, file_format=args.format)
    print(f"Exported {count} entries -> {args.output}")
    return 0



def run_sync(args: argparse.Namespace) -> int:
    mount_path: Path = args.sd_path
    if not mount_path.exists():
        print(f"SD path does not exist: {mount_path}")
        return 2

    amiibos = _load_remote_amiibos(getattr(args, "series", None), getattr(args, "character", None))

    export_dir = mount_path / "apps_data" / "amiibo_db"
    count = export_entries(amiibos, export_dir, file_format=args.format)
    print(f"Synced {count} metadata entries -> {export_dir}")

    if args.nfc_source:
        nfc_target = mount_path / "nfc" / "amiibo"
        try:
            nfc_count = import_nfc_files(args.nfc_source, nfc_target, overwrite=args.overwrite_nfc)
        except (FileNotFoundError, NotADirectoryError) as error:
            print(str(error))
            return 2
        print(f"Imported {nfc_count} NFC files -> {nfc_target}")

    return 0



def run_import_nfc(args: argparse.Namespace) -> int:
    mount_path: Path = args.sd_path
    if not mount_path.exists():
        print(f"SD path does not exist: {mount_path}")
        return 2

    target_dir = mount_path / Path(args.target_subdir)
    try:
        count = import_nfc_files(args.source, target_dir, overwrite=args.overwrite)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(str(error))
        return 2

    print(f"Imported {count} NFC files -> {target_dir}")
    return 0



def run_validate(args: argparse.Namespace) -> int:
    results = validate_nfc_directory(args.source)
    if not results:
        print("No .nfc files found.")
        return 0

    valid = [r for r in results if r.valid]
    invalid = [r for r in results if not r.valid]
    print(f"Valid:   {len(valid)}")
    print(f"Invalid: {len(invalid)}")
    for r in invalid:
        print(f"  FAIL  {r.path.name}: {r.reason}")
    return 0 if not invalid else 1



def run_inventory(args: argparse.Namespace) -> int:
    amiibos = _load_remote_amiibos(getattr(args, "series", None), getattr(args, "character", None))
    nfc_sources: list[Path] = args.nfc_sources or []
    report = build_inventory(amiibos, nfc_sources)
    text = render_inventory_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Report written -> {args.output}")
    else:
        print(text)
    return 0



def run_organize(args: argparse.Namespace) -> int:
    amiibos = fetch_amiibos()
    renamed, as_is = organize_nfc_files(args.source, args.output, amiibos, overwrite=args.overwrite)
    print(f"Organized {renamed} matched files, {as_is} unmatched -> {args.output}")
    return 0



def run_images(args: argparse.Namespace) -> int:
    amiibos = _load_remote_amiibos(getattr(args, "series", None), getattr(args, "character", None))
    downloaded, skipped = download_images(amiibos, args.output, overwrite=args.overwrite)
    print(f"Downloaded {downloaded} images, skipped {skipped} -> {args.output}")
    return 0



def run_stage_desktop(args: argparse.Namespace) -> int:
    desktop = Path.home() / "Desktop" / args.name / DEFAULT_SD_NFC_DIR / "amiibo"
    desktop.mkdir(parents=True, exist_ok=True)
    try:
        count = import_nfc_files(args.nfc_source, desktop, overwrite=True)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(str(error))
        return 2
    print(f"Staged {count} NFC files -> {desktop}")
    print(f"Use the Flipper desktop app to copy ~/Desktop/{args.name}/nfc/ to your SD card.")
    return 0



def run_pick(args: argparse.Namespace) -> int:
    amiibos = fetch_amiibos()
    if args.by == "series":
        selected = pick_series(amiibos)
    else:
        selected = pick_characters(amiibos)
    if not selected:
        print("Nothing selected.")
        return 1
    count = export_entries(selected, args.output, file_format=args.format)
    print(f"Exported {count} entries -> {args.output}")
    return 0



def run_convert_bin(args: argparse.Namespace) -> int:
    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return 2

    summary = convert_directory(
        args.source,
        args.output,
        overwrite=args.overwrite,
        flatten=args.flatten,
    )
    print(f"Converted {summary.converted} files, skipped {summary.skipped_total} -> {args.output}")
    if summary.skipped_existing or summary.skipped_invalid_size:
        print(f"  skipped existing: {summary.skipped_existing}")
        print(f"  skipped invalid size: {summary.skipped_invalid_size}")
    if args.verbose:
        print(f"  scanned: {summary.scanned}")
        print(f"  source root: {summary.source_root}")
        print(f"  output root: {summary.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
