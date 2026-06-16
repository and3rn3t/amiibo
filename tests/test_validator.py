from pathlib import Path

from amiibo_flipper.validator import validate_nfc_file, validate_nfc_directory, FLIPPER_NFC_MAGIC



def test_validate_nfc_file_valid(tmp_path: Path) -> None:
    f = tmp_path / "mario.nfc"
    f.write_text(f"{FLIPPER_NFC_MAGIC}\nVersion: 2\n", encoding="utf-8")
    result = validate_nfc_file(f)
    assert result.valid



def test_validate_nfc_file_invalid(tmp_path: Path) -> None:
    f = tmp_path / "bad.nfc"
    f.write_bytes(b"\x00\x01\x02\x03")
    result = validate_nfc_file(f)
    assert not result.valid
    assert result.reason



def test_validate_nfc_directory_counts(tmp_path: Path) -> None:
    (tmp_path / "good.nfc").write_text(f"{FLIPPER_NFC_MAGIC}\n", encoding="utf-8")
    (tmp_path / "bad.nfc").write_bytes(b"\xde\xad")
    results = validate_nfc_directory(tmp_path)
    assert len(results) == 2
    assert sum(1 for r in results if r.valid) == 1
