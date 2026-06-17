#!/usr/bin/env zsh
# notarize-macos.sh — Submit an already-built .app or .dmg for notarization and staple it.
# Required env:
#   APPLE_NOTARY_PROFILE   Name of notarytool keychain profile
# Optional env:
#   APP_PATH               Default: dist/amiibo-flipper.app
#   DMG_PATH               Default: dist/amiibo-flipper.dmg
# Usage:
#   ./notarize-macos.sh app
#   ./notarize-macos.sh dmg
set -euo pipefail

SCRIPT_DIR="${0:a:h}"
cd "$SCRIPT_DIR"

TARGET="${1:-}"
PROFILE="${APPLE_NOTARY_PROFILE:-}"
APP_PATH="${APP_PATH:-dist/amiibo-flipper.app}"
DMG_PATH="${DMG_PATH:-dist/amiibo-flipper.dmg}"

if [[ -z "$TARGET" || ( "$TARGET" != "app" && "$TARGET" != "dmg" ) ]]; then
  echo "Usage: ./notarize-macos.sh [app|dmg]"
  exit 1
fi

if [[ -z "$PROFILE" ]]; then
  echo "Set APPLE_NOTARY_PROFILE to a notarytool keychain profile name."
  echo "Example: xcrun notarytool store-credentials amiibo-notary --apple-id ... --team-id ... --password ..."
  exit 1
fi

ARTIFACT="$APP_PATH"
if [[ "$TARGET" == "dmg" ]]; then
  ARTIFACT="$DMG_PATH"
fi

if [[ ! -e "$ARTIFACT" ]]; then
  echo "Artifact not found: $ARTIFACT"
  exit 1
fi

echo "==> Submitting $ARTIFACT for notarization..."
xcrun notarytool submit "$ARTIFACT" --keychain-profile "$PROFILE" --wait

echo "==> Stapling ticket..."
xcrun stapler staple "$ARTIFACT"

echo "==> Verifying stapled ticket..."
if [[ "$TARGET" == "app" ]]; then
  xcrun stapler validate "$ARTIFACT"
else
  xcrun stapler validate "$ARTIFACT"
fi

echo "Done: $ARTIFACT notarized and stapled."
