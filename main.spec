# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Detect the current platform
is_windows = sys.platform.startswith('win')
is_macos = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

# Platform-specific paths and data files
if is_windows:
    datas = [
        ('esp_env\\Lib\\site-packages\\esptool\\targets\\stub_flasher', 'esptool/targets/stub_flasher'),
        ('drivers\\CP210x_VCP_Windows\\CP210xVCPInstaller_x64.exe', '.'),
    ]
    pathex = ['esp_env\\Lib\\site-packages']
elif is_macos:
    datas = [
        ('esp_env/Lib/site-packages/esptool/targets/stub_flasher', 'esptool/targets/stub_flasher'),
    ]
    pathex = ['esp_env/Lib/site-packages']
elif is_linux:
    datas = [
        ('esp_env/Lib/site-packages/esptool/targets/stub_flasher', 'esptool/targets/stub_flasher'),
    ]
    pathex = ['esp_env/Lib/site-packages']
else:
    datas = []
    pathex = []

a = Analysis(
    ['main.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=[
        'serial',
        'serial.tools.list_ports',
        'esptool',
        'esptool.loader',
        'esptool.targets',
        'ttkbootstrap',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
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
    name='main',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)