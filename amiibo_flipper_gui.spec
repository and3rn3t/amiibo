# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for amiibo-flipper GUI — macOS .app bundle."""

import sys
from pathlib import Path
import PyQt6

PYQT6_ROOT = Path(PyQt6.__file__).resolve().parent
QT6_ROOT = PYQT6_ROOT / "Qt6"
PLUGINS_ROOT = QT6_ROOT / "plugins"
FRAMEWORKS_ROOT = QT6_ROOT / "lib"
ICON_PATH = Path("assets/icon.icns")

# Collect all Qt6 plugin directories we need
qt_plugins = [
    ("platforms", "PyQt6/Qt6/plugins/platforms"),
    ("platformthemes", "PyQt6/Qt6/plugins/platformthemes"),
    ("styles", "PyQt6/Qt6/plugins/styles"),
    ("imageformats", "PyQt6/Qt6/plugins/imageformats"),
    ("iconengines", "PyQt6/Qt6/plugins/iconengines"),
    ("accessible", "PyQt6/Qt6/plugins/accessible"),
]

datas = []
for plugin_dir, dest in qt_plugins:
    src = PLUGINS_ROOT / plugin_dir
    if src.exists():
        datas.append((str(src), dest))

# Include data directory if it exists
data_dir = Path("data")
if data_dir.exists():
    datas.append(("data", "data"))

block_cipher = None

a = Analysis(
    ["amiibo_flipper/gui/main_window.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "amiibo_flipper",
        "amiibo_flipper.gui",
        "amiibo_flipper.gui.tabs",
        "amiibo_flipper.gui.tabs.converter",
        "amiibo_flipper.gui.tabs.batch_runner",
        "amiibo_flipper.gui.tabs.watch_monitor",
        "amiibo_flipper.gui.tabs.duplicates",
        "amiibo_flipper.gui.tabs.dashboard",
        "amiibo_flipper.gui.tabs.settings_panel",
        "amiibo_flipper.gui.settings",
        "amiibo_flipper.gui.widgets",
        "amiibo_flipper.parallel",
        "amiibo_flipper.archive",
        "amiibo_flipper.batch",
        "amiibo_flipper.duplicates",
        "amiibo_flipper.converter",
        "yaml",
        "watchdog",
        "watchdog.observers",
        "watchdog.events",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="amiibo-flipper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="amiibo-flipper",
)

app = BUNDLE(
    coll,
    name="amiibo-flipper.app",
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
    bundle_identifier="com.andernet.amiibo-flipper",
    version="0.1.0",
    info_plist={
        "CFBundleName": "amiibo-flipper",
        "CFBundleDisplayName": "amiibo-flipper",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "© 2025 andernet",
        "LSMinimumSystemVersion": "11.0",
        "LSApplicationCategoryType": "public.app-category.utilities",
        "NSRequiresAquaSystemAppearance": False,
    },
)
