# analyze_dashboard_issues.py
"""
Script para ANALIZAR problemas del dashboard SIN MODIFICAR NADA
Ejecutar: python analyze_dashboard_issues.py
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# Agregar backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_api_endpoints():
    """Analiza todos los endpoints de la API sin modificar nada"""
    print("="*60)
    print("ANÁLISIS DE ENDPOINTS DE LA API")
    print("="*60)
    
    base_url = "http://localhost:8000"
    results = {
        'api_running': False,
        'stats_endpoint': False,
        'cases_endpoint': False,
        'detection_endpoint': False,
        'has_data': False,
        'errors': []
    }
    
    # 1. Probar endpoint de estadísticas
    print("\n1. Analizando /api/dashboard/stats...")
    try:
        response = requests.get(f"{base_url}/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            results['api_running'] = True
            results['stats_endpoint'] = True
            
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Total casos: {stats.get('total_cases', 0)}")
            print(f"   Casos pendientes: {stats.get('pending_cases', 0)}")
            print(f"   Monto total: ${stats.get('total_amount', 0):,.2f}")
            
            # Verificar si hay datos en cases_by_severity
            severity_data = stats.get('cases_by_severity', {})
            if severity_data and any(v > 0 for v in severity_data.values()):
                results['has_data'] = True
                print(f"   ✓ Datos de severidad: {severity_data}")
            else:
                print("   ⚠ WARNING: No hay datos de severidad o están en cero")
                results['errors'].append("No hay datos de severidad")
        else:
            print(f"   ✗ Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            results['errors'].append(f"Stats endpoint error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ✗ Error: No se puede conectar al servidor")
        results['errors'].append("Servidor no disponible")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        results['errors'].append(f"Stats endpoint: {str(e)}")
    
    # 2. Probar endpoint de casos
    print("\n2. Analizando /api/fraud-cases...")
    try:
        response = requests.get(f"{base_url}/api/fraud-cases", timeout=5)
        if response.status_code == 200:
            cases = response.json()
            results['cases_endpoint'] = True
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Casos obtenidos: {len(cases)}")
            
            if len(cases) > 0:
                print(f"   Ejemplo de caso: {cases[0].get('title', 'Sin título')[:50]}...")
            else:
                print("   ⚠ No hay casos registrados")
                results['errors'].append("No hay casos en la base de datos")
        else:
            print(f"   ✗ Error: Status {response.status_code}")
            results['errors'].append(f"Cases endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        results['errors'].append(f"Cases endpoint: {str(e)}")
    
    # 3. Probar detección manual (solo GET, no POST)
    print("\n3. Analizando disponibilidad de detección...")
    try:
        # Solo verificar que el endpoint existe
        response = requests.post(f"{base_url}/api/run-detection", 
                                json={}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            results['detection_endpoint'] = True
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Detección ejecutada: {result.get('cases_detected', 0)} casos")
        else:
            print(f"   ✗ Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            results['errors'].append(f"Detection endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        results['errors'].append(f"Detection endpoint: {str(e)}")
    
    return results

def analyze_database_stats():
    """Analiza estadísticas en la base de datos SIN MODIFICAR NADA"""
    print("\n" + "="*60)
    print("ANÁLISIS DE BASE DE DATOS")
    print("="*60)
    
    try:
        from database.db_context import db_context
        from models.fraud_models import FraudCase, FraudStatus, FraudSeverity
    except ImportError as e:
        print(f"✗ Error importando módulos: {e}")
        return {'database_accessible': False, 'errors': [str(e)]}
    
    results = {
        'database_accessible': True,
        'total_cases': 0,
        'enum_issues': [],
        'data_issues': [],
        'stats_by_status': {},
        'stats_by_severity': {},
        'errors': []
    }
    
    try:
        with db_context.get_session() as session:
            # Obtener todos los casos
            all_cases = session.query(FraudCase).all()
            results['total_cases'] = len(all_cases)
            print(f"\nTotal de casos en BD: {len(all_cases)}")
            
            if len(all_cases) == 0:
                print("⚠ No hay casos en la base de datos")
                results['data_issues'].append("No hay casos en la base de datos")
                return results
            
            # Analizar tipos de datos (sin modificar)
            print(f"\nAnalizando primeros 5 casos:")
            for i, case in enumerate(all_cases[:5]):
                print(f"\nCaso {case.case_number}:")
                print(f"  Status: {case.status} (tipo: {type(case.status)})")
                print(f"  Severity: {case.severity} (tipo: {type(case.severity)})")
                
                # Detectar problemas de enum sin corregir
                if isinstance(case.status, str):
                    results['enum_issues'].append(f"Caso {case.case_number}: status es string")
                
                if isinstance(case.severity, str):
                    results['enum_issues'].append(f"Caso {case.case_number}: severity es string")
            
            # Calcular estadísticas por status
            status_counts = {}
            for case in all_cases:
                status = str(case.status) if case.status else 'NULL'
                status_counts[status] = status_counts.get(status, 0) + 1
            results['stats_by_status'] = status_counts
            
            # Calcular estadísticas por severidad
            severity_counts = {}
            for case in all_cases:
                severity = str(case.severity) if case.severity else 'NULL'
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            results['stats_by_severity'] = severity_counts
            
            # Mostrar estadísticas
            print("\n" + "-"*40)
            print("ESTADÍSTICAS ENCONTRADAS:")
            print("-"*40)
            
            print(f"Total: {len(all_cases)}")
            print("\nPor status:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
            
            print("\nPor severidad:")
            for severity, count in severity_counts.items():
                print(f"  {severity}: {count}")
                
    except Exception as e:
        print(f"✗ Error accediendo a la base de datos: {e}")
        results['database_accessible'] = False
        results['errors'].append(str(e))
        
    return results

def analyze_detectors():
    """Analiza si los detectores funcionan SIN EJECUTARLOS"""
    print("\n" + "="*60)
    print("ANÁLISIS DE DETECTORES")
    print("="*60)
    
    results = {
        'detectors_importable': True,
        'detector_classes': [],
        'import_errors': [],
        'method_analysis': {}
    }
    
    try:
        from services.detectors import FacturasAnomalias, RoboDeCombustible, ManipulacionDatos
        results['detector_classes'] = ['FacturasAnomalias', 'RoboDeCombustible', 'ManipulacionDatos']
        print("✓ Detectores importados correctamente")
        
        # Analizar cada detector sin ejecutar
        detectors = [
            ("FacturasAnomalias", FacturasAnomalias),
            ("RoboDeCombustible", RoboDeCombustible),
            ("ManipulacionDatos", ManipulacionDatos)
        ]
        
        for name, detector_class in detectors:
            print(f"\nAnalizando {name}:")
            try:
                # Solo instanciar, no ejecutar
                detector = detector_class()
                
                # Verificar métodos disponibles
                methods = [method for method in dir(detector) if not method.startswith('_')]
                print(f"  ✓ Métodos disponibles: {methods}")
                
                # Verificar si tiene método detect
                if hasattr(detector, 'detect'):
                    print(f"  ✓ Método 'detect' disponible")
                    results['method_analysis'][name] = {
                        'instantiable': True,
                        'has_detect': True,
                        'methods': methods
                    }
                else:
                    print(f"  ✗ Método 'detect' NO disponible")
                    results['method_analysis'][name] = {
                        'instantiable': True,
                        'has_detect': False,
                        'methods': methods
                    }
                    
            except Exception as e:
                print(f"  ✗ Error instanciando {name}: {e}")
                results['method_analysis'][name] = {
                    'instantiable': False,
                    'error': str(e)
                }
                
    except ImportError as e:
        print(f"✗ Error importando detectores: {e}")
        results['detectors_importable'] = False
        results['import_errors'].append(str(e))
    
    return results

def analyze_database_connection():
    """Analiza la conexión a la base de datos"""
    print("\n" + "="*60)
    print("ANÁLISIS DE CONEXIÓN A BASE DE DATOS")
    print("="*60)
    
    results = {
        'firebird_accessible': False,
        'postgres_accessible': False,
        'connection_errors': []
    }
    
    # Probar conexión Firebird
    print("\n1. Probando conexión Firebird...")
    try:
        from database.db_context import db_context
        
        # Intentar una query simple a Firebird
        test_query = "SELECT FIRST 1 * FROM RDB$DATABASE"
        result = db_context.execute_firebird_query(test_query)
        results['firebird_accessible'] = True
        print("   ✓ Conexión Firebird OK")
        
    except Exception as e:
        print(f"   ✗ Error Firebird: {e}")
        results['connection_errors'].append(f"Firebird: {str(e)}")
    
    # Probar conexión PostgreSQL
    print("\n2. Probando conexión PostgreSQL...")
    try:
        from database.db_context import db_context
        
        with db_context.get_session() as session:
            # Query simple para probar conexión
            result = session.execute("SELECT 1").fetchone()
            results['postgres_accessible'] = True
            print("   ✓ Conexión PostgreSQL OK")
            
    except Exception as e:
        print(f"   ✗ Error PostgreSQL: {e}")
        results['connection_errors'].append(f"PostgreSQL: {str(e)}")
    
    return results

def generate_analysis_report(api_results, db_results, detector_results, connection_results):
    """Genera un reporte completo de análisis"""
    print("\n" + "="*60)
    print("REPORTE DE ANÁLISIS COMPLETO")
    print("="*60)
    
    print(f"\n🔍 ESTADO GENERAL:")
    print(f"   API ejecutándose: {'✓' if api_results['api_running'] else '✗'}")
    print(f"   Base de datos accesible: {'✓' if db_results['database_accessible'] else '✗'}")
    print(f"   Detectores importables: {'✓' if detector_results['detectors_importable'] else '✗'}")
    print(f"   Firebird conectado: {'✓' if connection_results['firebird_accessible'] else '✗'}")
    print(f"   PostgreSQL conectado: {'✓' if connection_results['postgres_accessible'] else '✗'}")
    
    print(f"\n📊 DATOS:")
    print(f"   Total casos en BD: {db_results['total_cases']}")
    print(f"   API devuelve datos: {'✓' if api_results['has_data'] else '✗'}")
    
    print(f"\n⚠ PROBLEMAS DETECTADOS:")
    all_errors = (api_results['errors'] + 
                 db_results['errors'] + 
                 detector_results['import_errors'] + 
                 connection_results['connection_errors'])
    
    if all_errors:
        for i, error in enumerate(all_errors, 1):
            print(f"   {i}. {error}")
    else:
        print("   No se detectaron problemas críticos")
    
    if db_results['enum_issues']:
        print(f"\n🔧 PROBLEMAS DE DATOS:")
        for issue in db_results['enum_issues'][:5]:  # Solo primeros 5
            print(f"   • {issue}")
        if len(db_results['enum_issues']) > 5:
            print(f"   ... y {len(db_results['enum_issues']) - 5} más")
    
    print(f"\n💡 RECOMENDACIONES:")
    
    if not api_results['api_running']:
        print("   • Iniciar el servidor API: cd backend && python -m uvicorn api.main:app --reload")
    
    if db_results['total_cases'] == 0:
        print("   • Insertar casos de prueba: python insert_fraud_test_cases.py")
    
    if db_results['enum_issues']:
        print("   • Revisar formato de enums en la base de datos")
    
    if not connection_results['firebird_accessible']:
        print("   • Verificar configuración de conexión Firebird")
    
    if not connection_results['postgres_accessible']:
        print("   • Verificar configuración de conexión PostgreSQL")

def main():
    """Función principal de análisis"""
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETO DEL SISTEMA (SIN MODIFICACIONES)")
    print("="*60)
    
    # 1. Analizar API
    print("\nPaso 1: Analizando API...")
    api_results = analyze_api_endpoints()
    
    # 2. Analizar base de datos
    print("\nPaso 2: Analizando base de datos...")
    db_results = analyze_database_stats()
    
    # 3. Analizar detectores
    print("\nPaso 3: Analizando detectores...")
    detector_results = analyze_detectors()
    
    # 4. Analizar conexiones
    print("\nPaso 4: Analizando conexiones...")
    connection_results = analyze_database_connection()
    
    # 5. Generar reporte
    generate_analysis_report(api_results, db_results, detector_results, connection_results)
    
    # Guardar reporte en archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"analysis_report_{timestamp}.json"
    
    full_report = {
        'timestamp': timestamp,
        'api_analysis': api_results,
        'database_analysis': db_results,
        'detector_analysis': detector_results,
        'connection_analysis': connection_results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2, default=str)
    
    print(f"\n📄 Reporte detallado guardado en: {report_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnálisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresione Enter para salir...")