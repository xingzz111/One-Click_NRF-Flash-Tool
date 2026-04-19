# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/XING/Documents/A193/DFU/tools/oneClickTool/nrf_oneclick_program.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/XING/Documents/A193/DFU/tools/oneClickTool/mix', 'mix')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MagicTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2',
    codesign_identity=None,
    entitlements_file=None,
)
