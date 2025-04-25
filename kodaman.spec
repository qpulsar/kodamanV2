# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(
    ['kodaman.py'],
    pathex=[r'd:\\Projects\\PythonProjects\\kodamanV2'],
    binaries=[],
    datas=[('client', 'client'), ('server', 'server'), ('shared', 'shared'), ('images', 'images'), ('preferences.json', '.'), ('server_settings.json', '.')] + collect_data_files('PyQt5'),
    hiddenimports=collect_submodules('PyQt5') + [
        'client.css_highlighter',
        'client.html_highlighter',
        'client.js_highlighter',
        'client.python_highlighter',
    ],
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
    name='kodaman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
