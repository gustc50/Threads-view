@echo off
REM =========================================================
REM  Executa o monitor do Threads no Windows.
REM  Uso: run.bat            (usa o tipo padrao do .env)
REM       run.bat RECENT     (busca publicacoes recentes)
REM       run.bat TOP        (busca publicacoes em destaque)
REM =========================================================

setlocal
cd /d "%~dp0"

REM Cria virtualenv na primeira execucao
if not exist ".venv\" (
    echo [setup] Criando ambiente virtual em .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [erro] Nao foi possivel criar o venv. Verifique se o Python esta instalado.
        exit /b 1
    )
    call ".venv\Scripts\activate.bat"
    echo [setup] Instalando dependencias ...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call ".venv\Scripts\activate.bat"
)

if "%1"=="" (
    python main.py
) else (
    python main.py --tipo %1
)

set EXITCODE=%errorlevel%
echo.
echo Finalizado com codigo %EXITCODE%.
pause
endlocal
exit /b %EXITCODE%
