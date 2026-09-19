"""
Script de automação para compilação do executável Windows (.exe)
Hospital Alemão Osvaldo Cruz - HAOC VoIP Monitor
"""
import os
import sys
import subprocess
from pathlib import Path

def compilar():
    print("=" * 70)
    print("  HAOC VoIP Monitor - Compilação do Executável Windows (.EXE)")
    print("=" * 70)

    raiz = Path(__file__).resolve().parent
    os.chdir(raiz)

    # 1. Garantir pasta data e arquivos mínimos
    data_dir = raiz / "data"
    data_dir.mkdir(exist_ok=True)

    # 2. Comando PyInstaller com todas as dependências ocultas do PyQt6 e SQLite
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "HAOC_VoIP_Monitor",
        "--add-data", f"{data_dir}{os.pathsep}data",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "sqlite3",
        "--hidden-import", "requests",
        "desktop_main.py",
    ]

    print(f"\n[*] Executando comando PyInstaller:\n{' '.join(cmd)}\n")
    resultado = subprocess.run(cmd)

    if resultado.returncode == 0:
        exe_path = raiz / "dist" / "HAOC_VoIP_Monitor.exe"
        print("\n" + "=" * 70)
        print("[SUCESSO] Executável criado com êxito!")
        print(f"Localização do executável: {exe_path}")
        print("=" * 70)
    else:
        print("\n[ERRO] Falha ao compilar o executável com PyInstaller.")
        sys.exit(resultado.returncode)

if __name__ == "__main__":
    compilar()
