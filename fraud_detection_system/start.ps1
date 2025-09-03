# Script para iniciar el Sistema de Detección de Fraude
# start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA DE DETECCION FRAUDE " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar entorno virtual Python
if (!(Test-Path ".\venv")) {
    Write-Host "Creando entorno virtual Python..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Instalar dependencias Python si es necesario
Write-Host "Verificando dependencias Python..." -ForegroundColor Yellow
pip install -q fastapi uvicorn sqlalchemy pyodbc firebird-driver python-dotenv

# Iniciar Backend en nueva ventana
Write-Host "Iniciando Backend..." -ForegroundColor Green
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

Start-Sleep -Seconds 3

# Verificar si el backend está corriendo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  OK Backend iniciado correctamente" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING Backend puede estar iniciandose..." -ForegroundColor Yellow
}

# Iniciar Frontend
Write-Host "Iniciando Frontend..." -ForegroundColor Green

# Verificar e instalar dependencias Node si es necesario
Push-Location frontend
if (!(Test-Path "node_modules")) {
    Write-Host "Instalando dependencias Node.js..." -ForegroundColor Yellow
    npm install
}

# Iniciar frontend en nueva ventana
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru
Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SISTEMA INICIADO CORRECTAMENTE        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Accesos:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "Para detener el sistema, cierre las ventanas de PowerShell" -ForegroundColor Yellow
Write-Host ""

# Mantener ventana abierta
Write-Host "Presione cualquier tecla para cerrar esta ventana..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")