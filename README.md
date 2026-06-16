# amiibo-flipper

Small Python CLI to fetch amiibo metadata and export it into files that are easy to browse on a Flipper SD card.

## What this project does

- Downloads amiibo metadata from the public Amiibo API.
- Saves a local JSON cache.
- Exports one file per amiibo plus an index for quick browsing on Flipper.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Sample data included: 24 Mario series amiibo NFC dumps are in `data/Super Mario/` for testing.

Try importing them:

```bash
amiibo-flipper import-nfc --source data/Super\ Mario --sd-path /Volumes/FLIPPER
```

Fetch data:

```bash
amiibo-flipper fetch --output data/amiibo.json
```

Export Flipper-friendly files:

```bash
amiibo-flipper export --input data/amiibo.json --output flipper-export/apps_data/amiibo_db --format txt
```

Sync directly to an SD card mount:

```bash
amiibo-flipper sync --sd-path /Volumes/FLIPPER
```

Sync metadata + your existing NFC dumps together:

```bash
amiibo-flipper sync --sd-path /Volumes/FLIPPER --nfc-source ~/Downloads/amiibo-dumps
```

Import only NFC dump files:

```bash
amiibo-flipper import-nfc --source ~/Downloads/amiibo-dumps --sd-path /Volumes/FLIPPER
```

This writes to:

- `/Volumes/FLIPPER/apps_data/amiibo_db/index.json`
- `/Volumes/FLIPPER/apps_data/amiibo_db/entries/*.txt`
- `/Volumes/FLIPPER/nfc/amiibo/*.nfc` and `/Volumes/FLIPPER/nfc/amiibo/*.bin`

## NFC safety scope

This tool can copy your existing NFC dump files (`.nfc` / `.bin`) onto the SD card.
It does not generate, decrypt, clone, or modify NFC credentials/keys.
