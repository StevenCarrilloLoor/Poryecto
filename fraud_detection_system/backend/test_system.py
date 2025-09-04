# backend/test_system.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_context import db_context
from services.detectors import FacturasAnomalias, RoboDeCombustible, ManipulacionDatos
from datetime import datetime
import json

def test_connections():
    """Prueba las conexiones a las bases de datos"""
    print("="*60)
    print("PROBANDO CONEXIONES")
    print("="*60)
    
    # 1. Probar SQL Server
    try:
        with db_context.get_session() as session:
            # Contar casos existentes
            from models.fraud_models import FraudCase
            count = session.query(FraudCase).count()
            print(f"✓ SQL Server conectado - Casos existentes: {count}")
    except Exception as e:
        print(f"✗ Error SQL Server: {e}")
        return False
    
    # 2. Probar Firebird
    try:
        query = "SELECT FIRST 1 * FROM DCTO"
        result = db_context.execute_firebird_query(query)
        print(f"✓ Firebird conectado - Registros recuperados: {len(result)}")
    except Exception as e:
        print(f"✗ Error Firebird: {e}")
        return False
    
    return True

def test_detectors():
    """Ejecuta los detectores y muestra resultados"""
    print("\n" + "="*60)
    print("EJECUTANDO DETECTORES")
    print("="*60)
    
    detectors = [
        ("Facturas Anomalías", FacturasAnomalias()),
        ("Robo Combustible", RoboDeCombustible()),
        ("Manipulación Datos", ManipulacionDatos())
    ]
    
    total_casos = 0
    
    for name, detector in detectors:
        print(f"\nEjecutando {name}...")
        try:
            results = detector.detect()
            print(f"  Casos detectados: {len(results)}")
            
            if results:
                # Mostrar primer caso como ejemplo
                case = results[0]
                print(f"  Ejemplo: {case['title']}")
                print(f"  Severidad: {case['severity'].value}")
                if case.get('amount'):
                    print(f"  Monto: ${case['amount']:,.2f}")
                
                # Guardar en base de datos
                for fraud_data in results:
                    try:
                        saved_case = db_context.create_fraud_case(fraud_data)
                        print(f"  ✓ Caso guardado: {saved_case.case_number}")
                        total_casos += 1
                    except Exception as e:
                        print(f"  ✗ Error guardando caso: {e}")
            
        except Exception as e:
            print(f"  ✗ Error en detector: {e}")
            import traceback
            traceback.print_exc()
    
    return total_casos

def check_firebird_data():
    """Verifica que hay datos en Firebird para analizar"""
    print("\n" + "="*60)
    print("VERIFICANDO DATOS EN FIREBIRD")
    print("="*60)
    
    # Queries corregidas para Firebird
    tables = {
        'DCTO': 'SELECT COUNT(*) FROM DCTO',
        'MOVI': 'SELECT COUNT(*) FROM MOVI',
        'CLIE': 'SELECT COUNT(*) FROM CLIE',
        'DESP': 'SELECT COUNT(*) FROM DESP WHERE FEC_DESP IS NOT NULL',
        'TANQ_MOV': 'SELECT COUNT(*) FROM TANQ_MOV',
        'XDCTO': 'SELECT COUNT(*) FROM XDCTO'
    }
    
    for table, query in tables.items():
        try:
            result = db_context.execute_firebird_query(query)
            # En Firebird, COUNT(*) devuelve una columna sin nombre o con nombre COUNT
            if result and len(result) > 0:
                # Obtener el primer valor del primer registro
                first_row = result[0]
                # Firebird puede devolver el count con diferentes nombres
                count = first_row.get('COUNT', first_row.get('COUNT(*)') or list(first_row.values())[0])
                print(f"  {table}: {count} registros")
            else:
                print(f"  {table}: 0 registros")
        except Exception as e:
            print(f"  {table}: Error - {str(e)[:50]}...")

def test_api():
    """Prueba los endpoints de la API"""
    print("\n" + "="*60)
    print("PROBANDO API")
    print("="*60)
    
    import requests
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        ('GET', '/'),
        ('GET', '/api/fraud-cases'),
        ('GET', '/api/dashboard/stats'),
        ('GET', '/api/detector-configs'),
    ]
    
    for method, endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.request(method, url, timeout=5)
            print(f"  {method} {endpoint}: {response.status_code}")
            
            if endpoint == '/api/dashboard/stats' and response.status_code == 200:
                stats = response.json()
                print(f"    Total casos: {stats.get('total_cases', 0)}")
                print(f"    Pendientes: {stats.get('pending_cases', 0)}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ✗ API no está corriendo. Inicie con: cd backend && python -m uvicorn api.main:app --reload")
            return False
        except Exception as e:
            print(f"  {method} {endpoint}: Error - {e}")
    
    return True

def insert_test_data():
    """Inserta datos de prueba para generar alertas"""
    print("\n" + "="*60)
    print("INSERTANDO DATOS DE PRUEBA")
    print("="*60)
    
    try:
        conn = db_context.get_firebird_connection()
        cursor = conn.cursor()
        
        # Primero, verificar si existen los clientes TEST
        cursor.execute("SELECT COUNT(*) FROM CLIE WHERE COD_CLIE = 'TEST001'")
        if cursor.fetchone()[0] == 0:
            # Crear cliente de prueba
            cursor.execute("""
                INSERT INTO CLIE (COD_CLIE, NOM_CLIE, RUC_CLIE) 
                VALUES ('TEST001', 'CLIENTE PRUEBA 001', '9999999999')
            """)
            cursor.execute("""
                INSERT INTO CLIE (COD_CLIE, NOM_CLIE, RUC_CLIE) 
                VALUES ('TEST002', 'CLIENTE PRUEBA 002', '8888888888')
            """)
            print("  ✓ Clientes de prueba creados")
        
        # Insertar facturas sospechosas
        from datetime import datetime, timedelta
        fecha_hoy = datetime.now()
        
        test_data = [
            # Facturas con montos redondos para el mismo cliente
            (9999001, 'FC', '99001', 'TEST001', 1000.00, 0, 120.00, 0),
            (9999002, 'FC', '99002', 'TEST001', 2000.00, 0, 240.00, 0),
            (9999003, 'FC', '99003', 'TEST001', 3000.00, 0, 360.00, 0),
            # Factura con descuento excesivo (50%)
            (9999004, 'FC', '99004', 'TEST002', 10000.00, 0, 1200.00, 5000.00),
        ]
        
        inserted = 0
        for sec, tip, num, cliente, tni, tsi, iva, dsc in test_data:
            try:
                # Verificar si ya existe
                cursor.execute(f"SELECT COUNT(*) FROM DCTO WHERE SEC_DCTO = {sec}")
                if cursor.fetchone()[0] == 0:
                    query = f"""
                        INSERT INTO DCTO (SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO, 
                                        COD_CLIE, TNI_DCTO, TSI_DCTO, IVA_DCTO, DSC_DCTO)
                        VALUES ({sec}, '{tip}', '{num}', 'NOW', 
                               '{cliente}', {tni}, {tsi}, {iva}, {dsc})
                    """
                    cursor.execute(query)
                    inserted += 1
            except Exception as e:
                print(f"  Error insertando registro {sec}: {e}")
        
        conn.commit()
        print(f"  ✓ {inserted} registros de prueba insertados")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Error insertando datos de prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Limpia los datos de prueba"""
    print("\n" + "="*60)
    print("LIMPIANDO DATOS DE PRUEBA")
    print("="*60)
    
    try:
        conn = db_context.get_firebird_connection()
        cursor = conn.cursor()
        
        # Eliminar registros de prueba
        cursor.execute("DELETE FROM DCTO WHERE SEC_DCTO >= 9999000")
        cursor.execute("DELETE FROM CLIE WHERE COD_CLIE LIKE 'TEST%'")
        conn.commit()
        
        print("  ✓ Datos de prueba eliminados")
        cursor.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Error limpiando: {e}")
        return False

def show_sample_data():
    """Muestra algunos datos de ejemplo de Firebird"""
    print("\n" + "="*60)
    print("DATOS DE EJEMPLO EN FIREBIRD")
    print("="*60)
    
    try:
        # Mostrar algunas facturas recientes
        query = """
            SELECT FIRST 5 
                D.SEC_DCTO, D.TIP_DCTO, D.NUM_DCTO, 
                D.FEC_DCTO, D.COD_CLIE, 
                D.TNI_DCTO, D.TSI_DCTO, D.IVA_DCTO
            FROM DCTO D
            WHERE D.TIP_DCTO IN ('FC', 'FV')
            ORDER BY D.SEC_DCTO DESC
        """
        
        facturas = db_context.execute_firebird_query(query)
        
        if facturas:
            print("\nÚltimas facturas:")
            for f in facturas[:3]:
                total = (f.get('TNI_DCTO', 0) or 0) + (f.get('TSI_DCTO', 0) or 0) + (f.get('IVA_DCTO', 0) or 0)
                print(f"  Factura {f.get('NUM_DCTO', 'N/A')}: ${total:,.2f} - Cliente: {f.get('COD_CLIE', 'N/A')}")
        else:
            print("  No se encontraron facturas")
            
    except Exception as e:
        print(f"  Error obteniendo datos de ejemplo: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" SISTEMA DE DETECCIÓN DE FRAUDE - PRUEBAS")
    print("="*60)
    
    # 1. Probar conexiones
    if not test_connections():
        print("\n✗ Error en conexiones. Revise configuración.")
        sys.exit(1)
    
    # 2. Verificar datos existentes
    check_firebird_data()
    
    # 3. Mostrar algunos datos de ejemplo
    show_sample_data()
    
    # 4. Preguntar si insertar datos de prueba
    print("\n¿Desea insertar datos de prueba para generar alertas? (s/n): ", end="")
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        if insert_test_data():
            print("\nEjecutando detectores con datos de prueba...")
            casos = test_detectors()
            print(f"\n✓ Total de casos detectados y guardados: {casos}")
            
            # Preguntar si limpiar
            print("\n¿Desea eliminar los datos de prueba? (s/n): ", end="")
            if input().strip().lower() == 's':
                cleanup_test_data()
    else:
        # Solo ejecutar detectores con datos existentes
        print("\nEjecutando detectores con datos existentes...")
        casos = test_detectors()
        print(f"\n✓ Total de casos detectados: {casos}")
    
    # 5. Probar API si está corriendo
    print("\n¿La API está corriendo? (s/n): ", end="")
    if input().strip().lower() == 's':
        test_api()
    
    print("\n" + "="*60)
    print(" PRUEBAS COMPLETADAS")
    print("="*60)
    
    if casos > 0:
        print("\n✓ Se detectaron casos de fraude!")
        print("  1. Inicie el backend: cd backend && python -m uvicorn api.main:app --reload")
        print("  2. Inicie el frontend: cd frontend && npm run dev")
        print("  3. Abra el dashboard: http://localhost:5173/dashboard")
    else:
        print("\n✓ No se detectaron casos sospechosos.")
        print("  Esto es normal si los datos están correctos.")