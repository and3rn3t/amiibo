from pathlib import Path

from amiibo_flipper.nfc import import_nfc_files



def test_import_nfc_files_copies_supported_suffixes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "mario.nfc").write_text("data", encoding="utf-8")
    (source / "zelda.bin").write_bytes(b"\x00\x01")
    (source / "readme.txt").write_text("ignore", encoding="utf-8")

    target = tmp_path / "target"
    copied = import_nfc_files(source, target)

    assert copied == 2
    assert (target / "mario.nfc").exists()
    assert (target / "zelda.bin").exists()
    assert not (target / "readme.txt").exists()



def test_import_nfc_files_respects_overwrite_false(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "mario.nfc").write_text("new", encoding="utf-8")

    target = tmp_path / "target"
    target.mkdir()
    existing = target / "mario.nfc"
    existing.write_text("old", encoding="utf-8")

    copied = import_nfc_files(source, target, overwrite=False)

    assert copied == 0
    assert existing.read_text(encoding="utf-8") == "old"
