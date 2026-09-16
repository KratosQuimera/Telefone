# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec para HAOC VoIP Monitor Desktop.
Gera o executável standalone corporativo para Windows 10/11.
"""
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Diretório raiz
project_root = os.path.abspath(os.getcwd())

# Coleta de submódulos ocultos para evitar erros de importação dinâmica
hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'sqlalchemy',
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.dialects.sqlite',
    'openpyxl',
    'dotenv',
    'haoc_voip',
    'haoc_voip.config',
    'haoc_voip.core',
    'haoc_voip.core.models',
    'haoc_voip.core.database',
    'haoc_voip.core.auth',
    'haoc_voip.core.monitor',
    'haoc_voip.core.importer',
    'haoc_voip.core.backup',
    'haoc_voip.desktop',
    'haoc_voip.desktop.styles',
    'haoc_voip.desktop.signals',
    'haoc_voip.desktop.login_dialog',
    'haoc_voip.desktop.ramal_dialog',
    'haoc_voip.desktop.incidentes_dialog',
    'haoc_voip.desktop.import_dialog',
    'haoc_voip.desktop.main_window',
]

# Dados adicionais e arquivos de configuração
added_datas = [
    ('haoc_voip', 'haoc_voip'),
]

# Inclui diretório de dados caso exista
if os.path.exists('data'):
    added_datas.append(('data', 'data'))

a = Analysis(
    ['desktop_main.py'],
    pathex=[project_root],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'pandas'],
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
    name='HAOC_VoIP_Monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem tela preta do prompt de comando
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
