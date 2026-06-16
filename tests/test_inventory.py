from pathlib import Path

from amiibo_flipper.inventory import build_inventory, render_inventory_report
from amiibo_flipper.models import Amiibo


def _make_amiibo(name: str, series: str = "Test", character: str = "Hero") -> Amiibo:
    return Amiibo(
        head="00000000",
        tail="00000001",
        name=name,
        amiibo_series=series,
        game_series=series,
        character=character,
        type="Figure",
        image="",
        release_au=None,
        release_eu=None,
        release_jp=None,
        release_na=None,
    )



def test_inventory_have_by_name(tmp_path: Path) -> None:
    (tmp_path / "Mario.nfc").write_text("data", encoding="utf-8")
    amiibos = [_make_amiibo("Mario"), _make_amiibo("Luigi")]
    report = build_inventory(amiibos, [tmp_path])
    assert any(a.name == "Mario" for a in report.have)
    assert any(a.name == "Luigi" for a in report.missing)



def test_inventory_render_contains_sections(tmp_path: Path) -> None:
    amiibos = [_make_amiibo("Mario")]
    report = build_inventory(amiibos, [])
    text = render_inventory_report(report)
    assert "Have" in text
    assert "Missing" in text
