@echo off
chcp 65001 > nul
title HAOC VoIP Monitor - Gerador de Executável Windows (.EXE)
color 0A

echo =====================================================================
echo       HOSPITAL ALEMÃO OSVALDO CRUZ - NOC TELEFONIA IP
echo          Gerador Automático do Executável Desktop (.EXE)
echo =====================================================================
echo.

:: 1. Verificar instalação do Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não foi encontrado no PATH do sistema.
    echo Por favor, instale o Python 3.10 ou superior e marque "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [*] Python detectado com sucesso!
echo.

:: 2. Instalar dependências e PyInstaller
echo [*] Verificando e instalando dependências (PyQt6, PyInstaller, etc.)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [*] Compilando executável nativo Windows com PyInstaller...
python build_exe.py

if %errorlevel% equ 0 (
    echo.
    echo =====================================================================
    echo [SUCESSO] Executável gerado com êxito!
    echo Arquivo disponível em: dist\HAOC_VoIP_Monitor.exe
    echo =====================================================================
) else (
    echo.
    echo [ERRO] Falha durante a geração do executável.
)

echo.
pause
