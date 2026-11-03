# PyInstaller spec for Salli Baba. Build on Windows with:
#   pyinstaller build/build.spec
# Output .exe lands in dist/SalliBaba/SalliBaba.exe
block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[('../assets', 'assets')],
    hiddenimports=['customtkinter'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SalliBaba',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='../assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SalliBaba',
)
