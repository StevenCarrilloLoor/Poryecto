# test_firebird_dates.py
"""
Test para verificar el formato de fechas de Firebird
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.db_context import db_context
from datetime import datetime

def test_date_formats():
    """Prueba diferentes queries de fecha"""
    print("="*60)
    print("PROBANDO FORMATOS DE FECHA EN FIREBIRD")
    print("="*60)
    
    queries = [
        # Query 1: Fecha directa
        ("Fecha directa", "SELECT FIRST 1 FEC_DCTO FROM DCTO WHERE FEC_DCTO IS NOT NULL"),
        
        # Query 2: Fecha actual
        ("Fecha actual", "SELECT CURRENT_DATE as FECHA FROM RDB$DATABASE"),
        
        # Query 3: Timestamp actual
        ("Timestamp actual", "SELECT CURRENT_TIMESTAMP as FECHA FROM RDB$DATABASE"),
        
        # Query 4: Despachos con fecha
        ("Despacho con fecha", "SELECT FIRST 1 FEC_DESP FROM DESP WHERE FEC_DESP IS NOT NULL"),
    ]
    
    for nombre, query in queries:
        try:
            print(f"\n{nombre}:")
            print(f"  Query: {query}")
            resultado = db_context.execute_firebird_query(query)
            
            if resultado and len(resultado) > 0:
                row = resultado[0]
                for key, value in row.items():
                    print(f"  {key}: {value}")
                    print(f"  Tipo: {type(value)}")
                    
                    # Intentar parsear si es string
                    if isinstance(value, str):
                        value_clean = value.strip()
                        print(f"  String limpio: '{value_clean}'")
                        
                        # Probar diferentes formatos
                        formats = [
                            '%d/%m/%Y %H:%M:%S',
                            '%Y-%m-%d %H:%M:%S',
                            '%d/%m/%Y',
                            '%Y-%m-%d',
                            '%d.%m.%Y %H:%M:%S',
                            '%d-%m-%Y %H:%M:%S'
                        ]
                        
                        for fmt in formats:
                            try:
                                parsed = datetime.strptime(value_clean[:19], fmt)
                                print(f"  ✓ Parseado con formato '{fmt}': {parsed}")
                                break
                            except:
                                continue
                    elif isinstance(value, datetime):
                        print(f"  ✓ Ya es datetime: {value}")
            else:
                print(f"  Sin resultados")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

def test_numeric_values():
    """Prueba valores numéricos de Firebird"""
    print("\n" + "="*60)
    print("PROBANDO VALORES NUMÉRICOS EN FIREBIRD")
    print("="*60)
    
    query = """
    SELECT FIRST 5 
        TNI_DCTO, TSI_DCTO, IVA_DCTO, DSC_DCTO,
        TNI_DCTO + TSI_DCTO + IVA_DCTO as TOTAL_CALC
    FROM DCTO 
    WHERE TNI_DCTO IS NOT NULL
    """
    
    try:
        resultados = db_context.execute_firebird_query(query)
        
        for i, row in enumerate(resultados[:3], 1):
            print(f"\nRegistro {i}:")
            for key, value in row.items():
                print(f"  {key}: {value} (tipo: {type(value).__name__})")
                
                # Probar conversión a float
                try:
                    if value is not None:
                        float_val = float(value)
                        print(f"    -> Como float: {float_val}")
                except Exception as e:
                    print(f"    -> Error convirtiendo a float: {e}")
                    
    except Exception as e:
        print(f"Error: {e}")

def test_division():
    """Prueba divisiones en Firebird"""
    print("\n" + "="*60)
    print("PROBANDO DIVISIONES EN FIREBIRD")
    print("="*60)
    
    # Query que evita división por cero
    query = """
    SELECT FIRST 5
        DSC_DCTO, TNI_DCTO,
        CASE 
            WHEN TNI_DCTO > 0 THEN DSC_DCTO * 100.0 / TNI_DCTO 
            ELSE 0 
        END as PORCENTAJE
    FROM DCTO
    WHERE DSC_DCTO > 0 AND TNI_DCTO > 0
    """
    
    try:
        resultados = db_context.execute_firebird_query(query)
        
        for row in resultados[:3]:
            print(f"\nDescuento: {row['DSC_DCTO']}, Total: {row['TNI_DCTO']}")
            print(f"  Porcentaje calculado en SQL: {row.get('PORCENTAJE', 'N/A')}")
            
            # Calcular en Python
            if row['TNI_DCTO'] and row['DSC_DCTO']:
                try:
                    dsc = float(row['DSC_DCTO'])
                    tni = float(row['TNI_DCTO'])
                    if tni > 0:
                        pct = (dsc / tni) * 100
                        print(f"  Porcentaje calculado en Python: {pct:.2f}%")
                except Exception as e:
                    print(f"  Error calculando en Python: {e}")
                    
    except Exception as e:
        print(f"Error: {e}")

def test_data_manipulation_queries():
    """Prueba queries del detector de manipulación de datos"""
    print("\n" + "="*60)
    print("PROBANDO QUERIES DE MANIPULACIÓN DE DATOS")
    print("="*60)
    
    # Query para XDCTO
    query = """
    SELECT FIRST 10 COD_XUSUA, FEC_XDCTO
    FROM XDCTO
    WHERE FEC_XDCTO IS NOT NULL
    ORDER BY FEC_XDCTO DESC
    """
    
    try:
        print("\nRegistros de auditoría (XDCTO):")
        resultados = db_context.execute_firebird_query(query)
        
        usuarios_count = {}
        for row in resultados:
            usuario = row.get('COD_XUSUA', 'UNKNOWN')
            fecha = row.get('FEC_XDCTO')
            
            print(f"  Usuario: {usuario}, Fecha: {fecha} (tipo: {type(fecha).__name__})")
            
            # Contar por usuario
            if usuario not in usuarios_count:
                usuarios_count[usuario] = 0
            usuarios_count[usuario] += 1
        
        print(f"\nResumen: {usuarios_count}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("\nTEST DE COMPATIBILIDAD FIREBIRD")
    print("="*60)
    
    # Ejecutar todos los tests
    test_date_formats()
    test_numeric_values()
    test_division()
    test_data_manipulation_queries()
    
    print("\n" + "="*60)
    print("TESTS COMPLETADOS")
    print("="*60)
    
    input("\nPresiona Enter para salir...")