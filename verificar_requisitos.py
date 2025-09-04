"""
SCRIPT DE VERIFICACIÓN MÍNIMO - NO MODIFICA NADA
Solo verifica si tienes todo lo necesario para conectar a Firebird
"""

import struct
import sys
import os

print("="*60)
print("VERIFICACIÓN DE REQUISITOS PARA FIREBIRD 32 BITS")
print("="*60)

# 1. Verificar Python
bits = struct.calcsize('P') * 8
print(f"\n1. Python actual: {bits} bits")
print(f"   Ubicación: {sys.executable}")

if bits == 32:
    print("   ✅ Python de 32 bits - Compatible con servidor")
else:
    print("   ⚠ Python de 64 bits - NO compatible con servidor de 32 bits")
    print("   Necesitas usar Python de 32 bits")

# 2. Verificar si pyodbc está instalado
print("\n2. Verificando pyodbc...")
try:
    import pyodbc
    print("   ✅ pyodbc está instalado")
    
    # Buscar driver Firebird
    print("\n3. Drivers ODBC disponibles:")
    drivers = pyodbc.drivers()
    firebird_found = False
    for driver in drivers:
        if 'Firebird' in driver or 'InterBase' in driver:
            print(f"   ✅ Driver Firebird encontrado: {driver}")
            firebird_found = True
            
    if not firebird_found:
        print("   ❌ No hay driver ODBC Firebird de 32 bits")
        print("   Instala: Firebird_ODBC_2.0.5.156_Win32.exe")
        
except ImportError:
    print("   ❌ pyodbc NO está instalado")
    print("   Ejecuta: pip install pyodbc")

# 3. Verificar gds32.dll
print("\n4. Verificando gds32.dll...")
paths_to_check = [
    "C:\\Windows\\SysWOW64\\gds32.dll",
    "C:\\Windows\\System32\\gds32.dll"
]

gds_found = False
for path in paths_to_check:
    if os.path.exists(path):
        print(f"   ✅ gds32.dll encontrado en: {path}")
        gds_found = True
        break

if not gds_found:
    print("   ❌ gds32.dll NO encontrado")
    print("   Instala Firebird Client 2.5 de 32 bits")

# 4. Verificar base de datos
print("\n5. Verificando base de datos...")
db_path = r"C:\Users\steve\Desktop\Trabajos\Petrolrios\Instalador Firebird-FlameRobin-ODBCFirebird\BD\BD PRUEBA\CONTAC.FDB"
if os.path.exists(db_path):
    print(f"   ✅ Base de datos encontrada")
    print(f"   Tamaño: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
else:
    print(f"   ❌ No se encuentra: {db_path}")

# Resumen
print("\n" + "="*60)
print("RESUMEN:")
print("="*60)

if bits == 32 and firebird_found and gds_found:
    print("\n✅ TODO LISTO para conectar a Firebird")
    print("\nPrueba de conexión (copia y ejecuta):")
    print("-" * 40)
    print("""
import pyodbc
dsn = "DRIVER={Firebird/InterBase(r) driver};DBNAME=localhost:C:\\\\Users\\\\steve\\\\Desktop\\\\Trabajos\\\\Petrolrios\\\\Instalador Firebird-FlameRobin-ODBCFirebird\\\\BD\\\\BD PRUEBA\\\\CONTAC.FDB;UID=sysdba;PWD=jmcjmc;"
try:
    conn = pyodbc.connect(dsn)
    print("Conexión exitosa!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
""")
else:
    print("\n❌ Faltan componentes:")
    if bits != 32:
        print("  - Python de 32 bits")
    if not firebird_found:
        print("  - Driver ODBC Firebird de 32 bits")
    if not gds_found:
        print("  - Biblioteca gds32.dll")

input("\nPresiona Enter para salir...")