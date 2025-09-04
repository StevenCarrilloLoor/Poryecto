import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("VERIFICACIÓN FINAL - DRIVER FIREBIRD ODBC 64 BITS")
print("="*60)

# 1. Buscar el driver Firebird
print("\n1. Buscando driver Firebird/InterBase...")
drivers = pyodbc.drivers()
firebird_driver = None

for driver in drivers:
    if 'Firebird' in driver or 'InterBase' in driver:
        print(f"   ✓ ENCONTRADO: {driver}")
        firebird_driver = driver
        break

if not firebird_driver:
    print("   ✗ Driver Firebird NO encontrado")
    print("\n   Asegúrate de:")
    print("   1. Haber instalado Firebird_ODBC_2.0.5.156_x64.exe")
    print("   2. Haberlo ejecutado como Administrador")
    print("   3. Haber reiniciado el terminal")
    exit(1)

# 2. Configurar y probar conexión
print(f"\n2. Probando conexión con driver: {firebird_driver}")
print("-"*50)

db_path = r"C:\Users\steve\Desktop\Trabajos\Petrolrios\Instalador Firebird-FlameRobin-ODBCFirebird\BD\BD PRUEBA\CONTAC.FDB"

# Verificar que existe el archivo
if not os.path.exists(db_path):
    print(f"   ✗ No se encuentra el archivo: {db_path}")
    exit(1)

# Probar conexión
dsn = f"DRIVER={{{firebird_driver}}};DBNAME=localhost:{db_path};UID=sysdba;PWD=jmcjmc;"

try:
    print("   Conectando...")
    conn = pyodbc.connect(dsn)
    print("   ✓ CONEXIÓN EXITOSA!")
    
    # Obtener información de la BD
    cursor = conn.cursor()
    
    # Versión de Firebird
    cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
    version = cursor.fetchone()
    print(f"\n   Firebird Version: {version[0] if version else 'Unknown'}")
    
    # Contar tablas
    cursor.execute("""
        SELECT COUNT(*) 
        FROM RDB$RELATIONS 
        WHERE RDB$SYSTEM_FLAG = 0
    """)
    table_count = cursor.fetchone()[0]
    print(f"   Número de tablas: {table_count}")
    
    # Mostrar primeras 10 tablas
    cursor.execute("""
        SELECT FIRST 10 RDB$RELATION_NAME 
        FROM RDB$RELATIONS 
        WHERE RDB$SYSTEM_FLAG = 0 
        ORDER BY RDB$RELATION_NAME
    """)
    
    print("\n   Primeras tablas encontradas:")
    for table in cursor.fetchall():
        print(f"     - {table[0].strip()}")
    
    conn.close()
    
    # 3. Mostrar configuración para el .env
    print("\n" + "="*60)
    print("✓ CONFIGURACIÓN EXITOSA")
    print("="*60)
    print("\nACTUALIZA tu archivo .env con esta línea:\n")
    print(f"FIREBIRD_DSN={dsn}")
    print("\n" + "="*60)
    
    # 4. Crear archivo de prueba actualizado
    print("\n3. Creando archivo de prueba actualizado...")
    
    test_code = f'''import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Test Firebird
try:
    dsn = os.getenv('FIREBIRD_DSN')
    conn = pyodbc.connect(dsn)
    print("✓ Conexión a Firebird exitosa")
    
    cursor = conn.cursor()
    cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
    version = cursor.fetchone()
    print(f"  Versión: {{version[0] if version else 'Unknown'}}")
    
    conn.close()
except Exception as e:
    print(f"✗ Error conectando a Firebird: {{e}}")

# Test SQL Server
try:
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={{server}};DATABASE={{database}};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    print("✓ Conexión a SQL Server exitosa")
    conn.close()
except Exception as e:
    print(f"✗ Error conectando a SQL Server: {{e}}")
'''
    
    with open('test_conexion_final.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("   ✓ Archivo 'test_conexion_final.py' creado")
    
except Exception as e:
    print(f"   ✗ Error al conectar: {e}")
    print(f"\n   Tipo de error: {type(e).__name__}")
    print("\n   Posibles causas:")
    print("   1. El servicio de Firebird no está ejecutándose")
    print("   2. Credenciales incorrectas")
    print("   3. Firewall bloqueando la conexión")
    
    # Intentar conexión local sin servidor
    print("\n   Intentando conexión local (sin servidor)...")
    dsn_local = f"DRIVER={{{firebird_driver}}};DBNAME={db_path};UID=sysdba;PWD=jmcjmc;"
    try:
        conn = pyodbc.connect(dsn_local)
        print("   ✓ Conexión local exitosa!")
        conn.close()
        print(f"\n   Usa este DSN en tu .env:")
        print(f"   FIREBIRD_DSN={dsn_local}")
    except Exception as e2:
        print(f"   ✗ Conexión local también falló: {e2}")