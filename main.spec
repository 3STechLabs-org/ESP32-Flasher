# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Detect the current platform
is_windows = sys.platform.startswith('win')
is_macos = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

pil_path = os.path.join('esp_env', 'Lib', 'site-packages', 'PIL')
pil_data = [
    (os.path.join(pil_path, 'palettes'), os.path.join('PIL', 'palettes')),
    (os.path.join(pil_path, 'fonts'), os.path.join('PIL', 'fonts')),
]

# Collect PIL submodules and data files
pil_hidden_imports = collect_submodules('PIL')
pil_datas = collect_data_files('PIL')

#datas = [
#    (os.path.join('esp_env', 'Lib', 'site-packages', 'esptool', 'targets', 'stub_flasher'), os.path.join('esptool', 'targets', 'stub_flasher')),
#]
datas = [
    (os.path.join('venv', 'lib', 'python3.12', 'site-packages', 'esptool', 'targets', 'stub_flasher'), os.path.join('esptool', 'targets', 'stub_flasher')),
]
datas += pil_datas

#pathex = [os.path.join('esp_env', 'Lib', 'site-packages')]
pathex = [os.path.join('venv', 'lib','python3.12', 'site-packages')]
# Platform-specific paths and data files
if is_windows:
    datas += [
        (os.path.join('drivers', 'CP210x_VCP_Windows', 'CP210xVCPInstaller_x64.exe'), '.'),
    ]
elif is_macos:
    print("MAC")
elif is_linux:
    pass
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
        'PIL',
        'PIL_imaging',
        'PIL.ExifTags',
        'PIL._tkinter_finder',
        'PIL._imagingtk',
        'PIL._imaging',
        'PIL._imagingft',
        'PIL._imagingmath',
        'PIL._imagingmorph',
        'PIL._webp',
    ] + pil_hidden_imports,
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