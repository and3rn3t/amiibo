#!/usr/bin/env zsh
# build-macos.sh — Build amiibo-flipper.app and (optionally) a .dmg for macOS
# Usage: ./build-macos.sh [--dmg]
set -euo pipefail

SCRIPT_DIR="${0:a:h}"
cd "$SCRIPT_DIR"

APP_NAME="amiibo-flipper"
SPEC_FILE="amiibo_flipper_gui.spec"
DIST_DIR="dist"
BUILD_DIR="build_pyinstaller"

echo "==> Activating venv..."
source .venv/bin/activate

echo "==> Installing/upgrading build deps..."
pip install pyinstaller -q

echo "==> Repairing Qt plugin visibility (macOS)..."
python - <<'PY'
import subprocess, sys
from pathlib import Path
try:
    import PyQt6
    root = Path(PyQt6.__file__).resolve().parent
    targets = [
        root,
        root / "Qt6",
        root / "Qt6" / "plugins",
        root / "Qt6" / "plugins" / "platforms",
    ]
    files = list((root / "Qt6" / "plugins" / "platforms").glob("*.dylib"))
    for p in [*targets, *files]:
        if p.exists():
            subprocess.run(["chflags", "nohidden", str(p)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for stale in (root / "Qt6" / "plugins" / "platforms").glob("* 2.dylib"):
        stale.unlink(missing_ok=True)
    print("  Qt plugins: OK")
except Exception as e:
    print(f"  Qt repair skipped: {e}")
PY

echo "==> Running PyInstaller..."
pyinstaller "$SPEC_FILE" \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    --noconfirm \
    --clean

APP_PATH="$DIST_DIR/$APP_NAME.app"

if [[ ! -d "$APP_PATH" ]]; then
    echo "ERROR: $APP_PATH not created — check PyInstaller output above."
    exit 1
fi

echo ""
echo "==> Cleaning extended attributes and signing bundle..."
find "$APP_PATH" -name '._*' -delete 2>/dev/null || true
find "$APP_PATH" -name '.DS_Store' -delete 2>/dev/null || true
xattr -cr "$APP_PATH"
codesign --force --deep --sign - "$APP_PATH" && echo "  Signed OK" || echo "  Signing failed (app may still work locally)"

echo ""
echo "✓ App bundle built: $APP_PATH"

# Optional: package into a .dmg if --dmg flag passed
if [[ "${1:-}" == "--dmg" ]]; then
    echo ""
    echo "==> Creating .dmg..."
    DMG_PATH="$DIST_DIR/$APP_NAME.dmg"
    if command -v hdiutil &>/dev/null; then
        hdiutil create \
            -volname "$APP_NAME" \
            -srcfolder "$APP_PATH" \
            -ov \
            -format UDZO \
            "$DMG_PATH"
        echo "✓ Disk image created: $DMG_PATH"
    else
        echo "  hdiutil not found, skipping .dmg creation."
    fi
fi

echo ""
echo "Done. To run the app:"
echo "  open $APP_PATH"
