# test_desp_data.py
"""
Verifica los datos en la tabla DESP para detectar problemas
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.db_context import db_context
from datetime import datetime, timedelta

def analyze_desp_table():
    """Analiza la tabla DESP para entender los datos"""
    print("="*60)
    print("ANÁLISIS DE TABLA DESP")
    print("="*60)
    
    # 1. Verificar estructura y primeros registros
    print("\n1. PRIMEROS REGISTROS:")
    query = "SELECT FIRST 5 * FROM DESP WHERE CAN_DESP IS NOT NULL"
    try:
        results = db_context.execute_firebird_query(query)
        for i, row in enumerate(results, 1):
            print(f"\nRegistro {i}:")
            for key, value in row.items():
                if 'FEC' in key:
                    print(f"  {key}: {value} (tipo: {type(value).__name__})")
                elif 'CAN' in key or 'VTO' in key:
                    print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Buscar despachos grandes
    print("\n2. DESPACHOS GRANDES (>150 galones):")
    query = """
    SELECT FIRST 10 
        NUM_DESP, COD_CLIE, CAN_DESP, VTO_DESP, FEC_DESP
    FROM DESP
    WHERE CAN_DESP > 150
    ORDER BY CAN_DESP DESC
    """
    try:
        results = db_context.execute_firebird_query(query)
        print(f"Encontrados: {len(results)} despachos grandes")
        for r in results[:5]:
            print(f"  Despacho {r.get('NUM_DESP')}: {r.get('CAN_DESP')} gal, "
                  f"Cliente: {r.get('COD_CLIE')}, Fecha: {r.get('FEC_DESP')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Analizar formato de fechas
    print("\n3. FORMATOS DE FECHA EN DESP:")
    query = "SELECT FIRST 20 FEC_DESP FROM DESP WHERE FEC_DESP IS NOT NULL"
    try:
        results = db_context.execute_firebird_query(query)
        date_types = {}
        for r in results:
            fecha = r.get('FEC_DESP')
            tipo = type(fecha).__name__
            if tipo not in date_types:
                date_types[tipo] = []
            date_types[tipo].append(str(fecha)[:50])
        
        for tipo, ejemplos in date_types.items():
            print(f"  Tipo {tipo}:")
            for ejemplo in ejemplos[:3]:
                print(f"    '{ejemplo}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Agrupar por cliente
    print("\n4. CLIENTES CON MÁS DESPACHOS:")
    query = """
    SELECT COD_CLIE, COUNT(*) as TOTAL
    FROM DESP
    WHERE COD_CLIE IS NOT NULL
    GROUP BY COD_CLIE
    HAVING COUNT(*) > 10
    ORDER BY 2 DESC
    """
    try:
        results = db_context.execute_firebird_query(query, fetch_size=20)
        print(f"Clientes con >10 despachos: {len(results)}")
        for r in results[:5]:
            print(f"  Cliente {r.get('COD_CLIE')}: {r.get('TOTAL')} despachos")
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. Verificar si hay despachos múltiples el mismo día
    print("\n5. ANÁLISIS DE DESPACHOS MÚLTIPLES:")
    query = """
    SELECT FIRST 500
        COD_CLIE, FEC_DESP, CAN_DESP
    FROM DESP
    WHERE COD_CLIE IS NOT NULL
    ORDER BY COD_CLIE, FEC_DESP
    """
    try:
        results = db_context.execute_firebird_query(query)
        
        # Agrupar manualmente por cliente y fecha
        cliente_dias = {}
        for r in results:
            cliente = r.get('COD_CLIE')
            fecha_raw = r.get('FEC_DESP')
            
            # Intentar obtener solo la fecha (sin hora)
            fecha_dia = None
            if fecha_raw:
                try:
                    if isinstance(fecha_raw, str):
                        # Tomar solo los primeros 10 caracteres (DD/MM/YYYY)
                        fecha_dia = fecha_raw[:10]
                    elif isinstance(fecha_raw, datetime):
                        fecha_dia = fecha_raw.date()
                except:
                    continue
            
            if cliente and fecha_dia:
                key = f"{cliente}_{fecha_dia}"
                if key not in cliente_dias:
                    cliente_dias[key] = 0
                cliente_dias[key] += 1
        
        # Encontrar días con múltiples despachos
        multiples = {k: v for k, v in cliente_dias.items() if v > 3}
        print(f"Días con >3 despachos del mismo cliente: {len(multiples)}")
        
        for key, count in list(multiples.items())[:5]:
            cliente, fecha = key.split('_', 1)
            print(f"  Cliente {cliente} el {fecha}: {count} despachos")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # 6. Insertar datos de prueba si no hay suficientes
    print("\n6. VERIFICACIÓN DE DATOS DE PRUEBA:")
    try:
        # Verificar si ya existen datos de prueba
        check_query = "SELECT COUNT(*) as TOTAL FROM DESP WHERE COD_CLIE = 'TEST001'"
        result = db_context.execute_firebird_query(check_query)
        existing = result[0].get('TOTAL', 0) if result else 0
        
        if existing == 0:
            print("  No hay datos de prueba. ¿Desea insertarlos? (s/n): ", end="")
            if input().strip().lower() == 's':
                insert_test_fuel_data()
        else:
            print(f"  Ya existen {existing} registros de prueba")
    except Exception as e:
        print(f"  Error verificando datos de prueba: {e}")

def insert_test_fuel_data():
    """Inserta datos de prueba en DESP"""
    try:
        conn = db_context.get_firebird_connection()
        cursor = conn.cursor()
        
        # Insertar despachos de prueba
        test_data = [
            # Cliente con despacho excesivo
            (99001, 'TEST001', 'CLIENTE PRUEBA COMBUSTIBLE', 'PREMIUM', 250.5, 875.50),
            # Cliente con múltiples despachos el mismo día
            (99002, 'TEST002', 'TRANSPORTE SOSPECHOSO', 'DIESEL', 80.0, 280.00),
            (99003, 'TEST002', 'TRANSPORTE SOSPECHOSO', 'DIESEL', 85.0, 297.50),
            (99004, 'TEST002', 'TRANSPORTE SOSPECHOSO', 'DIESEL', 90.0, 315.00),
            (99005, 'TEST002', 'TRANSPORTE SOSPECHOSO', 'DIESEL', 95.0, 332.50),
        ]
        
        inserted = 0
        for num, cod_clie, nom_clie, prod, cantidad, valor in test_data:
            try:
                query = f"""
                INSERT INTO DESP (NUM_DESP, COD_CLIE, NOM_PROD, 
                                CAN_DESP, VTO_DESP, FEC_DESP)
                VALUES ({num}, '{cod_clie}', '{prod}', 
                       {cantidad}, {valor}, CURRENT_TIMESTAMP)
                """
                cursor.execute(query)
                inserted += 1
            except Exception as e:
                print(f"    Error insertando {num}: {e}")
        
        conn.commit()
        print(f"  ✓ {inserted} despachos de prueba insertados")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error insertando datos: {e}")

if __name__ == "__main__":
    print("\nTEST DE DATOS EN TABLA DESP")
    print("="*60)
    
    analyze_desp_table()
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("="*60)
    
    input("\nPresiona Enter para salir...")