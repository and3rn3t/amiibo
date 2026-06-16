# amiibo-flipper Configuration Reference

Store your default settings in `.amiibo.yml` or `.amiibo.json` in your project root to avoid typing repeated flags.

## Example Configuration (.amiibo.yml)

```yaml
# Path to cached amiibo API data (created by 'fetch' command)
amiibo_json: data/amiibo.json

# Export directory for Flipper database
export_dir: flipper-export/apps_data/amiibo_db

# Flipper SD card NFC directory
sd_nfc_dir: nfc/amiibo

# Desktop staging folder name
desktop_name: flipper-amiibo

# Default filters (optional, can override per command)
default_series: Mario           # Filter to this series by default
default_character: Luigi        # Filter to this character by default

# Reserved for future extensions
extra_options: {}
```

## Creating a Config File

Generate a template:

```bash
python -m amiibo_flipper.config --init
```

Or manually create `.amiibo.yml` or `.amiibo.json`.

## New Features

### 1. Import Archives (ZIP → NFC)

Convert an entire ZIP archive of amiibo dumps in one command:

```bash
# Basic import
amiibo-flipper import-archive --archive amiibo-collection.zip --output nfc/amiibo

# With duplicate detection
amiibo-flipper import-archive \
  --archive amiibo-collection.zip \
  --output nfc/amiibo \
  --flatten \
  --check-duplicates

# Overwrite existing files
amiibo-flipper import-archive \
  --archive update.zip \
  --output nfc/amiibo \
  --overwrite
```

**Options:**
- `--archive PATH` (required): ZIP file to import
- `--output PATH` (required): Directory for converted files
- `--flatten`: Write all files to one folder (no subdirectories)
- `--check-duplicates`: Scan for duplicate files after import
- `--overwrite`: Replace existing .nfc files (default: skip)

### 2. Detect Duplicates

Find duplicate amiibo files by content hash:

```bash
# Quick scan
amiibo-flipper check-duplicates --source nfc/amiibo

# Save report to file
amiibo-flipper check-duplicates \
  --source nfc/amiibo \
  --report duplicates-report.json

# Verbose output
amiibo-flipper check-duplicates --source nfc/amiibo -v
```

**Options:**
- `--source PATH` (required): Directory to scan for duplicates
- `--report PATH` (optional): Save JSON report to file
- `-v`: Verbose output with details

**Report Format (JSON):**
```json
{
  "total_files": 1000,
  "duplicates_found": 5,
  "duplicate_groups": [
    ["path/to/file1.nfc", "path/to/file2.nfc"],
    ["path/to/file3.nfc", "path/to/file4.nfc", "path/to/file5.nfc"]
  ]
}
```

### 3. Configuration Support

Now all commands respect your `.amiibo.yml` defaults:

```bash
# Without config, you'd need:
amiibo-flipper export --input data/amiibo.json --output flipper-export/apps_data/amiibo_db

# With config, just:
amiibo-flipper export

# Config defaults can still be overridden per command:
amiibo-flipper export --output /custom/output/path
```

## Typical Workflow

1. **Create config**
   ```bash
   # Generate template
   amiibo-flipper config --init
   # Edit .amiibo.yml with your paths
   ```

2. **Import collection**
   ```bash
   amiibo-flipper import-archive \
     --archive amiibo-dumps.zip \
     --output nfc/amiibo \
     --check-duplicates
   ```

3. **Check for duplicates**
   ```bash
   amiibo-flipper check-duplicates --source nfc/amiibo --report report.json
   ```

4. **Organize and stage**
   ```bash
   amiibo-flipper organize --source nfc/amiibo --output nfc/organized
   amiibo-flipper stage-desktop --nfc-source nfc/organized
   ```

5. **Sync to Flipper**
   ```bash
   amiibo-flipper sync --sd-path /Volumes/FLIP --format txt
   ```

## Tips

- Use `--flatten` when importing large archives to avoid deep directory nesting
- Run `check-duplicates --report report.json` to track duplicate changes over time
- Config files are optional; all CLI flags work without them
- Config file location is auto-detected: `.amiibo.yml` or `.amiibo.json` in current directory
