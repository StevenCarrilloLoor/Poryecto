"""
DbContext FINAL COMPLETO - backend/database/db_context.py
"""

import os
import json
import pyodbc
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

from models.fraud_models import Base, FraudCase, DetectorConfig, AuditLog, FraudStatus

load_dotenv()

class FraudDetectionDbContext:
    """
    Contexto de base de datos personalizado para el sistema de detección de fraude.
    """
    
    def __init__(self):
        self.sql_server_engine = None
        self.SessionLocal = None
        self.firebird_connection = None
        self._initialize_sql_server()
        
    def _initialize_sql_server(self):
        """Inicializa la conexión a SQL Server"""
        try:
            server = os.getenv('DB_SERVER', 'STEVEN-ALIENWAR\\SQLTRABAJO')
            database = os.getenv('DB_DATABASE', 'FraudDetectionDB')
            
            if os.getenv('DB_TRUSTED_CONNECTION', 'yes').lower() == 'yes':
                connection_string = (
                    f"mssql+pyodbc://@{server}/{database}"
                    f"?driver=ODBC+Driver+17+for+SQL+Server"
                    f"&trusted_connection=yes"
                )
            else:
                username = os.getenv('DB_USERNAME', 'sa')
                password = os.getenv('DB_PASSWORD', '')
                connection_string = (
                    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
                    f"?driver=ODBC+Driver+17+for+SQL+Server"
                )
            
            self.sql_server_engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False  # Cambiar a False para menos logs
            )
            
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.sql_server_engine,
                    expire_on_commit=False  # IMPORTANTE: No expirar objetos después del commit
                )
            )
            
            self.create_tables()
            
        except Exception as e:
            print(f"Error inicializando SQL Server: {e}")
            raise
    
    def create_tables(self):
        """Crea todas las tablas en SQL Server si no existen"""
        try:
            Base.metadata.create_all(bind=self.sql_server_engine)
            print("✓ Tablas de SQL Server verificadas/creadas")
        except Exception as e:
            print(f"Error creando tablas: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager para sesiones de SQL Server"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_firebird_connection(self):
        """Obtiene conexión a Firebird con manejo de reconexión"""
        try:
            if self.firebird_connection:
                cursor = self.firebird_connection.cursor()
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                cursor.close()
                return self.firebird_connection
        except:
            if self.firebird_connection:
                try:
                    self.firebird_connection.close()
                except:
                    pass
                self.firebird_connection = None
        
        try:
            dsn = os.getenv('FIREBIRD_DSN')
            self.firebird_connection = pyodbc.connect(dsn, timeout=10)
            return self.firebird_connection
        except Exception as e:
            print(f"Error conectando a Firebird: {e}")
            raise
    
    def execute_firebird_query(self, query: str, params: tuple = None, fetch_size: int = 1000) -> List[Dict]:
        """Ejecuta query en Firebird con límite de resultados"""
        conn = self.get_firebird_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            row_count = 0
            while row_count < fetch_size:
                row = cursor.fetchone()
                if not row:
                    break
                results.append(dict(zip(columns, row)))
                row_count += 1
            
            return results
            
        finally:
            cursor.close()
    
    def _fraud_case_to_dict(self, case: FraudCase) -> Dict:
        """Convierte un FraudCase a diccionario con todos los campos"""
        return {
            'id': case.id,
            'case_number': case.case_number,
            'detector_type': case.detector_type.value if case.detector_type else None,
            'severity': case.severity.value if case.severity else None,
            'status': case.status.value if case.status else 'PENDIENTE',
            'title': case.title,
            'description': case.description,
            'amount': float(case.amount) if case.amount else None,
            'source_table': case.source_table,
            'source_record_id': case.source_record_id,
            'transaction_date': case.transaction_date,
            'client_code': case.client_code,
            'client_name': case.client_name,
            'client_ruc': case.client_ruc,
            'detection_date': case.detection_date,
            'detection_rules': case.detection_rules,
            'confidence_score': float(case.confidence_score) if case.confidence_score else None,
            'created_at': case.created_at,
            'updated_at': case.updated_at,
            'created_by': case.created_by,
            'updated_by': case.updated_by
        }
    
    def get_fraud_cases(self, 
                       status: str = None, 
                       detector_type: str = None,
                       date_from: datetime = None,
                       date_to: datetime = None,
                       limit: int = 100) -> List[Dict]:
        """Obtiene casos de fraude y los devuelve como diccionarios"""
        session = self.SessionLocal()
        try:
            query = session.query(FraudCase)
            
            if status:
                query = query.filter(FraudCase.status == status)
            if detector_type:
                query = query.filter(FraudCase.detector_type == detector_type)
            if date_from:
                query = query.filter(FraudCase.transaction_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.transaction_date <= date_to)
            
            cases = query.order_by(FraudCase.detection_date.desc()).limit(limit).all()
            
            # Convertir a diccionarios antes de cerrar la sesión
            result = [self._fraud_case_to_dict(case) for case in cases]
            
            return result
            
        finally:
            session.close()
    
    def create_fraud_case(self, fraud_data: Dict[str, Any]) -> Dict:
        """Crea un nuevo caso de fraude y retorna un diccionario"""
        session = self.SessionLocal()
        try:
            # Generar número de caso único
            import uuid
            fraud_data['case_number'] = f"FRAUD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Asegurar que status tenga un valor por defecto
            if 'status' not in fraud_data or fraud_data['status'] is None:
                fraud_data['status'] = FraudStatus.PENDING
            
            # Crear instancia del caso
            fraud_case = FraudCase(**fraud_data)
            
            # Agregar y hacer commit
            session.add(fraud_case)
            session.commit()
            
            # Hacer refresh para obtener el ID
            session.refresh(fraud_case)
            
            # Convertir a diccionario ANTES de cerrar la sesión
            case_dict = self._fraud_case_to_dict(fraud_case)
            
            # Log de auditoría
            audit_log = AuditLog(
                action="CREATE_FRAUD_CASE",
                entity_type="FraudCase",
                entity_id=str(fraud_case.id),
                new_values=json.dumps(fraud_data, default=str),
                user="SYSTEM",
                fraud_case_id=fraud_case.id,
                timestamp=datetime.utcnow()
            )
            session.add(audit_log)
            session.commit()
            
            # Crear objeto simple para compatibilidad
            class FraudCaseResult:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
            
            return FraudCaseResult(case_dict)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_fraud_case_status(self, case_id: int, new_status: str, user: str, notes: str = None) -> bool:
        """Actualiza el estado de un caso de fraude"""
        session = self.SessionLocal()
        try:
            fraud_case = session.query(FraudCase).filter(FraudCase.id == case_id).first()
            
            if not fraud_case:
                return False
            
            # Obtener el valor string del status anterior
            old_status_value = fraud_case.status.value if fraud_case.status else 'PENDIENTE'
            
            # Convertir el nuevo status a enum si viene como string
            if isinstance(new_status, str):
                # Buscar el enum correspondiente
                for status in FraudStatus:
                    if status.value == new_status:
                        fraud_case.status = status
                        break
            else:
                fraud_case.status = new_status
            
            fraud_case.updated_by = user
            fraud_case.updated_at = datetime.utcnow()
            
            # Log audit con valores string (NO con el enum directamente)
            audit_log = AuditLog(
                action="UPDATE_STATUS",
                entity_type="FraudCase",
                entity_id=str(case_id),
                old_values=json.dumps({"status": old_status_value}),  # Usar el valor string
                new_values=json.dumps({
                    "status": new_status if isinstance(new_status, str) else new_status.value, 
                    "notes": notes
                }),
                user=user,
                fraud_case_id=case_id,
                timestamp=datetime.utcnow()
            )
            session.add(audit_log)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error actualizando estado: {e}")
            raise e
        finally:
            session.close()
    
    def get_detector_configs(self, enabled_only: bool = True) -> List[DetectorConfig]:
        """Obtiene configuraciones de detectores"""
        session = self.SessionLocal()
        try:
            query = session.query(DetectorConfig)
            if enabled_only:
                query = query.filter(DetectorConfig.enabled == True)
            configs = query.all()
            
            # Hacer una copia de los datos antes de cerrar la sesión
            result = []
            for config in configs:
                result.append(config)
            
            return result
            
        finally:
            session.close()
    
    def log_audit(self, action: str, entity_type: str, entity_id: str, 
                  old_values: str = None, new_values: str = None, 
                  user: str = "SYSTEM", fraud_case_id: int = None):
        """Registra una entrada en el log de auditoría"""
        session = self.SessionLocal()
        try:
            audit_log = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                user=user,
                fraud_case_id=fraud_case_id,
                timestamp=datetime.utcnow()
            )
            session.add(audit_log)
            session.commit()
        finally:
            session.close()
    
    def get_fraud_statistics(self, date_from: datetime = None, date_to: datetime = None) -> Dict:
        """Obtiene estadísticas de casos de fraude"""
        session = self.SessionLocal()
        try:
            query = session.query(FraudCase)
            
            if date_from:
                query = query.filter(FraudCase.detection_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.detection_date <= date_to)
            
            cases = query.all()
            
            def safe_enum_value(obj, attr):
                val = getattr(obj, attr, None)
                if val and hasattr(val, 'value'):
                    return val.value
                return None
            
            stats = {
                "total_cases": len(cases),
                "pending": len([c for c in cases if safe_enum_value(c, 'status') == "PENDIENTE"]),
                "confirmed": len([c for c in cases if safe_enum_value(c, 'status') == "CONFIRMADO"]),
                "rejected": len([c for c in cases if safe_enum_value(c, 'status') == "RECHAZADO"]),
                "total_amount": sum([float(c.amount) if c.amount else 0 for c in cases]),
                "by_severity": {
                    "CRITICO": len([c for c in cases if safe_enum_value(c, 'severity') == "CRITICO"]),
                    "ALTO": len([c for c in cases if safe_enum_value(c, 'severity') == "ALTO"]),
                    "MEDIO": len([c for c in cases if safe_enum_value(c, 'severity') == "MEDIO"]),
                    "BAJO": len([c for c in cases if safe_enum_value(c, 'severity') == "BAJO"])
                }
            }
            
            return stats
            
        finally:
            session.close()
    
    def close(self):
        """Cierra todas las conexiones"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.sql_server_engine:
            self.sql_server_engine.dispose()
        if self.firebird_connection:
            self.firebird_connection.close()

# Instancia global del contexto
db_context = FraudDetectionDbContext()