#!/usr/bin/env zsh
# build-macos.sh — Build amiibo-flipper.app and optionally sign/notarize for macOS.
# Usage:
#   ./build-macos.sh
#   ./build-macos.sh --dmg
#
# Optional env vars:
#   APPLE_SIGN_IDENTITY   Developer ID Application identity name
#   APPLE_TEAM_ID         Apple team identifier used for signing metadata
#   APPLE_NOTARY_PROFILE  notarytool keychain profile name for notarization
set -euo pipefail

SCRIPT_DIR="${0:a:h}"
cd "$SCRIPT_DIR"

APP_NAME="amiibo-flipper"
SPEC_FILE="amiibo_flipper_gui.spec"
DIST_DIR="dist"
BUILD_DIR="build_pyinstaller"
ASSETS_DIR="assets"
ICONSET_DIR="$ASSETS_DIR/icon.iconset"
ICON_PNG="$ASSETS_DIR/icon.png"
ICON_ICNS="$ASSETS_DIR/icon.icns"
SIGN_IDENTITY="${APPLE_SIGN_IDENTITY:-}"
TEAM_ID="${APPLE_TEAM_ID:-}"
NOTARY_PROFILE="${APPLE_NOTARY_PROFILE:-}"
STAGE_ROOT="$DIST_DIR/.stage"

find_developer_id_identity() {
    local team_id="$1"
    security find-identity -v -p codesigning 2>/dev/null \
        | grep 'Developer ID Application:' \
        | grep "(${team_id})" \
        | sed -E 's/.*"(.+)"/\1/' \
        | head -n 1
}

if [[ -z "$SIGN_IDENTITY" && -n "$TEAM_ID" ]]; then
    SIGN_IDENTITY="$(find_developer_id_identity "$TEAM_ID")"
    if [[ -n "$SIGN_IDENTITY" ]]; then
        echo "==> Using Developer ID identity from Team ID: $SIGN_IDENTITY"
    else
        echo "ERROR: No 'Developer ID Application' identity found in Keychain for team $TEAM_ID"
        echo "Run: security find-identity -v -p codesigning"
        exit 1
    fi
fi

if [[ -n "$SIGN_IDENTITY" && -n "$TEAM_ID" && "$SIGN_IDENTITY" != *"(${TEAM_ID})"* ]]; then
    echo "ERROR: APPLE_SIGN_IDENTITY does not match APPLE_TEAM_ID ($TEAM_ID)"
    echo "Identity: $SIGN_IDENTITY"
    exit 1
fi

if [[ -n "$NOTARY_PROFILE" && -z "$SIGN_IDENTITY" ]]; then
    echo "ERROR: APPLE_NOTARY_PROFILE requires Developer ID signing."
    echo "Set APPLE_SIGN_IDENTITY or APPLE_TEAM_ID before notarizing."
    exit 1
fi

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

export QT_PLUGIN_PATH="$PWD/.venv/lib/python3.14/site-packages/PyQt6/Qt6/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$PWD/.venv/lib/python3.14/site-packages/PyQt6/Qt6/plugins/platforms"
export QT_QPA_PLATFORM="offscreen"

echo "==> Generating app icon..."
mkdir -p "$ASSETS_DIR" "$ICONSET_DIR"
python scripts/generate_app_icon.py

for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
done
sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 64 64 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
cp "$ICON_PNG" "$ICONSET_DIR/icon_512x512@2x.png"
iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"

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
rm -rf "$STAGE_ROOT"
mkdir -p "$STAGE_ROOT"
STAGED_APP_PATH="$STAGE_ROOT/$APP_NAME.app"
ditto "$APP_PATH" "$STAGED_APP_PATH"
find "$STAGED_APP_PATH" -name '._*' -delete 2>/dev/null || true
find "$STAGED_APP_PATH" -name '.DS_Store' -delete 2>/dev/null || true
xattr -cr "$STAGED_APP_PATH"
if [[ -n "$SIGN_IDENTITY" ]]; then
    codesign --force --deep --options runtime --entitlements macos-entitlements.plist --sign "$SIGN_IDENTITY" "$STAGED_APP_PATH" && echo "  Developer ID signed OK" || echo "  Developer ID signing failed"
else
    codesign --force --deep --sign - "$STAGED_APP_PATH" && echo "  Ad-hoc signed OK" || echo "  Ad-hoc signing failed"
fi
rm -rf "$APP_PATH"
mv "$STAGED_APP_PATH" "$APP_PATH"
rm -rf "$STAGE_ROOT"

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
        if [[ -n "$SIGN_IDENTITY" ]]; then
            xattr -cr "$DMG_PATH"
            codesign --force --sign "$SIGN_IDENTITY" "$DMG_PATH" && echo "  DMG signed OK" || echo "  DMG signing failed"
        fi
        if [[ -n "$NOTARY_PROFILE" ]]; then
            echo "==> Notarizing DMG..."
            xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_PROFILE" --wait
            xcrun stapler staple "$DMG_PATH"
            xcrun stapler validate "$DMG_PATH"
            echo "  DMG notarized and stapled"
        fi
        echo "✓ Disk image created: $DMG_PATH"
    else
        echo "  hdiutil not found, skipping .dmg creation."
    fi
fi

echo ""
echo "Done. To run the app:"
echo "  open $APP_PATH"
