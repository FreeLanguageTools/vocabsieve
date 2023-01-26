# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['vocabsieve.py'],
    pathex=[],
    binaries=[],
    datas=[
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/simplemma/data', 'simplemma/data'),
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/pymorphy2_dicts_ru/data', 'pymorphy2_dicts_ru/data'),
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/pymorphy2_dicts_uk/data', 'pymorphy2_dicts_uk/data'),
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/vocabsieve/ext/reader/templates', 'vocabsieve/ext/reader/templates'),
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/vocabsieve/ext/reader/static', 'vocabsieve/ext/reader/static'),
      ('/home/appveyor/venv3.8/lib/python3.8/site-packages/sentence_splitter/non_breaking_prefixes', 'sentence_splitter/non_breaking_prefixes')
      ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vocabsieve',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
