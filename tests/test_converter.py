from pathlib import Path

import pytest

from amiibo_flipper.converter import bin_to_nfc, convert_directory, NTAG215_EXPECTED_SIZE



def _make_bin() -> bytes:
    # 135 pages x 4 bytes, with a valid-looking UID in pages 0 and 1
    data = bytearray(NTAG215_EXPECTED_SIZE)
    # page 0: UID[0:3] + BCC0
    data[0:4] = [0x04, 0xAB, 0xCD, 0x00]
    # page 1: UID[3:7]
    data[4:8] = [0xEF, 0x01, 0x02, 0x03]
    return bytes(data)



def test_bin_to_nfc_uid_extraction() -> None:
    nfc = bin_to_nfc(_make_bin())
    assert "UID: 04 AB CD EF 01 02 03" in nfc



def test_bin_to_nfc_header_fields() -> None:
    nfc = bin_to_nfc(_make_bin())
    assert "Filetype: Flipper NFC device" in nfc
    assert "Device type: NTAG215" in nfc
    assert "Pages total: 135" in nfc
    assert "Page 0:" in nfc
    assert "Page 134:" in nfc



def test_bin_to_nfc_rejects_wrong_size() -> None:
    with pytest.raises(ValueError, match="Expected"):
        bin_to_nfc(b"\x00" * 100)



def test_convert_directory_preserves_tree_and_reports(tmp_path: Path) -> None:
    source = tmp_path / "source"
    nested = source / "Series A"
    nested.mkdir(parents=True)
    (nested / "mario.bin").write_bytes(_make_bin())
    (nested / "readme.txt").write_text("ignore", encoding="utf-8")

    output = tmp_path / "output"
    summary = convert_directory(source, output)

    assert summary.scanned == 1
    assert summary.converted == 1
    assert summary.skipped_total == 0
    assert (output / "Series A" / "mario.nfc").exists()



def test_convert_directory_flatten_and_skip_existing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    first = source / "first"
    second = source / "second"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "mario.bin").write_bytes(_make_bin())
    (second / "link.bin").write_bytes(_make_bin())

    output = tmp_path / "output"
    (output / "link.nfc").parent.mkdir(parents=True)
    (output / "link.nfc").write_text("already here", encoding="utf-8")

    summary = convert_directory(source, output, flatten=True)

    assert summary.scanned == 2
    assert summary.converted == 1
    assert summary.skipped_existing == 1
    assert (output / "mario.nfc").exists()
    assert (output / "link.nfc").read_text(encoding="utf-8") == "already here"



def test_convert_directory_matches_uppercase_extensions(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "mario.BIN").write_bytes(_make_bin())

    output = tmp_path / "output"
    summary = convert_directory(source, output)

    assert summary.scanned == 1
    assert summary.converted == 1
    assert (output / "mario.nfc").exists()
