from __future__ import annotations

from amiibo_flipper.models import Amiibo



def pick_series(amiibos: list[Amiibo]) -> list[Amiibo]:
    series_names = sorted({a.amiibo_series for a in amiibos})
    print("\nAvailable amiibo series:")
    for i, name in enumerate(series_names, 1):
        count = sum(1 for a in amiibos if a.amiibo_series == name)
        print(f"  {i:3}. {name}  ({count} amiibo)")

    print("\nEnter series numbers to include (e.g. 1 3 5), or 'all' for everything:")
    raw = input("> ").strip()

    if raw.lower() == "all":
        return amiibos

    chosen: set[str] = set()
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(series_names):
                chosen.add(series_names[idx])
        except ValueError:
            pass

    selected = [a for a in amiibos if a.amiibo_series in chosen]
    print(f"\nSelected {len(selected)} amiibo from {len(chosen)} series.")
    return selected



def pick_characters(amiibos: list[Amiibo]) -> list[Amiibo]:
    characters = sorted({a.character for a in amiibos})
    print("\nAvailable characters:")
    for i, name in enumerate(characters, 1):
        count = sum(1 for a in amiibos if a.character == name)
        print(f"  {i:3}. {name}  ({count} variant{'s' if count != 1 else ''})")

    print("\nEnter character numbers to include (e.g. 1 3 5), or 'all':")
    raw = input("> ").strip()

    if raw.lower() == "all":
        return amiibos

    chosen: set[str] = set()
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(characters):
                chosen.add(characters[idx])
        except ValueError:
            pass

    selected = [a for a in amiibos if a.character in chosen]
    print(f"\nSelected {len(selected)} amiibo for {len(chosen)} character(s).")
    return selected
