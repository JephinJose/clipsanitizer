# PyInstaller spec: bundles main.py + dropzone.py + filemeta.py + sanitize.py
# into one macOS .app that runs as a menu-bar-only agent (no Dock icon).
# Build with: pyinstaller ClipSanitizer.spec
block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["dropzone", "filemeta", "sanitize"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClipSanitizer",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ClipSanitizer",
)

app = BUNDLE(
    coll,
    name="ClipSanitizer.app",
    icon=None,
    bundle_identifier="com.clipsanitizer.app",
    info_plist={
        "LSUIElement": True,  # menu-bar-only agent, no Dock icon/app switcher entry
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
    },
)
