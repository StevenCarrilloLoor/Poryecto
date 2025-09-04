"""
CONFIGURACIÓN PYTHON 32 BITS PARA SISTEMA DE DETECCIÓN DE FRAUDE
================================================================
Guarda este archivo como: setup_32bits.py
Ejecuta con: C:\Python313-32\python.exe setup_32bits.py
"""

import os
import sys
import subprocess
import struct
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60)

def run_command(command, shell=True):
    """Ejecuta comando y retorna resultado"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print_header("CONFIGURACIÓN SISTEMA DETECCIÓN FRAUDE")
    print("Este script configurará Python 32 bits para tu proyecto")
    print("SIN modificar tu configuración actual de 64 bits")
    
    # 1. Verificar arquitectura de Python actual
    print("\n1. VERIFICACIÓN DE PYTHON")
    print("-" * 40)
    bits = struct.calcsize('P') * 8
    python_path = sys.executable
    
    print(f"   Python actual: {python_path}")
    print(f"   Arquitectura: {bits} bits")
    
    if bits != 32:
        print("\n   ⚠ IMPORTANTE: Debes ejecutar con Python 32 bits")
        print("   Comando correcto:")
        print("   C:\\Python313-32\\python.exe setup_32bits.py")
        response = input("\n   ¿Continuar de todos modos? (s/n): ").lower()
        if response != 's':
            return False
    
    # 2. Detectar carpeta del proyecto
    print("\n2. UBICACIÓN DEL PROYECTO")
    print("-" * 40)
    
    # Buscar en la ruta actual o preguntar
    current_path = Path.cwd()
    if "fraud_detection_system" in str(current_path):
        project_path = current_path
        while project_path.name != "fraud_detection_system" and project_path.parent != project_path:
            project_path = project_path.parent
    else:
        # Ruta por defecto de tu proyecto
        project_path = Path("C:/Users/steve/Desktop/Trabajos/Petrolrios/Poryecto/fraud_detection_system")
    
    if not project_path.exists():
        print(f"   ✗ No encontrado en: {project_path}")
        custom_path = input("   Ingresa la ruta completa del proyecto: ").strip()
        project_path = Path(custom_path)
    
    backend_path = project_path / "backend"
    if not backend_path.exists():
        print(f"   ✗ No se encontró la carpeta backend en: {project_path}")
        return False
    
    print(f"   ✓ Proyecto encontrado: {project_path}")
    print(f"   ✓ Backend en: {backend_path}")
    
    # 3. Crear entorno virtual 32 bits (sin eliminar el existente)
    print("\n3. CONFIGURACIÓN DE ENTORNO VIRTUAL")
    print("-" * 40)
    
    os.chdir(backend_path)
    venv32_path = backend_path / "venv32"
    
    if venv32_path.exists():
        print("   ⚠ Ya existe venv32")
        response = input("   ¿Recrear entorno? (s/n): ").lower()
        if response == 's':
            print("   Eliminando venv32 anterior...")
            shutil.rmtree(venv32_path)
    
    if not venv32_path.exists():
        print("   Creando venv32 (esto puede tomar unos minutos)...")
        if bits == 32:
            # Si ya estamos en Python 32 bits
            success, _, _ = run_command(f'"{python_path}" -m venv venv32')
        else:
            # Usar Python 32 bits específicamente
            python32 = "C:\\Python313-32\\python.exe"
            if not Path(python32).exists():
                print(f"   ✗ No se encuentra Python 32 bits en: {python32}")
                print("   Por favor instala Python 3.13 de 32 bits primero")
                return False
            success, _, _ = run_command(f'"{python32}" -m venv venv32')
        
        if success:
            print("   ✓ Entorno venv32 creado exitosamente")
        else:
            print("   ✗ Error creando entorno virtual")
            return False
    
    # 4. Obtener rutas del entorno virtual
    pip32 = venv32_path / "Scripts" / "pip.exe"
    python32_venv = venv32_path / "Scripts" / "python.exe"
    
    # 5. Actualizar pip
    print("\n4. INSTALACIÓN DE DEPENDENCIAS")
    print("-" * 40)
    print("   Actualizando pip...")
    run_command(f'"{pip32}" install --upgrade pip')
    
    # 6. Instalar dependencias del proyecto
    packages = [
        # Core
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "websockets==12.0",
        
        # Database
        "sqlalchemy==2.0.23",
        "pyodbc==5.0.1",
        "python-dotenv==1.0.0",
        
        # Utilities
        "pydantic==2.5.0",
        "python-dateutil==2.8.2",
    ]
    
    print("   Instalando paquetes principales...")
    for i, package in enumerate(packages, 1):
        print(f"   [{i}/{len(packages)}] Instalando {package.split('==')[0]}...")
        success, _, error = run_command(f'"{pip32}" install {package}')
        if not success and "already satisfied" not in error:
            print(f"      ⚠ Problema con {package}")
    
    print("   ✓ Dependencias instaladas")
    
    # 7. NO instalar firebird-driver ya que usaremos ODBC
    print("\n5. CONFIGURACIÓN FIREBIRD")
    print("-" * 40)
    print("   Usando conexión ODBC (no firebird-driver)")
    print("   Verificando drivers ODBC...")
    
    # Crear script de verificación
    check_script = '''
import pyodbc
import struct
import sys

print(f"Python: {struct.calcsize('P') * 8} bits")
print("\\nDrivers ODBC disponibles:")
drivers = pyodbc.drivers()
firebird_found = False
for driver in drivers:
    if 'Firebird' in driver or 'InterBase' in driver:
        print(f"  ✓ {driver}")
        firebird_found = True
    else:
        print(f"  - {driver}")

if not firebird_found:
    print("\\n✗ No se encontró driver Firebird ODBC de 32 bits")
    sys.exit(1)
else:
    print("\\n✓ Driver Firebird encontrado")
'''
    
    check_file = backend_path / "check_odbc.py"
    with open(check_file, 'w') as f:
        f.write(check_script)
    
    success, output, _ = run_command(f'"{python32_venv}" "{check_file}"')
    print(output)
    check_file.unlink()  # Eliminar archivo temporal
    
    # 8. Crear script de prueba de conexión
    print("\n6. CREANDO SCRIPTS DE UTILIDAD")
    print("-" * 40)
    
    # Script de prueba de conexión
    test_script = '''import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("PRUEBA DE CONEXIÓN - PYTHON 32 BITS")
print("="*60)

# Test Firebird
print("\\n1. Probando Firebird...")
try:
    dsn = os.getenv('FIREBIRD_DSN')
    if not dsn:
        print("   ✗ FIREBIRD_DSN no está configurado en .env")
    else:
        conn = pyodbc.connect(dsn)
        cursor = conn.cursor()
        
        # Probar query simple
        cursor.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        count = cursor.fetchone()[0]
        print(f"   ✓ Conexión exitosa - {count} tablas encontradas")
        
        conn.close()
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test SQL Server
print("\\n2. Probando SQL Server...")
try:
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    
    if os.getenv('DB_TRUSTED_CONNECTION', 'yes').lower() == 'yes':
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    else:
        username = os.getenv('DB_USERNAME')
        password = os.getenv('DB_PASSWORD')
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    
    conn = pyodbc.connect(conn_str)
    print(f"   ✓ Conexión exitosa a {database}")
    conn.close()
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\\n" + "="*60)
'''
    
    test_file = backend_path / "test_conexion_32bits.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    print(f"   ✓ Creado: test_conexion_32bits.py")
    
    # 9. Crear archivo BAT para activar entorno
    bat_content = f'''@echo off
title Sistema Deteccion Fraude - Python 32 bits
echo ============================================
echo   SISTEMA DETECCION FRAUDE - PYTHON 32 BITS
echo ============================================
echo.

cd /d "{backend_path}"

echo Activando entorno virtual 32 bits...
call venv32\\Scripts\\activate.bat

echo.
python -c "import struct; print(f'Python activo: {{struct.calcsize(\\"P\\") * 8}} bits')"
echo.

echo Comandos disponibles:
echo   - python test_conexion_32bits.py  (probar conexiones)
echo   - python -m uvicorn api.main:app --reload  (iniciar API)
echo   - python test_firebird_tables.py  (verificar Firebird)
echo.

cmd /k
'''
    
    bat_file = backend_path / "activar_venv32.bat"
    with open(bat_file, 'w') as f:
        f.write(bat_content)
    print(f"   ✓ Creado: activar_venv32.bat")
    
    # 10. Crear script de inicio del sistema
    start_script = f'''@echo off
title Iniciar Sistema - Python 32 bits
cd /d "{backend_path}"
call venv32\\Scripts\\activate.bat
echo Iniciando API con Python 32 bits...
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
'''
    
    start_file = backend_path / "iniciar_api_32bits.bat"
    with open(start_file, 'w') as f:
        f.write(start_script)
    print(f"   ✓ Creado: iniciar_api_32bits.bat")
    
    # 11. Verificar .env
    print("\n7. VERIFICACIÓN DE CONFIGURACIÓN")
    print("-" * 40)
    
    env_file = project_path / ".env"
    if not env_file.exists():
        env_file = backend_path / ".env"
    
    if env_file.exists():
        print(f"   ✓ Archivo .env encontrado")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'FIREBIRD_DSN' in content:
                print("   ✓ FIREBIRD_DSN configurado")
            else:
                print("   ⚠ FIREBIRD_DSN no está en .env")
    else:
        print("   ⚠ No se encontró archivo .env")
    
    # Resumen final
    print_header("✅ CONFIGURACIÓN COMPLETADA")
    
    print(f"""
    ESTRUCTURA CREADA:
    ==================
    📁 {backend_path}/
       📁 venv32/          → Entorno Python 32 bits
       📄 test_conexion_32bits.py
       📄 activar_venv32.bat
       📄 iniciar_api_32bits.bat
    
    PRÓXIMOS PASOS:
    ===============
    
    1. INSTALAR DRIVERS (si no están):
       - Firebird_ODBC_2.0.5.156_Win32.exe (32 bits)
       - Firebird-2.5.2.26540_0_Win32.exe (cliente 32 bits)
    
    2. PROBAR CONEXIONES:
       - Doble clic en: activar_venv32.bat
       - Ejecutar: python test_conexion_32bits.py
    
    3. INICIAR SISTEMA:
       - Doble clic en: iniciar_api_32bits.bat
       - O desde el terminal activado: python -m uvicorn api.main:app --reload
    
    IMPORTANTE:
    ===========
    - Tu venv original (64 bits) NO fue modificado
    - Usa venv32 para producción (compatible con servidor)
    - Usa venv para desarrollo local si prefieres 64 bits
    """)
    
    return True

if __name__ == "__main__":
    try:
        if main():
            print("\n✅ Script completado exitosamente")
        else:
            print("\n⚠ Script terminado con advertencias")
    except KeyboardInterrupt:
        print("\n\n⚠ Script cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")