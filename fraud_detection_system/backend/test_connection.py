import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Test Firebird
try:
    dsn = os.getenv('FIREBIRD_DSN')
    conn = pyodbc.connect(dsn)
    print("✓ Conexión a Firebird exitosa")
    conn.close()
except Exception as e:
    print(f"✗ Error conectando a Firebird: {e}")

# Test SQL Server
try:
    server = os.getenv('DB_SERVER')
    database = 'master'  # Primero conectar a master
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    print("✓ Conexión a SQL Server exitosa")
    conn.close()
except Exception as e:
    print(f"✗ Error conectando a SQL Server: {e}")