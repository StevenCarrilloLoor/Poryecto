@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   COMPLETAR CONFIGURACIONES
echo   Sistema de Detección de Fraude
echo ========================================
echo.
echo Este script creará todos los archivos de configuración faltantes:
echo   - alembic.ini
echo   - .gitignore
echo   - README.md
echo   - frontend/.env
echo   - frontend/.eslintrc.json
echo   - frontend/.prettierrc
echo   - frontend/tsconfig.node.json
echo.
pause

python completar_configuracion.py

if errorlevel 1 (
    echo.
    echo ERROR: El script falló
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   CONFIGURACIONES COMPLETADAS
echo ========================================
echo.
pause
