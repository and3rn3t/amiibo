#!/usr/bin/env bash
# Demo: New amiibo-flipper Features (Config, Archive Import, Duplicate Detection)

set -e

DEMO_DIR="/tmp/amiibo-demo-$$"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  amiibo-flipper Demo: Config, Archive Import, Duplicates     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Create a config file
echo "1️⃣  Creating config file (.amiibo.yml)..."
cat > .amiibo.yml << 'EOF'
# Example amiibo-flipper configuration
amiibo_json: data/amiibo.json
export_dir: flipper-export/apps_data/amiibo_db
sd_nfc_dir: nfc/amiibo
desktop_name: flipper-amiibo

# Optional: Set defaults to avoid repeating flags
default_series: ~  # "Mario", "Zelda", etc.
default_character: ~  # "Link", "Mario", etc.
EOF
echo "✓ Created .amiibo.yml"
echo ""

# 2. Create sample archive
echo "2️⃣  Creating sample ZIP archive with test files..."
mkdir -p sample-amiibo/mario sample-amiibo/zelda
python3 << 'EOF'
import zipfile
import os

# Create sample .bin files (540 bytes, valid NTAG215 size)
os.makedirs("sample-amiibo/mario", exist_ok=True)
os.makedirs("sample-amiibo/zelda", exist_ok=True)

# Create test files
with open("sample-amiibo/mario/mario-1.bin", "wb") as f:
    f.write(b"MARIO_BIN" + b"\x00" * 531)  # 540 bytes

with open("sample-amiibo/mario/mario-2.bin", "wb") as f:
    f.write(b"MARIO_BIN" + b"\x00" * 531)  # Same content = duplicate

with open("sample-amiibo/zelda/link-1.bin", "wb") as f:
    f.write(b"ZELDA_BIN" + b"\x00" * 531)  # Different content

# Create ZIP
with zipfile.ZipFile("amiibo-collection.zip", "w") as zf:
    zf.write("sample-amiibo/mario/mario-1.bin", arcname="mario/mario-1.bin")
    zf.write("sample-amiibo/mario/mario-2.bin", arcname="mario/mario-2.bin")
    zf.write("sample-amiibo/zelda/link-1.bin", arcname="zelda/link-1.bin")

print("✓ Created amiibo-collection.zip with 3 test files")
EOF
echo ""

# 3. Import archive
echo "3️⃣  Importing archive with conversion..."
amiibo-flipper import-archive \
  --archive amiibo-collection.zip \
  --output nfc/amiibo \
  --check-duplicates
echo ""

# 4. Show directory structure
echo "4️⃣  Converted NFC structure:"
find nfc -type f | head -10 || echo "No files created (normal if CLI not available)"
echo ""

# 5. Check for duplicates
echo "5️⃣  Checking for duplicates..."
amiibo-flipper check-duplicates --source nfc/amiibo --report duplicates.json || true
echo ""

# 6. Show report
echo "6️⃣  Duplicate report:"
if [ -f duplicates.json ]; then
  cat duplicates.json
fi
echo ""

# Cleanup
cd /
rm -rf "$DEMO_DIR"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Demo complete! Features ready to use.                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
