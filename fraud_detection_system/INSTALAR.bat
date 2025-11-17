@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   INSTALADOR AUTOMÁTICO
echo   Sistema de Detección de Fraude
echo ========================================
echo.
echo Este script instalará todo lo necesario para ejecutar el proyecto:
echo   - Python 3.11 (32-bit y 64-bit)
echo   - Node.js LTS
echo   - SQL Server Express
echo   - Drivers ODBC
echo   - Todas las dependencias
echo.
echo IMPORTANTE: Se solicitarán permisos de administrador
echo.
pause

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python no está instalado en este sistema
    echo.
    echo Por favor, instale Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Durante la instalación, asegúrese de marcar:
    echo   [X] Add Python to PATH
    echo.
    pause
    exit /b 1
)

REM Ejecutar el script de instalación
echo.
echo Iniciando instalación...
echo.
python setup_automatico.py

if errorlevel 1 (
    echo.
    echo ERROR: La instalación falló
    echo Revise los mensajes de error arriba
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   INSTALACIÓN COMPLETADA
echo ========================================
echo.
pause
