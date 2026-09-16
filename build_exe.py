#!/usr/bin/env python3
"""
Script automatizado de compilação do executável Desktop (HAOC_VoIP_Monitor.exe).
Compatível com Windows 10/11 e sistemas desktop.
"""
import os
import sys
import subprocess
import shutil

def main():
    print("=" * 70)
    print("  HAOC VoIP Monitor Enterprise - Gerador de Executável (.exe)")
    print("=" * 70)

    # 1. Verificar/Instalar PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller detectado: versão {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller não encontrado. Instalando automaticamente via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.4.0"])
        print("[OK] PyInstaller instalado com sucesso.")

    # 2. Assegurar diretório do banco e inicialização
    if not os.path.exists("data"):
        os.makedirs("data", exist_ok=True)
    
    # 3. Executar o PyInstaller utilizando o arquivo de especificação .spec
    spec_file = "haoc_voip_desktop.spec"
    if not os.path.exists(spec_file):
        print(f"[ERRO] Arquivo de especificação '{spec_file}' não encontrado!")
        sys.exit(1)

    print(f"\n[*] Iniciando empacotamento com PyInstaller ({spec_file})...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_file,
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("  SUCESSO: Executável gerado com sucesso!")
        print("=" * 70)
        dist_dir = os.path.abspath("dist")
        exe_name = "HAOC_VoIP_Monitor.exe" if sys.platform == "win32" else "HAOC_VoIP_Monitor"
        exe_path = os.path.join(dist_dir, exe_name)
        print(f"\nO executável foi criado em:")
        print(f"  -> {exe_path}")
        print("\nPara distribuir no hospital, copie o arquivo executável da pasta 'dist'.")
    else:
        print("\n[ERRO] Falha ao compilar o executável com PyInstaller.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
