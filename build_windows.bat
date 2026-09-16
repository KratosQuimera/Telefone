@echo off
chcp 65001 >nul
cls
echo =======================================================================
echo   HAOC VoIP Monitor Enterprise - Compilador de Executavel Windows (.exe)
echo =======================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] O Python nao foi encontrado no PATH do Windows!
    echo Instale o Python 3.10+ e marque a opcao "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias obrigatorias e PyInstaller...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller>=6.4.0

echo.
echo [2/3] Inicializando banco de dados local...
python init_db.py

echo.
echo [3/3] Compilando executavel HAOC_VoIP_Monitor.exe...
python build_exe.py

echo.
if exist "dist\HAOC_VoIP_Monitor.exe" (
    echo =======================================================================
    echo   CONCLUIDO COM SUCESSO!
    echo   Executavel gerado em: dist\HAOC_VoIP_Monitor.exe
    echo =======================================================================
) else (
    echo [AVISO] Verifique as mensagens acima para diagnosticar eventuais alertas.
)

echo.
pause
