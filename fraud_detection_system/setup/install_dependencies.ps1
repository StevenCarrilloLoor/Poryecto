# Script de Instalacion de Dependencias
# setup/install_dependencies.ps1
# Ejecutar como: .\setup\install_dependencies.ps1

# Configurar codificacion UTF-8 para PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALACION DE DEPENDENCIAS          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para verificar si un comando existe
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
if (Test-Command "python") {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK Python instalado: $pythonVersion" -ForegroundColor Green
    
    # Verificar version minima (3.8+)
    $versionString = $pythonVersion -replace 'Python ', ''
    $versionParts = $versionString.Split('.')
    $majorVersion = [int]$versionParts[0]
    $minorVersion = [int]$versionParts[1]
    
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
        Write-Host "  ERROR Se requiere Python 3.8 o superior" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ERROR Python no esta instalado" -ForegroundColor Red
    Write-Host "  Por favor, instale Python 3.8+ desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Verificar Node.js
Write-Host "Verificando Node.js..." -ForegroundColor Yellow
if (Test-Command "node") {
    $nodeVersion = node --version
    Write-Host "  OK Node.js instalado: $nodeVersion" -ForegroundColor Green
    
    # Verificar version minima (14+)
    $versionString = $nodeVersion -replace 'v', ''
    $versionParts = $versionString.Split('.')
    $majorVersion = [int]$versionParts[0]
    
    if ($majorVersion -lt 14) {
        Write-Host "  ERROR Se requiere Node.js 14.0 o superior" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ERROR Node.js no esta instalado" -ForegroundColor Red
    Write-Host "  Por favor, instale Node.js desde: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Verificar npm
Write-Host "Verificando npm..." -ForegroundColor Yellow
if (Test-Command "npm") {
    $npmVersion = npm --version
    Write-Host "  OK npm instalado: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "  ERROR npm no esta instalado" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALANDO DEPENDENCIAS PYTHON        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Actualizar pip
Write-Host "Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK pip actualizado" -ForegroundColor Green
} else {
    Write-Host "  ERROR al actualizar pip" -ForegroundColor Red
    exit 1
}

# Crear entorno virtual si no existe
$venvPath = ".\venv"
if (!(Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Entorno virtual creado" -ForegroundColor Green
    } else {
        Write-Host "  ERROR al crear entorno virtual" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  INFO Entorno virtual ya existe" -ForegroundColor DarkGray
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "  OK Entorno virtual activado" -ForegroundColor Green
} else {
    Write-Host "  ERROR No se encuentra el script de activacion" -ForegroundColor Red
    exit 1
}

# Instalar dependencias Python
Write-Host "Instalando paquetes Python..." -ForegroundColor Yellow

# Versiones compatibles con Python 3.13
$pythonPackages = @(
    "fastapi==0.115.0",
    "uvicorn[standard]==0.32.0",
    "sqlalchemy==2.0.36",
    "alembic==1.13.3",
    "pyodbc==5.2.0",
    "firebird-driver==1.10.6",
    "python-dotenv==1.0.1",
    "pydantic==2.10.3",
    "python-multipart==0.0.17",
    "websockets==13.1",
    "pytest==8.3.4",
    "pytest-cov==6.0.0",
    "black==24.10.0",
    "flake8==7.1.1"
)

$packageInstalled = 0
$totalPackages = $pythonPackages.Count

foreach ($package in $pythonPackages) {
    $packageInstalled++
    Write-Host "  [$packageInstalled/$totalPackages] Instalando $package..." -ForegroundColor Gray
    pip install $package --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ERROR instalando $package" -ForegroundColor Red
        # Continuar con otros paquetes
    }
}

Write-Host "  OK Paquetes Python instalados" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALANDO DEPENDENCIAS NODE.JS       " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Crear directorio frontend si no existe
$frontendPath = ".\frontend"
if (!(Test-Path $frontendPath)) {
    Write-Host "Creando directorio frontend..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $frontendPath -Force | Out-Null
    Write-Host "  OK Directorio frontend creado" -ForegroundColor Green
}

# Cambiar al directorio frontend
Push-Location $frontendPath

try {
    # Inicializar package.json si no existe
    if (!(Test-Path "package.json")) {
        Write-Host "Inicializando package.json..." -ForegroundColor Yellow
        npm init -y | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK package.json creado" -ForegroundColor Green
        } else {
            Write-Host "  ERROR al crear package.json" -ForegroundColor Red
            throw "Error en npm init"
        }
    }

    # Instalar dependencias Node.js
    Write-Host "Instalando paquetes Node.js..." -ForegroundColor Yellow

    # Instalar dependencias de produccion
    Write-Host "  Instalando dependencias de produccion..." -ForegroundColor Gray
    $prodPackages = "react@18.2.0 react-dom@18.2.0 typescript@5.3.2 axios@1.6.2 socket.io-client@4.5.4 @mui/material@5.14.18 @emotion/react@11.11.1 @emotion/styled@11.11.0 @mui/icons-material@5.14.18 @tanstack/react-query@5.8.4 react-router-dom@6.20.0 recharts@2.10.1"
    
    npm install $prodPackages.Split(' ') --save --silent
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    OK Dependencias de produccion instaladas" -ForegroundColor Green
    } else {
        Write-Host "    ERROR al instalar dependencias de produccion" -ForegroundColor Yellow
    }

    # Instalar dependencias de desarrollo
    Write-Host "  Instalando dependencias de desarrollo..." -ForegroundColor Gray
    $devPackages = "@types/react@18.2.39 @types/react-dom@18.2.17 @types/node@20.10.0 @vitejs/plugin-react@4.2.0 vite@5.0.4 eslint@8.54.0 prettier@3.1.0"
    
    npm install $devPackages.Split(' ') --save-dev --silent
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    OK Dependencias de desarrollo instaladas" -ForegroundColor Green
    } else {
        Write-Host "    ERROR al instalar dependencias de desarrollo" -ForegroundColor Yellow
    }

    Write-Host "  OK Paquetes Node.js instalados" -ForegroundColor Green
    
} catch {
    Write-Host "  ERROR en instalacion Node.js: $_" -ForegroundColor Red
} finally {
    # Volver al directorio raiz
    Pop-Location
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO BASE DE DATOS            " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar SQL Server
Write-Host "Verificando SQL Server..." -ForegroundColor Yellow
$sqlServer = "STEVEN-ALIENWAR\SQLTRABAJO"

try {
    # Intentar conexion usando .NET SqlClient
    Add-Type -AssemblyName System.Data
    $connectionString = "Server=$sqlServer;Database=master;Integrated Security=true;Connection Timeout=5;"
    $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
    $connection.Open()
    $connection.Close()
    Write-Host "  OK SQL Server accesible: $sqlServer" -ForegroundColor Green
} catch {
    Write-Host "  WARNING No se puede conectar a SQL Server: $sqlServer" -ForegroundColor Yellow
    Write-Host "  Por favor, verifique que SQL Server este instalado y ejecutandose" -ForegroundColor Yellow
}

# Verificar driver ODBC de Firebird
Write-Host "Verificando driver ODBC de Firebird..." -ForegroundColor Yellow
try {
    $odbcDrivers = Get-OdbcDriver -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*Firebird*" }
    if ($odbcDrivers) {
        Write-Host "  OK Driver ODBC de Firebird instalado" -ForegroundColor Green
    } else {
        Write-Host "  WARNING Driver ODBC de Firebird no encontrado" -ForegroundColor Yellow
        Write-Host "  Por favor, instale el driver desde: https://firebirdsql.org/en/odbc-driver/" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  INFO No se pudo verificar drivers ODBC" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALACION COMPLETADA                " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Resumen de instalacion:" -ForegroundColor Cyan
Write-Host "  OK Python y dependencias instaladas" -ForegroundColor White
Write-Host "  OK Node.js y dependencias instaladas" -ForegroundColor White
Write-Host "  OK Entorno virtual creado" -ForegroundColor White
Write-Host ""

Write-Host "Configuracion pendiente:" -ForegroundColor Yellow
Write-Host "  1. Configure el archivo .env con sus credenciales" -ForegroundColor White
Write-Host "  2. Ejecute las migraciones de base de datos:" -ForegroundColor White
Write-Host "     alembic upgrade head" -ForegroundColor Gray
Write-Host ""

Write-Host "Para iniciar el sistema:" -ForegroundColor Cyan
Write-Host "  Backend:" -ForegroundColor White
Write-Host "     cd backend" -ForegroundColor Gray
Write-Host "     uvicorn api.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  Frontend:" -ForegroundColor White
Write-Host "     cd frontend" -ForegroundColor Gray
Write-Host "     npm run dev" -ForegroundColor Gray
Write-Host ""

Write-Host "Sistema listo para desarrollo!" -ForegroundColor Green

# Pausa para leer el resultado
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")