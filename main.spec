# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Your main script
    pathex=[r'D:\3STechLabs\werqwise\esp_flasher\esp_env\Lib\site-packages'],  # Path to your project directory
    binaries=[],
    datas=[
        (r'D:\3STechLabs\werqwise\esp_flasher\esp_env\Lib\site-packages\esptool\targets\stub_flasher', 'esptool/targets/stub_flasher'),
        (r'D:\3STechLabs\werqwise\esp_flasher\CP210x_VCP_Windows\CP210xVCPInstaller_x64.exe', '.'),  # Include the driver installer
    ],
    hiddenimports=[
        'serial.tools.list_ports',  # Ensure hidden imports are included
        'esptool'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',  # Name of the output executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',  # Name of the output directory
)
