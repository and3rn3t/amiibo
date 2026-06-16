from amiibo_flipper.exporter import render_text_entry, slugify_filename
from amiibo_flipper.models import Amiibo



def test_slugify_filename() -> None:
    assert slugify_filename("Mario / Smash Bros.-0000000000000002") == "Mario-Smash-Bros.-0000000000000002"



def test_render_text_entry_contains_core_fields() -> None:
    item = Amiibo(
        head="00000000",
        tail="00000002",
        name="Mario",
        amiibo_series="Super Smash Bros.",
        game_series="Mario",
        character="Mario",
        type="Figure",
        image="https://example.com/mario.png",
        release_au=None,
        release_eu="2014-11-28",
        release_jp="2014-12-06",
        release_na="2014-11-21",
    )

    text = render_text_entry(item)

    assert "Name: Mario" in text
    assert "ID: 0000000000000002" in text
    assert "Release (AU): -" in text
