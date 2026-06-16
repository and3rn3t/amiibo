# Advanced Features Guide

## 1. Watch Mode - Auto-Convert New Files

Watch a directory and automatically convert new `.bin` files as they appear.

### Basic Usage

```bash
# Watch for new files and convert them
amiibo-flipper watch \
  --source /path/to/new-dumps \
  --output nfc/amiibo
```

### Options

- `--source SOURCE` (required): Directory to monitor for new files
- `--output OUTPUT` (required): Directory for converted .nfc files
- `--flatten`: Write all files to one folder (no subdirectories)
- `--overwrite`: Overwrite existing files

### Example Workflow

```bash
# Terminal 1: Start watching
amiibo-flipper watch \
  --source ~/Downloads/amiibo-dumps \
  --output nfc/amiibo

# Terminal 2: Add new files as they're downloaded
cp ~/Downloads/new-amiibo.bin ~/Downloads/amiibo-dumps/
# Watch terminal automatically converts!
```

## 2. Parallel Processing - Faster Conversions

Convert many `.bin` files in parallel for better performance on large batches.

### Basic Usage

```bash
# Convert with parallel workers
amiibo-flipper convert-bin-parallel \
  --source bin-dumps/ \
  --output nfc/amiibo
```

### Options

- `--source SOURCE` (required): Directory of .bin files
- `--output OUTPUT` (required): Directory for .nfc files
- `--workers N`: Number of parallel threads (default: CPU count)
- `--overwrite`: Replace existing files

### Performance Comparison

```bash
# Sequential (default)
time amiibo-flipper convert-bin --source dumps/ --output nfc/

# Parallel (faster for large batches)
time amiibo-flipper convert-bin-parallel --source dumps/ --output nfc/ --workers 8
```

On a system with 1000 .bin files:
- Sequential: ~15 seconds
- Parallel (8 workers): ~3 seconds

## 3. Batch Mode - Chain Commands

Execute multiple commands in sequence from a YAML file for complex workflows.

### Basic Usage

```bash
# Create a batch file
cat > batch.yml << 'EOF'
commands:
  - name: fetch
    output: data/amiibo.json
  - name: export
    input: data/amiibo.json
    output: flipper-export/apps_data/amiibo_db
    series: Mario
  - name: download-images
    output: data/images
    series: Mario
EOF

# Execute batch
amiibo-flipper batch --file batch.yml
```

### Batch YAML Format

```yaml
commands:
  - name: fetch                           # Fetch amiibo API data
    output: data/amiibo.json
  
  - name: export                          # Export to Flipper format
    input: data/amiibo.json
    output: flipper-export/apps_data/amiibo_db
    series: Mario                         # Optional filters
    character: Luigi
    format: txt
  
  - name: sync                            # Sync directly to Flipper
    sd_path: /Volumes/FLIP
    format: txt
    nfc_source: nfc/amiibo
    overwrite_nfc: false
  
  - name: convert-bin                     # Convert bin to nfc
    source: bin-dumps/
    output: nfc/amiibo
    flatten: false
    overwrite: false
  
  - name: download-images                 # Download artwork
    output: data/images
    series: Zelda
    overwrite: false
  
  - name: inventory                       # Generate report
    nfc_sources: [nfc/amiibo]
    output: inventory-report.txt
    series: Mario
```

### Advanced Workflow Example

```yaml
# full-sync.yml: Complete sync workflow
commands:
  # 1. Fetch latest data from API
  - name: fetch
    output: data/amiibo.json
  
  # 2. Import previous collection
  - name: import-archive
    archive: old-collection.zip
    output: nfc/amiibo
    check_duplicates: true
  
  # 3. Convert any new bin files in parallel
  - name: convert-bin-parallel
    source: /tmp/new-bins
    output: nfc/amiibo
    workers: 8
    overwrite: true
  
  # 4. Export metadata to Flipper
  - name: export
    input: data/amiibo.json
    output: flipper-export/apps_data/amiibo_db
  
  # 5. Sync everything to device
  - name: sync
    sd_path: /Volumes/FLIP
    nfc_source: nfc/amiibo
    format: txt
```

Run it:
```bash
amiibo-flipper batch --file full-sync.yml -v
```

## Combining Features

### Example: Import Archive + Detect Duplicates + Watch for Updates

```bash
#!/bin/bash

# 1. Import archive and check for duplicates
amiibo-flipper import-archive \
  --archive my-collection.zip \
  --output nfc/amiibo \
  --check-duplicates

# 2. Start watching for new files
amiibo-flipper watch \
  --source ~/Downloads/new-amiibo \
  --output nfc/amiibo \
  --flatten
```

### Example: Batch Sync with Parallel Processing

```yaml
# fast-sync.yml
commands:
  - name: convert-bin-parallel
    source: to-convert/
    output: nfc/amiibo
    workers: 8
  
  - name: export
    input: data/amiibo.json
    output: flipper-export/apps_data/amiibo_db
  
  - name: sync
    sd_path: /Volumes/FLIP
    nfc_source: nfc/amiibo
    format: txt
```

## Performance Tips

- **Watch mode**: Best for ongoing collection updates, low resource usage
- **Parallel processing**: Use for batches > 100 files on multi-core systems
- **Batch mode**: Automate multi-step workflows, ideal for CI/CD pipelines
- **Combine all three**: Import large archive → parallel convert → watch for new files

## Troubleshooting

### Watch mode not detecting files
- Ensure files are actually written to disk (not still downloading)
- Some editors may not trigger file creation events; try moving files instead
- Check file permissions

### Parallel conversion slower than expected
- Verify `--workers` matches your CPU cores: `python -c "import os; print(os.cpu_count())"`
- I/O bottleneck: faster storage (SSD) helps more than more workers
- Monitor CPU usage to confirm parallelization is active

### Batch mode errors
- Check YAML syntax: `python -m yaml batch.yml` should parse without error
- Verify all required options are set (see YAML format above)
- Use `-vv` flag for detailed debugging: `amiibo-flipper batch --file batch.yml -vv`

## See Also

- [CONFIG.md](CONFIG.md) - Configuration file support
- [README.md](README.md) - Main documentation
