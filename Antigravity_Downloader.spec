# -*- mode: python ; coding: utf-8 -*-
import os
import importlib


a = Analysis(
    ['downmess.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(os.path.dirname(importlib.import_module('tkinterdnd2').__file__), 'tkdnd'), 'tkinterdnd2/tkdnd'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder', 'PIL', 'ctypes', 'customtkinter', 
        'yt_dlp', 'rembg', 'onnxruntime', 'cv2', 'flet', 'tkinterdnd2',
        'librosa', 'numpy', 'matplotlib', 'sklearn.utils._typedefs', 'sklearn.neighbors._partition_nodes'
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
    name='Antigravity_Downloader',
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
