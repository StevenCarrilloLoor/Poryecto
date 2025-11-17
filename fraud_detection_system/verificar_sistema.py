#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Verificación del Sistema
===================================

Este script verifica que todos los componentes estén correctamente instalados
y configurados.

Uso:
    python verificar_sistema.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Colores para la consola
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Imprime un encabezado con formato."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_check(text: str, status: bool, details: str = ""):
    """Imprime el resultado de una verificación."""
    if status:
        symbol = f"{Colors.GREEN}✓{Colors.RESET}"
        status_text = f"{Colors.GREEN}OK{Colors.RESET}"
    else:
        symbol = f"{Colors.RED}✗{Colors.RESET}"
        status_text = f"{Colors.RED}FALTA{Colors.RESET}"

    print(f"{symbol} {text:<50} [{status_text}]")
    if details:
        print(f"  {Colors.BLUE}→{Colors.RESET} {details}")

def check_command(command: str, args: list = ['--version']) -> tuple:
    """Verifica si un comando existe y retorna su versión."""
    try:
        result = subprocess.run(
            [command] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        output = result.stdout.strip() or result.stderr.strip()
        return True, output.split('\n')[0] if output else "Instalado"
    except FileNotFoundError:
        return False, "No encontrado"
    except Exception as e:
        return False, str(e)

def check_file_exists(path: Path) -> bool:
    """Verifica si un archivo existe."""
    return path.exists()

def check_directory_exists(path: Path) -> bool:
    """Verifica si un directorio existe."""
    return path.exists() and path.is_dir()

def check_python_packages(python_exe: str, packages: list) -> dict:
    """Verifica qué paquetes Python están instalados."""
    results = {}
    for package in packages:
        try:
            result = subprocess.run(
                [python_exe, '-m', 'pip', 'show', package],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            results[package] = result.returncode == 0
        except:
            results[package] = False
    return results

def check_node_packages(frontend_dir: Path, packages: list) -> dict:
    """Verifica qué paquetes Node.js están instalados."""
    results = {}
    node_modules = frontend_dir / 'node_modules'

    if not node_modules.exists():
        return {pkg: False for pkg in packages}

    for package in packages:
        package_dir = node_modules / package
        results[package] = package_dir.exists()

    return results

def main():
    """Función principal."""
    print_header("VERIFICACIÓN DEL SISTEMA")

    project_root = Path(__file__).parent.absolute()

    # ========================================================================
    # SOFTWARE BASE
    # ========================================================================
    print(f"\n{Colors.BOLD}1. SOFTWARE BASE{Colors.RESET}")
    print("─" * 70)

    # Python 64-bit
    python_ok, python_version = check_command('python')
    print_check("Python 64-bit", python_ok, python_version)

    # Python 32-bit
    python_32_paths = [
        r'C:\Python311-32\python.exe',
        r'C:\Program Files (x86)\Python311\python.exe',
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python311-32\python.exe')
    ]

    python_32_ok = False
    python_32_details = "No encontrado"
    for path in python_32_paths:
        if os.path.exists(path):
            python_32_ok = True
            python_32_details = path
            break

    print_check("Python 32-bit", python_32_ok, python_32_details)

    # Node.js
    node_ok, node_version = check_command('node')
    print_check("Node.js", node_ok, node_version)

    # npm
    npm_ok, npm_version = check_command('npm')
    print_check("npm", npm_ok, npm_version)

    # SQL Server
    sql_paths = [
        r'C:\Program Files\Microsoft SQL Server',
        r'C:\Program Files (x86)\Microsoft SQL Server'
    ]
    sql_ok = any(os.path.exists(p) for p in sql_paths)
    sql_details = "Encontrado" if sql_ok else "No encontrado"
    print_check("SQL Server", sql_ok, sql_details)

    # ODBC Driver 17
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-OdbcDriver | Where-Object { $_.Name -like '*SQL Server*17*' } | Select-Object -First 1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        odbc_ok = 'SQL Server' in result.stdout and '17' in result.stdout
    except:
        odbc_ok = False

    odbc_details = "Instalado" if odbc_ok else "No encontrado"
    print_check("ODBC Driver 17 para SQL Server", odbc_ok, odbc_details)

    # Firebird ODBC
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-OdbcDriver | Where-Object { $_.Name -like '*Firebird*' } | Select-Object -First 1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        firebird_ok = 'Firebird' in result.stdout
    except:
        firebird_ok = False

    firebird_details = "Instalado" if firebird_ok else "No encontrado"
    print_check("Firebird ODBC Driver", firebird_ok, firebird_details)

    # ========================================================================
    # ENTORNOS VIRTUALES
    # ========================================================================
    print(f"\n{Colors.BOLD}2. ENTORNOS VIRTUALES{Colors.RESET}")
    print("─" * 70)

    venv_path = project_root / 'venv'
    venv_ok = check_directory_exists(venv_path)
    venv_details = str(venv_path) if venv_ok else "No encontrado"
    print_check("Entorno virtual 64-bit (venv)", venv_ok, venv_details)

    venv32_path = project_root / 'venv32'
    venv32_ok = check_directory_exists(venv32_path)
    venv32_details = str(venv32_path) if venv32_ok else "No encontrado"
    print_check("Entorno virtual 32-bit (venv32)", venv32_ok, venv32_details)

    # ========================================================================
    # DEPENDENCIAS PYTHON
    # ========================================================================
    print(f"\n{Colors.BOLD}3. DEPENDENCIAS PYTHON (64-bit){Colors.RESET}")
    print("─" * 70)

    if venv_ok:
        python_64_exe = str(venv_path / 'Scripts' / 'python.exe')
        key_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pyodbc', 'firebird-driver']
        packages_status = check_python_packages(python_64_exe, key_packages)

        for package, installed in packages_status.items():
            print_check(f"  {package}", installed)
    else:
        print(f"  {Colors.YELLOW}⚠ Entorno virtual no encontrado{Colors.RESET}")

    print(f"\n{Colors.BOLD}4. DEPENDENCIAS PYTHON (32-bit){Colors.RESET}")
    print("─" * 70)

    if venv32_ok:
        python_32_exe = str(venv32_path / 'Scripts' / 'python.exe')
        key_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pyodbc', 'firebird-driver']
        packages_status = check_python_packages(python_32_exe, key_packages)

        for package, installed in packages_status.items():
            print_check(f"  {package}", installed)
    else:
        print(f"  {Colors.YELLOW}⚠ Entorno virtual no encontrado{Colors.RESET}")

    # ========================================================================
    # DEPENDENCIAS NODE.JS
    # ========================================================================
    print(f"\n{Colors.BOLD}5. DEPENDENCIAS NODE.JS{Colors.RESET}")
    print("─" * 70)

    frontend_dir = project_root / 'frontend'
    if check_directory_exists(frontend_dir):
        key_packages = ['react', 'react-dom', 'axios', '@mui/material', 'vite']
        packages_status = check_node_packages(frontend_dir, key_packages)

        for package, installed in packages_status.items():
            print_check(f"  {package}", installed)
    else:
        print(f"  {Colors.YELLOW}⚠ Directorio frontend no encontrado{Colors.RESET}")

    # ========================================================================
    # CONFIGURACIÓN
    # ========================================================================
    print(f"\n{Colors.BOLD}6. ARCHIVOS DE CONFIGURACIÓN{Colors.RESET}")
    print("─" * 70)

    env_file = project_root / '.env'
    env_ok = check_file_exists(env_file)
    env_details = "Configurado" if env_ok else "No encontrado"
    print_check("Archivo .env", env_ok, env_details)

    requirements_file = project_root / 'requirements.txt'
    req_ok = check_file_exists(requirements_file)
    print_check("requirements.txt", req_ok)

    package_json = frontend_dir / 'package.json'
    pkg_ok = check_file_exists(package_json)
    print_check("package.json", pkg_ok)

    # ========================================================================
    # ESTRUCTURA DEL PROYECTO
    # ========================================================================
    print(f"\n{Colors.BOLD}7. ESTRUCTURA DEL PROYECTO{Colors.RESET}")
    print("─" * 70)

    backend_dir = project_root / 'backend'
    backend_ok = check_directory_exists(backend_dir)
    print_check("Directorio backend", backend_ok)

    if backend_ok:
        api_file = backend_dir / 'api' / 'main.py'
        print_check("  backend/api/main.py", check_file_exists(api_file))

        models_file = backend_dir / 'models' / 'fraud_models.py'
        print_check("  backend/models/fraud_models.py", check_file_exists(models_file))

        db_file = backend_dir / 'database' / 'db_context.py'
        print_check("  backend/database/db_context.py", check_file_exists(db_file))

    frontend_ok = check_directory_exists(frontend_dir)
    print_check("Directorio frontend", frontend_ok)

    if frontend_ok:
        app_file = frontend_dir / 'src' / 'App.tsx'
        print_check("  frontend/src/App.tsx", check_file_exists(app_file))

        api_file = frontend_dir / 'src' / 'services' / 'api.ts'
        print_check("  frontend/src/services/api.ts", check_file_exists(api_file))

    # ========================================================================
    # SCRIPTS DE INICIO
    # ========================================================================
    print(f"\n{Colors.BOLD}8. SCRIPTS DE INICIO{Colors.RESET}")
    print("─" * 70)

    scripts = [
        'iniciar_sistema.bat',
        'iniciar_backend.bat',
        'iniciar_backend_32bit.bat',
        'iniciar_frontend.bat'
    ]

    for script in scripts:
        script_path = project_root / script
        script_ok = check_file_exists(script_path)
        print_check(f"  {script}", script_ok)

    # ========================================================================
    # RESUMEN
    # ========================================================================
    print_header("RESUMEN")

    all_checks = [
        ("Software base", python_ok and node_ok),
        ("Python 32-bit", python_32_ok),
        ("Drivers ODBC", odbc_ok and firebird_ok),
        ("Entornos virtuales", venv_ok and venv32_ok),
        ("Configuración", env_ok),
        ("Estructura proyecto", backend_ok and frontend_ok),
    ]

    passed = sum(1 for _, status in all_checks if status)
    total = len(all_checks)
    percentage = (passed / total) * 100

    print(f"Verificaciones completadas: {passed}/{total} ({percentage:.1f}%)\n")

    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Sistema completamente configurado y listo para usar!{Colors.RESET}\n")
        print(f"Para iniciar el sistema, ejecute: {Colors.CYAN}iniciar_sistema.bat{Colors.RESET}")
    elif percentage >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Sistema casi listo, faltan algunos componentes opcionales{Colors.RESET}\n")
        print(f"Puede intentar ejecutar el sistema con: {Colors.CYAN}iniciar_sistema.bat{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Sistema incompleto, faltan componentes críticos{Colors.RESET}\n")
        print(f"Ejecute el instalador: {Colors.CYAN}python setup_automatico.py{Colors.RESET}")

    print()

if __name__ == '__main__':
    try:
        main()
        input("\nPresione ENTER para salir...")
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verificación cancelada{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        input("\nPresione ENTER para salir...")
        sys.exit(1)
