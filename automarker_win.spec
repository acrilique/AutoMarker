# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
         ('icon.png', '.'),
         ('icon.ico', '.'),
         ('extension_installer_mac.sh', '.'),
         ('extension_installer_win.bat', '.'),
         ('README.md', '.'),
         ('AutoMarker.zxp', '.'),
         ('DaVinciResolveScript.py', '.'),
         ('Inter.ttf','.'),
         ('arrow_left.svg','.'),
         ('arrow_right.svg','.')
         ]

a = Analysis(
    ['automarkerQt.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
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
    name='AutoMarker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='automarker',
)
