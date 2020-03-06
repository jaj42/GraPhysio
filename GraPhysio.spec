# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)

import inspect
from os import path
import pint
pintdir = path.dirname(inspect.getfile(pint))

block_cipher = None

a = Analysis(['graphysio/__main__.py'],
             pathex=['/home/jaj/devel/GraPhysio'],
             binaries=[],
             datas=[(f'{pintdir}/constants_en.txt', './pint/constants_en.txt')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='__main__',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='GraPhysio')
