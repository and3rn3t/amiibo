from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from amiibo_flipper.archive import import_archive
from amiibo_flipper.batch import BatchRunner, create_batch_from_yaml
from amiibo_flipper.client import fetch_amiibos
from amiibo_flipper.config import load_config
from amiibo_flipper.converter import convert_directory
from amiibo_flipper.duplicates import format_duplicates_for_display, save_duplication_report, scan_for_duplicates
from amiibo_flipper.exporter import export_entries
from amiibo_flipper.images import download_images
from amiibo_flipper.inventory import build_inventory, render_inventory_report
from amiibo_flipper.models import Amiibo, amiibo_from_api
from amiibo_flipper.nfc import import_nfc_files
from amiibo_flipper.organizer import organize_nfc_files
from amiibo_flipper.parallel import convert_files_parallel, ConversionJob
from amiibo_flipper.picker import pick_characters, pick_series
from amiibo_flipper.validator import validate_nfc_directory



DEFAULT_AMIIBO_JSON = Path("data/amiibo.json")
DEFAULT_EXPORT_DIR = Path("flipper-export/apps_data/amiibo_db")
DEFAULT_SD_NFC_DIR = Path("nfc/amiibo")
DEFAULT_DESKTOP_NAME = "flipper-amiibo"

# Global config loaded on startup
_CONFIG = None


def get_config():
    """Get the loaded configuration."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_config()
    return _CONFIG



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

    # import-archive
    arch_parser = subparsers.add_parser(
        "import-archive",
        help="Extract and convert amiibo files from a ZIP archive",
    )
    arch_parser.add_argument("--archive", type=Path, required=True, help="Path to ZIP archive")
    arch_parser.add_argument("--output", type=Path, required=True, help="Output directory for converted .nfc files")
    arch_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .nfc files")
    arch_parser.add_argument(
        "--flatten",
        action="store_true",
        help="Flatten directory structure into a single folder",
    )
    arch_parser.add_argument(
        "--check-duplicates",
        action="store_true",
        help="Scan for duplicate files after import",
    )
    arch_parser.set_defaults(func=run_import_archive)

    # check-duplicates
    dup_parser = subparsers.add_parser(
        "check-duplicates",
        help="Scan directory for duplicate NFC/BIN files by content hash",
    )
    dup_parser.add_argument("--source", type=Path, required=True, help="Directory to scan")
    dup_parser.add_argument("--report", type=Path, help="Save results to JSON file")
    dup_parser.set_defaults(func=run_check_duplicates)

    # watch
    watch_parser = subparsers.add_parser(
        "watch",
        help="Watch directory and auto-convert new .bin files",
    )
    watch_parser.add_argument("--source", type=Path, required=True, help="Directory to monitor")
    watch_parser.add_argument("--output", type=Path, required=True, help="Output directory for .nfc files")
    watch_parser.add_argument("--flatten", action="store_true", help="Flatten output directory structure")
    watch_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    watch_parser.set_defaults(func=run_watch)

    # batch
    batch_parser = subparsers.add_parser(
        "batch",
        help="Execute a batch of commands from YAML file",
    )
    batch_parser.add_argument("--file", type=Path, required=True, help="YAML file with batch commands")
    batch_parser.set_defaults(func=run_batch)

    # convert-bin-parallel
    conv_par_parser = subparsers.add_parser(
        "convert-bin-parallel",
        help="Convert .bin files in parallel (faster for large batches)",
    )
    conv_par_parser.add_argument("--source", type=Path, required=True, help="Directory of .bin files")
    conv_par_parser.add_argument("--output", type=Path, required=True, help="Destination directory for .nfc files")
    conv_par_parser.add_argument("--workers", type=int, help="Number of parallel workers (default: CPU count)")
    conv_par_parser.add_argument("--overwrite", action="store_true")
    conv_par_parser.set_defaults(func=run_convert_bin_parallel)

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


def run_import_archive(args: argparse.Namespace) -> int:
    """Import and convert amiibo files from a ZIP archive."""
    if not args.archive.exists():
        print(f"Archive not found: {args.archive}")
        return 2

    try:
        result = import_archive(
            archive_path=args.archive,
            output_dir=args.output,
            overwrite=args.overwrite,
            flatten=args.flatten,
        )

        print(f"Imported archive: {args.archive.name}")
        print(f"  Converted: {result.converted_count}")
        print(f"  Skipped: {result.skipped_count}")
        print(f"  Output: {result.extract_dir}")

        if result.extraction_errors and args.verbose:
            print(f"  Extraction errors: {len(result.extraction_errors)}")
            for error in result.extraction_errors[:5]:
                print(f"    - {error}")

        if args.check_duplicates:
            print("\nScanning for duplicates...")
            dup_result = scan_for_duplicates(args.output)
            print(format_duplicates_for_display(dup_result))

        return 0

    except Exception as e:
        print(f"Import failed: {e}")
        return 2


def run_check_duplicates(args: argparse.Namespace) -> int:
    """Check for duplicate amiibo files by content hash."""
    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return 2

    result = scan_for_duplicates(args.source)
    print(format_duplicates_for_display(result))

    if args.report:
        save_duplication_report(result, args.report)
        print(f"\nReport saved to {args.report}")

    return 0 if result.duplicates_found == 0 else 1


def run_watch(args: argparse.Namespace) -> int:
    """Watch directory and auto-convert new .bin files."""
    try:
        from amiibo_flipper.watch import watch_directory
    except ImportError:
        print("Error: watchdog package required for watch mode")
        print("Install with: pip install watchdog")
        return 2

    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return 2

    args.output.mkdir(parents=True, exist_ok=True)

    def convert_single_file(source, output_dir, flatten, overwrite):
        """Convert a single file for watch mode."""
        from amiibo_flipper.converter import bin_to_nfc

        try:
            data = source.read_bytes()
            if len(data) != 540:
                return {"success": False, "reason": f"Invalid size: {len(data)}"}

            nfc_content = bin_to_nfc(data)

            if flatten:
                output_file = output_dir / f"{source.stem}.nfc"
            else:
                rel_path = source.relative_to(args.source)
                output_file = output_dir / rel_path.with_suffix(".nfc")

            if output_file.exists() and not overwrite:
                return {"success": False, "reason": "File exists"}

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(nfc_content)
            return {"success": True}

        except Exception as e:
            return {"success": False, "reason": str(e)}

    stats = watch_directory(
        source_dir=args.source,
        output_dir=args.output,
        convert_func=convert_single_file,
        flatten=args.flatten,
        overwrite=args.overwrite,
    )

    print("\n👁️  Watch session complete")
    print(f"  Converted: {stats.files_converted}")
    print(f"  Skipped: {stats.files_skipped}")
    print(f"  Errors: {stats.errors}")
    print(f"  Duration: {stats.session_duration:.1f}s")
    return 0 if stats.errors == 0 else 1


def run_batch(args: argparse.Namespace) -> int:
    """Execute batch commands from YAML file."""
    if not args.file.exists():
        print(f"Batch file not found: {args.file}")
        return 2

    try:
        yaml_content = args.file.read_text()
        commands = create_batch_from_yaml(yaml_content)

        if not commands:
            print("No commands found in batch file")
            return 0

        runner = BatchRunner()
        result = runner.run(commands)

        print("\n📦 Batch execution complete")
        print(f"  Commands run: {result.commands_run}")
        print(f"  Succeeded: {result.commands_succeeded}")
        print(f"  Failed: {result.commands_failed}")

        if result.failures:
            print("\n❌ Failures:")
            for cmd_name, error in result.failures:
                print(f"  {cmd_name}: {error}")

        return 0 if result.commands_failed == 0 else 1

    except Exception as e:
        print(f"Batch execution failed: {e}")
        return 2


def run_convert_bin_parallel(args: argparse.Namespace) -> int:
    """Convert .bin files in parallel using thread pool."""
    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return 2

    # Collect all .bin files
    bin_files = list(args.source.rglob("*.bin")) + list(args.source.rglob("*.BIN"))

    if not bin_files:
        print("No .bin files found")
        return 0

    # Create conversion jobs
    jobs = []
    for bin_file in bin_files:
        output_file = args.output / bin_file.relative_to(args.source).with_suffix(".nfc")
        jobs.append(ConversionJob(
            source_file=bin_file,
            output_file=output_file,
            overwrite=args.overwrite,
        ))

    print(f"Converting {len(jobs)} files in parallel...")
    result = convert_files_parallel(jobs, max_workers=args.workers)

    print(f"✓ Converted {result.succeeded} files")
    print(f"⊘ Skipped {result.skipped} files")
    if result.failed > 0:
        print(f"✗ Failed {result.failed} files")
        for file_path, error in result.errors[:5]:
            print(f"    {file_path.name}: {error}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
