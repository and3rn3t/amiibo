from pathlib import Path

from amiibo_flipper.models import Amiibo
from amiibo_flipper.organizer import organize_nfc_files


def _make_amiibo(name: str, series: str) -> Amiibo:
    return Amiibo(
        head="00000000",
        tail="00000002",
        name=name,
        amiibo_series=series,
        game_series=series,
        character=name,
        type="Figure",
        image="",
        release_au=None,
        release_eu=None,
        release_jp=None,
        release_na=None,
    )



def test_organize_matched_goes_to_series_folder(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "Mario.nfc").write_text("x", encoding="utf-8")

    output = tmp_path / "output"
    amiibos = [_make_amiibo("Mario", "Super Mario")]
    renamed, as_is = organize_nfc_files(source, output, amiibos)

    assert renamed == 1
    assert as_is == 0
    series_dir = output / "Super-Mario"
    assert any(series_dir.rglob("*.nfc"))



def test_organize_unmatched_goes_to_unsorted(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "unknown_thing.nfc").write_text("x", encoding="utf-8")

    output = tmp_path / "output"
    renamed, as_is = organize_nfc_files(source, output, amiibos=[])

    assert renamed == 0
    assert as_is == 1
    assert (output / "unsorted" / "unknown_thing.nfc").exists()
