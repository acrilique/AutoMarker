# -*- mode: python ; coding: utf-8 -*-

added_files = [
         ('icon.png', '.'),
         ('extension_installer_mac.sh', '.'),
         ('extension_installer_win.bat', '.'),
         ('README.md', '.'),
         ('AutoMarker.zxp', '.'),
         ('DaVinciResolveScript.py', '.')
         ]

a = Analysis(
    ['automarker.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
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
    name='AutoMarker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',
    codesign_identity='E9D38CA0B9FF902804EED51AAE0119CD2F0168E1',
    entitlements_file='entitlements.plist',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoMarker',
)
app = BUNDLE(
    coll,
    name='AutoMarker.app',
    icon='icon.png',
    bundle_identifier='com.acrilique.automarker',
)
