#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Instalación Automática para Sistema de Detección de Fraude
=====================================================================

Este script instala automáticamente todas las dependencias necesarias:
- Python 3.11 (32-bit y 64-bit)
- Node.js LTS
- SQL Server Express 2022
- ODBC Driver 17 para SQL Server
- Firebird ODBC Driver
- Dependencias Python
- Dependencias Node.js
- Configuración de base de datos

Uso:
    python setup_automatico.py

Requisitos:
    - Windows 10/11
    - Conexión a Internet
    - Permisos de administrador (se solicitarán automáticamente)
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import shutil
import platform
import ctypes
import time
import json
from pathlib import Path
from typing import Optional, Tuple, List

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

CONFIG = {
    # URLs de descarga
    'python_32': 'https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe',
    'python_64': 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe',
    'nodejs': 'https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi',
    'odbc_driver': 'https://go.microsoft.com/fwlink/?linkid=2249004',  # ODBC Driver 17
    'firebird_odbc': 'https://github.com/FirebirdSQL/firebird-odbc-driver/releases/download/v2.0.5.156/Firebird_ODBC_2.0.5.156_Win32.exe',
    'sqlserver_express': 'https://go.microsoft.com/fwlink/?linkid=2215158',  # SQL Server 2022 Express

    # Versiones requeridas
    'python_version': '3.11',
    'node_version': '14.0',

    # Directorios
    'project_root': Path(__file__).parent.absolute(),
    'backend_dir': Path(__file__).parent / 'backend',
    'frontend_dir': Path(__file__).parent / 'frontend',
    'temp_dir': Path(tempfile.gettempdir()) / 'fraud_detection_setup',
}

# Colores para la consola
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

# ============================================================================
# UTILIDADES
# ============================================================================

def is_admin() -> bool:
    """Verifica si el script se está ejecutando con permisos de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-ejecuta el script con permisos de administrador."""
    if sys.platform != 'win32':
        print(f"{Colors.RED}Este script solo funciona en Windows.{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.YELLOW}Solicitando permisos de administrador...{Colors.RESET}")
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)

def print_header(text: str):
    """Imprime un encabezado con formato."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    """Imprime un mensaje de éxito."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """Imprime un mensaje de error."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str):
    """Imprime un mensaje de advertencia."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str):
    """Imprime un mensaje informativo."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def command_exists(command: str) -> bool:
    """Verifica si un comando existe en el sistema."""
    try:
        subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return True
    except FileNotFoundError:
        return False

def get_command_version(command: str) -> Optional[str]:
    """Obtiene la versión de un comando."""
    try:
        result = subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.stdout.strip() or result.stderr.strip()
    except:
        return None

def download_file(url: str, dest: Path, description: str = "archivo") -> bool:
    """Descarga un archivo mostrando progreso."""
    try:
        print_info(f"Descargando {description}...")

        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            bar_length = 50
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r  [{bar}] {percent:.1f}%', end='', flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=show_progress)
        print()  # Nueva línea después de la barra de progreso
        print_success(f"{description} descargado correctamente")
        return True
    except Exception as e:
        print()
        print_error(f"Error al descargar {description}: {e}")
        return False

def run_installer(installer_path: Path, args: List[str], description: str) -> bool:
    """Ejecuta un instalador de Windows."""
    try:
        print_info(f"Instalando {description}...")
        cmd = [str(installer_path)] + args
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )

        if result.returncode == 0 or result.returncode == 3010:  # 3010 = requiere reinicio
            print_success(f"{description} instalado correctamente")
            return True
        else:
            print_error(f"Error al instalar {description}")
            return False
    except Exception as e:
        print_error(f"Error al instalar {description}: {e}")
        return False

# ============================================================================
# VERIFICACIÓN DE COMPONENTES
# ============================================================================

def check_python() -> Tuple[bool, bool]:
    """Verifica la instalación de Python 32-bit y 64-bit."""
    print_info("Verificando Python...")

    has_64 = False
    has_32 = False

    # Verificar Python 64-bit
    if command_exists('python'):
        version = get_command_version('python')
        if version and '3.11' in version:
            # Verificar arquitectura
            result = subprocess.run(
                ['python', '-c', 'import struct; print(struct.calcsize("P") * 8)'],
                stdout=subprocess.PIPE,
                text=True,
                check=False
            )
            bits = result.stdout.strip()
            if bits == '64':
                has_64 = True
                print_success(f"Python 64-bit instalado: {version}")

    # Verificar Python 32-bit
    python_32_paths = [
        r'C:\Python311-32\python.exe',
        r'C:\Program Files (x86)\Python311\python.exe',
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python311-32\python.exe')
    ]

    for path in python_32_paths:
        if os.path.exists(path):
            result = subprocess.run(
                [path, '--version'],
                stdout=subprocess.PIPE,
                text=True,
                check=False
            )
            if '3.11' in result.stdout:
                has_32 = True
                print_success(f"Python 32-bit instalado en: {path}")
                break

    if not has_64:
        print_warning("Python 64-bit no encontrado")
    if not has_32:
        print_warning("Python 32-bit no encontrado (necesario para Firebird)")

    return has_64, has_32

def check_nodejs() -> bool:
    """Verifica la instalación de Node.js."""
    print_info("Verificando Node.js...")

    if command_exists('node'):
        version = get_command_version('node')
        if version:
            print_success(f"Node.js instalado: {version}")
            return True

    print_warning("Node.js no encontrado")
    return False

def check_sqlserver() -> bool:
    """Verifica la instalación de SQL Server."""
    print_info("Verificando SQL Server...")

    sql_paths = [
        r'C:\Program Files\Microsoft SQL Server',
        r'C:\Program Files (x86)\Microsoft SQL Server'
    ]

    for path in sql_paths:
        if os.path.exists(path):
            print_success(f"SQL Server encontrado en: {path}")
            return True

    print_warning("SQL Server no encontrado")
    return False

def check_odbc_driver() -> bool:
    """Verifica la instalación del ODBC Driver 17 para SQL Server."""
    print_info("Verificando ODBC Driver 17 para SQL Server...")

    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-OdbcDriver | Where-Object { $_.Name -like '*SQL Server*17*' } | Select-Object -First 1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if 'SQL Server' in result.stdout and '17' in result.stdout:
            print_success("ODBC Driver 17 para SQL Server instalado")
            return True
    except:
        pass

    print_warning("ODBC Driver 17 para SQL Server no encontrado")
    return False

def check_firebird_odbc() -> bool:
    """Verifica la instalación del Firebird ODBC Driver."""
    print_info("Verificando Firebird ODBC Driver...")

    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-OdbcDriver | Where-Object { $_.Name -like '*Firebird*' } | Select-Object -First 1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if 'Firebird' in result.stdout:
            print_success("Firebird ODBC Driver instalado")
            return True
    except:
        pass

    print_warning("Firebird ODBC Driver no encontrado")
    return False

# ============================================================================
# INSTALACIÓN DE COMPONENTES
# ============================================================================

def install_python_64() -> bool:
    """Instala Python 64-bit."""
    print_header("INSTALANDO PYTHON 64-BIT")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'python-3.11.9-amd64.exe'

    if not download_file(CONFIG['python_64'], installer_path, "Python 64-bit"):
        return False

    args = [
        '/quiet',
        'InstallAllUsers=1',
        'PrependPath=1',
        'Include_test=0',
        'Include_launcher=1',
        'InstallLauncherAllUsers=1'
    ]

    return run_installer(installer_path, args, "Python 64-bit")

def install_python_32() -> bool:
    """Instala Python 32-bit."""
    print_header("INSTALANDO PYTHON 32-BIT")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'python-3.11.9.exe'

    if not download_file(CONFIG['python_32'], installer_path, "Python 32-bit"):
        return False

    # Instalación personalizada en directorio específico
    install_dir = r'C:\Python311-32'
    args = [
        '/quiet',
        f'TargetDir={install_dir}',
        'InstallAllUsers=1',
        'PrependPath=0',  # No agregar al PATH para evitar conflictos
        'Include_test=0',
        'Include_launcher=0'
    ]

    success = run_installer(installer_path, args, "Python 32-bit")

    if success:
        print_info(f"Python 32-bit instalado en: {install_dir}")

    return success

def install_nodejs() -> bool:
    """Instala Node.js."""
    print_header("INSTALANDO NODE.JS")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'nodejs.msi'

    if not download_file(CONFIG['nodejs'], installer_path, "Node.js"):
        return False

    args = ['/quiet', '/norestart']

    return run_installer(installer_path, args, "Node.js")

def install_odbc_driver() -> bool:
    """Instala ODBC Driver 17 para SQL Server."""
    print_header("INSTALANDO ODBC DRIVER 17 PARA SQL SERVER")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'msodbcsql.msi'

    if not download_file(CONFIG['odbc_driver'], installer_path, "ODBC Driver 17"):
        return False

    args = [
        '/quiet',
        '/norestart',
        'IACCEPTMSODBCSQLLICENSETERMS=YES'
    ]

    return run_installer(installer_path, args, "ODBC Driver 17 para SQL Server")

def install_firebird_odbc() -> bool:
    """Instala Firebird ODBC Driver."""
    print_header("INSTALANDO FIREBIRD ODBC DRIVER")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'firebird_odbc.exe'

    if not download_file(CONFIG['firebird_odbc'], installer_path, "Firebird ODBC Driver"):
        return False

    args = ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART']

    return run_installer(installer_path, args, "Firebird ODBC Driver")

def install_sqlserver() -> bool:
    """Instala SQL Server Express."""
    print_header("INSTALANDO SQL SERVER EXPRESS 2022")

    print_warning("La instalación de SQL Server puede tomar varios minutos...")
    print_info("Por favor, sea paciente...")

    temp_dir = CONFIG['temp_dir']
    temp_dir.mkdir(parents=True, exist_ok=True)

    installer_path = temp_dir / 'sqlserver_express.exe'

    if not download_file(CONFIG['sqlserver_express'], installer_path, "SQL Server Express"):
        return False

    # SQL Server Express requiere instalación interactiva o configuración compleja
    # Por ahora, solo descargamos y mostramos instrucciones
    print_info(f"Instalador descargado en: {installer_path}")
    print_warning("Para completar la instalación de SQL Server Express:")
    print_info("1. Ejecute el instalador descargado")
    print_info("2. Seleccione 'Instalación básica'")
    print_info("3. Acepte los términos de licencia")
    print_info("4. Espere a que complete la instalación")

    return True

# ============================================================================
# CONFIGURACIÓN DE ENTORNOS
# ============================================================================

def create_virtual_environments() -> bool:
    """Crea los entornos virtuales de Python (64-bit y 32-bit)."""
    print_header("CREANDO ENTORNOS VIRTUALES")

    project_root = CONFIG['project_root']

    # Crear entorno virtual 64-bit
    print_info("Creando entorno virtual 64-bit (venv)...")
    venv_path = project_root / 'venv'

    if venv_path.exists():
        print_warning("Entorno virtual 64-bit ya existe, recreando...")
        try:
            shutil.rmtree(venv_path)
        except Exception as e:
            print_error(f"Error al eliminar entorno virtual existente: {e}")
            return False

    try:
        subprocess.run(['python', '-m', 'venv', str(venv_path)], check=True)
        print_success("Entorno virtual 64-bit creado correctamente")
    except Exception as e:
        print_error(f"Error al crear entorno virtual 64-bit: {e}")
        return False

    # Crear entorno virtual 32-bit
    print_info("Creando entorno virtual 32-bit (venv32)...")
    venv32_path = project_root / 'venv32'

    if venv32_path.exists():
        print_warning("Entorno virtual 32-bit ya existe, recreando...")
        try:
            shutil.rmtree(venv32_path)
        except Exception as e:
            print_error(f"Error al eliminar entorno virtual 32-bit existente: {e}")
            return False

    # Buscar Python 32-bit
    python_32_paths = [
        r'C:\Python311-32\python.exe',
        r'C:\Program Files (x86)\Python311\python.exe',
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python311-32\python.exe')
    ]

    python_32_exe = None
    for path in python_32_paths:
        if os.path.exists(path):
            python_32_exe = path
            break

    if not python_32_exe:
        print_error("No se encontró Python 32-bit instalado")
        return False

    try:
        subprocess.run([python_32_exe, '-m', 'venv', str(venv32_path)], check=True)
        print_success("Entorno virtual 32-bit creado correctamente")
    except Exception as e:
        print_error(f"Error al crear entorno virtual 32-bit: {e}")
        return False

    return True

def install_python_dependencies() -> bool:
    """Instala las dependencias de Python en ambos entornos virtuales."""
    print_header("INSTALANDO DEPENDENCIAS PYTHON")

    project_root = CONFIG['project_root']
    requirements_file = project_root / 'requirements.txt'

    if not requirements_file.exists():
        print_error(f"Archivo requirements.txt no encontrado en: {requirements_file}")
        return False

    # Instalar en entorno 64-bit
    print_info("Instalando dependencias en entorno 64-bit...")
    pip_64 = project_root / 'venv' / 'Scripts' / 'pip.exe'

    try:
        subprocess.run(
            [str(pip_64), 'install', '--upgrade', 'pip'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        subprocess.run(
            [str(pip_64), 'install', '-r', str(requirements_file)],
            check=True
        )
        print_success("Dependencias instaladas en entorno 64-bit")
    except Exception as e:
        print_error(f"Error al instalar dependencias en entorno 64-bit: {e}")
        return False

    # Instalar en entorno 32-bit (solo paquetes esenciales para Firebird)
    print_info("Instalando dependencias en entorno 32-bit...")
    pip_32 = project_root / 'venv32' / 'Scripts' / 'pip.exe'

    essential_packages = [
        'fastapi==0.115.0',
        'uvicorn[standard]==0.32.0',
        'colorama==0.4.6',
        'watchfiles==0.21.0',
        'sqlalchemy==2.0.36',
        'pyodbc==5.2.0',
        'firebird-driver==1.10.6',
        'python-dotenv==1.0.1',
        'pydantic==2.10.3',
        'python-multipart==0.0.17',
        'websockets==13.1'
    ]

    try:
        subprocess.run(
            [str(pip_32), 'install', '--upgrade', 'pip'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        for package in essential_packages:
            print_info(f"  Instalando {package}...")
            subprocess.run(
                [str(pip_32), 'install', package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        print_success("Dependencias instaladas en entorno 32-bit")
    except Exception as e:
        print_error(f"Error al instalar dependencias en entorno 32-bit: {e}")
        return False

    return True

def install_nodejs_dependencies() -> bool:
    """Instala las dependencias de Node.js."""
    print_header("INSTALANDO DEPENDENCIAS NODE.JS")

    frontend_dir = CONFIG['frontend_dir']

    if not frontend_dir.exists():
        print_warning(f"Directorio frontend no encontrado: {frontend_dir}")
        return False

    package_json = frontend_dir / 'package.json'

    if not package_json.exists():
        print_error(f"Archivo package.json no encontrado en: {frontend_dir}")
        return False

    print_info("Instalando paquetes npm...")

    try:
        # Cambiar al directorio frontend
        os.chdir(frontend_dir)

        # Instalar dependencias
        subprocess.run(['npm', 'install'], check=True)

        print_success("Dependencias Node.js instaladas correctamente")

        # Volver al directorio raíz
        os.chdir(CONFIG['project_root'])

        return True
    except Exception as e:
        print_error(f"Error al instalar dependencias Node.js: {e}")
        os.chdir(CONFIG['project_root'])
        return False

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

def create_env_file() -> bool:
    """Crea el archivo .env con la configuración por defecto."""
    print_header("CREANDO ARCHIVO DE CONFIGURACIÓN")

    project_root = CONFIG['project_root']
    env_file = project_root / '.env'

    if env_file.exists():
        print_warning("Archivo .env ya existe, creando backup...")
        backup_file = project_root / '.env.backup'
        shutil.copy(env_file, backup_file)
        print_info(f"Backup creado en: {backup_file}")

    # Obtener nombre de computadora para SQL Server
    computer_name = platform.node()

    env_content = f"""# Configuración de entorno - Sistema de Detección de Fraude
# Generado automáticamente por setup_automatico.py

# Database - SQL Server
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER={computer_name}\\SQLTRABAJO
DB_DATABASE=FraudDetectionDB
DB_USERNAME=sa
DB_PASSWORD=your_password_here
DB_TRUSTED_CONNECTION=yes

# Database - Firebird
# IMPORTANTE: Actualizar esta ruta con la ubicación real de su base de datos Firebird
FIREBIRD_DSN=DRIVER=Firebird/InterBase(r) driver;UID=sysdba;PWD=jmcjmc;DBNAME=localhost:C:\\ruta\\a\\tu\\base\\de\\datos.fdb;

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Security
SECRET_KEY=your-secret-key-change-in-production-xyz123
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_FILE=fraud_detection.log

# Detection Settings
DETECTION_BATCH_SIZE=1000
DETECTION_INTERVAL_SECONDS=300
MAX_CONCURRENT_DETECTIONS=5

# Alert Settings
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_HOST=smtp.gmail.com
ALERT_EMAIL_PORT=587
ALERT_EMAIL_USER=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
"""

    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Archivo .env creado correctamente")
        print_warning("IMPORTANTE: Edite el archivo .env para configurar:")
        print_info("  - Credenciales de SQL Server (si no usa autenticación de Windows)")
        print_info("  - Ruta a la base de datos Firebird (FIREBIRD_DSN)")
        print_info("  - Clave secreta para producción (SECRET_KEY)")
        return True
    except Exception as e:
        print_error(f"Error al crear archivo .env: {e}")
        return False

def setup_database() -> bool:
    """Configura la base de datos de SQL Server."""
    print_header("CONFIGURANDO BASE DE DATOS SQL SERVER")

    print_info("Intentando crear la base de datos FraudDetectionDB...")

    computer_name = platform.node()
    server = f"{computer_name}\\SQLTRABAJO"

    create_db_command = f'sqlcmd -S "{server}" -E -Q "CREATE DATABASE FraudDetectionDB"'

    try:
        result = subprocess.run(
            ['powershell', '-Command', create_db_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print_success("Base de datos FraudDetectionDB creada correctamente")
        else:
            if 'already exists' in result.stderr or 'ya existe' in result.stderr:
                print_warning("Base de datos FraudDetectionDB ya existe")
            else:
                print_error(f"Error al crear base de datos: {result.stderr}")
                print_warning("Puede crear la base de datos manualmente ejecutando:")
                print_info(f'  sqlcmd -S "{server}" -E -Q "CREATE DATABASE FraudDetectionDB"')
                return False

        # Verificar que la base de datos existe
        verify_command = f'sqlcmd -S "{server}" -E -Q "SELECT name FROM sys.databases WHERE name = \'FraudDetectionDB\'"'
        result = subprocess.run(
            ['powershell', '-Command', verify_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if 'FraudDetectionDB' in result.stdout:
            print_success("Base de datos verificada correctamente")
            return True
        else:
            print_error("No se pudo verificar la base de datos")
            return False

    except Exception as e:
        print_error(f"Error al configurar base de datos: {e}")
        return False

def run_migrations() -> bool:
    """Ejecuta las migraciones de Alembic."""
    print_header("EJECUTANDO MIGRACIONES DE BASE DE DATOS")

    project_root = CONFIG['project_root']
    backend_dir = CONFIG['backend_dir']

    if not backend_dir.exists():
        print_error(f"Directorio backend no encontrado: {backend_dir}")
        return False

    alembic_exe = project_root / 'venv' / 'Scripts' / 'alembic.exe'

    if not alembic_exe.exists():
        print_error("Alembic no está instalado en el entorno virtual")
        return False

    print_info("Ejecutando migraciones con Alembic...")

    try:
        # Cambiar al directorio del proyecto
        os.chdir(project_root)

        # Ejecutar migraciones
        result = subprocess.run(
            [str(alembic_exe), 'upgrade', 'head'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print_success("Migraciones ejecutadas correctamente")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Error al ejecutar migraciones: {e}")
        print_warning("Puede ejecutar las migraciones manualmente con:")
        print_info("  .\\venv\\Scripts\\activate")
        print_info("  alembic upgrade head")
        return False
    except Exception as e:
        print_error(f"Error inesperado al ejecutar migraciones: {e}")
        return False

# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

def create_start_scripts() -> bool:
    """Crea scripts de inicio para facilitar el uso del sistema."""
    print_header("CREANDO SCRIPTS DE INICIO")

    project_root = CONFIG['project_root']

    # Script para iniciar backend (64-bit)
    start_backend = project_root / 'iniciar_backend.bat'
    backend_content = """@echo off
echo ========================================
echo   INICIANDO BACKEND (64-bit)
echo ========================================
echo.
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
cd backend
echo Iniciando servidor FastAPI...
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
"""

    # Script para iniciar backend con Firebird (32-bit)
    start_backend_32 = project_root / 'iniciar_backend_32bit.bat'
    backend_32_content = """@echo off
echo ========================================
echo   INICIANDO BACKEND (32-bit para Firebird)
echo ========================================
echo.
cd /d "%~dp0"
call venv32\\Scripts\\activate.bat
cd backend
echo Iniciando servidor FastAPI con soporte Firebird 32-bit...
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
"""

    # Script para iniciar frontend
    start_frontend = project_root / 'iniciar_frontend.bat'
    frontend_content = """@echo off
echo ========================================
echo   INICIANDO FRONTEND
echo ========================================
echo.
cd /d "%~dp0frontend"
echo Iniciando servidor de desarrollo Vite...
npm run dev
pause
"""

    # Script para iniciar ambos
    start_all = project_root / 'iniciar_sistema.bat'
    all_content = """@echo off
echo ========================================
echo   INICIANDO SISTEMA COMPLETO
echo ========================================
echo.
cd /d "%~dp0"
echo Iniciando backend...
start "Backend - Sistema de Deteccion de Fraude" cmd /k iniciar_backend.bat
timeout /t 3 /nobreak >nul
echo Iniciando frontend...
start "Frontend - Sistema de Deteccion de Fraude" cmd /k iniciar_frontend.bat
echo.
echo Sistema iniciado!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo.
pause
"""

    try:
        with open(start_backend, 'w', encoding='utf-8') as f:
            f.write(backend_content)
        print_success("Script 'iniciar_backend.bat' creado")

        with open(start_backend_32, 'w', encoding='utf-8') as f:
            f.write(backend_32_content)
        print_success("Script 'iniciar_backend_32bit.bat' creado")

        with open(start_frontend, 'w', encoding='utf-8') as f:
            f.write(frontend_content)
        print_success("Script 'iniciar_frontend.bat' creado")

        with open(start_all, 'w', encoding='utf-8') as f:
            f.write(all_content)
        print_success("Script 'iniciar_sistema.bat' creado")

        return True
    except Exception as e:
        print_error(f"Error al crear scripts de inicio: {e}")
        return False

def print_final_summary():
    """Imprime un resumen final de la instalación."""
    print_header("INSTALACIÓN COMPLETADA")

    print(f"{Colors.GREEN}{Colors.BOLD}¡El sistema está listo para usar!{Colors.RESET}\n")

    print(f"{Colors.CYAN}Pasos siguientes:{Colors.RESET}")
    print(f"  {Colors.YELLOW}1.{Colors.RESET} Edite el archivo .env con sus configuraciones:")
    print(f"     - Ruta a la base de datos Firebird (FIREBIRD_DSN)")
    print(f"     - Credenciales de SQL Server si es necesario")
    print()

    print(f"  {Colors.YELLOW}2.{Colors.RESET} Para iniciar el sistema, ejecute:")
    print(f"     {Colors.GREEN}iniciar_sistema.bat{Colors.RESET}   (inicia backend y frontend)")
    print()
    print(f"     O inicie cada componente por separado:")
    print(f"     {Colors.GREEN}iniciar_backend.bat{Colors.RESET}   (backend 64-bit)")
    print(f"     {Colors.GREEN}iniciar_backend_32bit.bat{Colors.RESET}   (backend 32-bit con Firebird)")
    print(f"     {Colors.GREEN}iniciar_frontend.bat{Colors.RESET}  (frontend)")
    print()

    print(f"  {Colors.YELLOW}3.{Colors.RESET} Acceda a la aplicación:")
    print(f"     Frontend: {Colors.CYAN}http://localhost:5173{Colors.RESET}")
    print(f"     API: {Colors.CYAN}http://localhost:8000{Colors.RESET}")
    print(f"     Docs: {Colors.CYAN}http://localhost:8000/docs{Colors.RESET}")
    print()

    print(f"{Colors.CYAN}Entornos virtuales creados:{Colors.RESET}")
    print(f"  venv    - Python 64-bit (principal)")
    print(f"  venv32  - Python 32-bit (para compatibilidad con Firebird)")
    print()

    print(f"{Colors.YELLOW}Nota:{Colors.RESET} Si necesita conectarse a Firebird, use el backend de 32-bit")
    print()

def main():
    """Función principal del script."""
    # Verificar Windows
    if sys.platform != 'win32':
        print_error("Este script solo funciona en Windows")
        sys.exit(1)

    # Verificar permisos de administrador
    if not is_admin():
        run_as_admin()
        return

    print_header("INSTALADOR AUTOMÁTICO - SISTEMA DE DETECCIÓN DE FRAUDE")

    print(f"{Colors.CYAN}Este script instalará:{Colors.RESET}")
    print("  • Python 3.11 (32-bit y 64-bit)")
    print("  • Node.js LTS")
    print("  • SQL Server Express 2022")
    print("  • ODBC Driver 17 para SQL Server")
    print("  • Firebird ODBC Driver")
    print("  • Todas las dependencias del proyecto")
    print("  • Configuración de base de datos")
    print()

    input("Presione ENTER para continuar o Ctrl+C para cancelar...")

    # Crear directorio temporal
    CONFIG['temp_dir'].mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # FASE 1: VERIFICACIÓN
    # ========================================================================
    print_header("FASE 1: VERIFICACIÓN DE COMPONENTES")

    has_python_64, has_python_32 = check_python()
    has_nodejs = check_nodejs()
    has_sqlserver = check_sqlserver()
    has_odbc = check_odbc_driver()
    has_firebird_odbc = check_firebird_odbc()

    # ========================================================================
    # FASE 2: INSTALACIÓN
    # ========================================================================
    print_header("FASE 2: INSTALACIÓN DE COMPONENTES FALTANTES")

    components_installed = []

    if not has_python_64:
        if install_python_64():
            components_installed.append("Python 64-bit")
            time.sleep(2)  # Esperar a que se complete la instalación

    if not has_python_32:
        if install_python_32():
            components_installed.append("Python 32-bit")
            time.sleep(2)

    if not has_nodejs:
        if install_nodejs():
            components_installed.append("Node.js")
            time.sleep(2)

    if not has_odbc:
        if install_odbc_driver():
            components_installed.append("ODBC Driver 17")
            time.sleep(2)

    if not has_firebird_odbc:
        if install_firebird_odbc():
            components_installed.append("Firebird ODBC Driver")
            time.sleep(2)

    if not has_sqlserver:
        print_info("SQL Server Express no está instalado")
        response = input("¿Desea descargar el instalador de SQL Server Express? (s/n): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            install_sqlserver()
            print_warning("Por favor, complete la instalación de SQL Server manualmente")
            print_warning("Después, ejecute este script nuevamente")
            input("\nPresione ENTER cuando haya completado la instalación de SQL Server...")

    if components_installed:
        print_success(f"Componentes instalados: {', '.join(components_installed)}")
        print_warning("Es posible que necesite reiniciar el equipo para que los cambios surtan efecto")
        response = input("\n¿Desea continuar con la configuración ahora? (s/n): ")
        if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print_info("Ejecute este script nuevamente después de reiniciar")
            sys.exit(0)

    # ========================================================================
    # FASE 3: ENTORNOS VIRTUALES
    # ========================================================================
    if not create_virtual_environments():
        print_error("Error al crear entornos virtuales")
        sys.exit(1)

    # ========================================================================
    # FASE 4: DEPENDENCIAS
    # ========================================================================
    if not install_python_dependencies():
        print_error("Error al instalar dependencias Python")
        sys.exit(1)

    if not install_nodejs_dependencies():
        print_warning("Error al instalar dependencias Node.js (continuar de todas formas)")

    # ========================================================================
    # FASE 5: CONFIGURACIÓN
    # ========================================================================
    if not create_env_file():
        print_error("Error al crear archivo de configuración")
        sys.exit(1)

    # ========================================================================
    # FASE 6: BASE DE DATOS
    # ========================================================================
    if setup_database():
        print_info("Intentando ejecutar migraciones...")
        run_migrations()  # No es crítico si falla

    # ========================================================================
    # FASE 7: SCRIPTS DE INICIO
    # ========================================================================
    if not create_start_scripts():
        print_warning("Error al crear scripts de inicio (no crítico)")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print_final_summary()

    # Limpiar archivos temporales
    try:
        shutil.rmtree(CONFIG['temp_dir'])
        print_info("Archivos temporales eliminados")
    except:
        pass

    input("\nPresione ENTER para salir...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Instalación cancelada por el usuario{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Error inesperado: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
