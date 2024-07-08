# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['D:\\3STechLabs\\werqwise\\esp_flasher\\esp_env\\Lib\\site-packages'],
    binaries=[],
    datas=[
        ('D:\\3STechLabs\\werqwise\\esp_flasher\\esp_env\\Lib\\site-packages\\esptool\\targets\\stub_flasher', 'esptool/targets/stub_flasher'),
        ('D:\\3STechLabs\\werqwise\\esp_flasher\\CP210x_VCP_Windows\\CP210xVCPInstaller_x64.exe', '.'),
        (r'C:\Python312\python312.dll', '.')
    ],
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