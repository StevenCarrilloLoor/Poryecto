"""
DbContext personalizado para el manejo de base de datos
backend/database/db_context.py
"""

import os
import json
import pyodbc
import firebird.driver as fdb
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

from models.fraud_models import Base, FraudCase, DetectorConfig, AuditLog

load_dotenv()

class FraudDetectionDbContext:
    """
    Contexto de base de datos personalizado para el sistema de detección de fraude.
    Maneja tanto SQL Server (para datos de fraude) como Firebird (para datos fuente).
    """
    
    def __init__(self):
        self.sql_server_engine = None
        self.SessionLocal = None
        self.firebird_connection = None
        self._initialize_sql_server()
        
    def _initialize_sql_server(self):
        """Inicializa la conexión a SQL Server"""
        try:
            # Construir cadena de conexión para SQL Server
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
            
            # Crear engine con pool de conexiones
            self.sql_server_engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=os.getenv('LOG_LEVEL', 'INFO') == 'DEBUG'
            )
            
            # Crear session factory
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.sql_server_engine
                )
            )
            
            # Crear tablas si no existen
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
        """Obtiene conexión a Firebird"""
        if not self.firebird_connection:
            try:
                dsn = os.getenv('FIREBIRD_DSN')
                self.firebird_connection = pyodbc.connect(dsn)
            except Exception as e:
                print(f"Error conectando a Firebird: {e}")
                raise
        return self.firebird_connection
    
    def execute_firebird_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Ejecuta query en Firebird y retorna resultados como lista de diccionarios"""
        conn = self.get_firebird_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        finally:
            cursor.close()
    
    # Métodos específicos para casos de fraude
    def get_fraud_cases(self, 
                       status: str = None, 
                       detector_type: str = None,
                       date_from: datetime = None,
                       date_to: datetime = None,
                       limit: int = 100) -> List[FraudCase]:
        """Obtiene casos de fraude con filtros"""
        with self.get_session() as session:
            query = session.query(FraudCase)
            
            if status:
                query = query.filter(FraudCase.status == status)
            if detector_type:
                query = query.filter(FraudCase.detector_type == detector_type)
            if date_from:
                query = query.filter(FraudCase.transaction_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.transaction_date <= date_to)
            
            return query.order_by(FraudCase.detection_date.desc()).limit(limit).all()
    
    def create_fraud_case(self, fraud_data: Dict[str, Any]) -> FraudCase:
        """Crea un nuevo caso de fraude"""
        with self.get_session() as session:
            # Generar número de caso único
            import uuid
            fraud_data['case_number'] = f"FRAUD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            fraud_case = FraudCase(**fraud_data)
            session.add(fraud_case)
            session.commit()
            session.refresh(fraud_case)
            
            # Registrar en auditoría
            self.log_audit(
                action="CREATE_FRAUD_CASE",
                entity_type="FraudCase",
                entity_id=str(fraud_case.id),
                new_values=json.dumps(fraud_data, default=str),
                user="SYSTEM"
            )
            
            return fraud_case
    
    def update_fraud_case_status(self, case_id: int, new_status: str, user: str, notes: str = None) -> bool:
        """Actualiza el estado de un caso de fraude"""
        with self.get_session() as session:
            fraud_case = session.query(FraudCase).filter(FraudCase.id == case_id).first()
            
            if not fraud_case:
                return False
            
            old_status = fraud_case.status
            fraud_case.status = new_status
            fraud_case.updated_by = user
            fraud_case.updated_at = datetime.utcnow()
            
            # Log audit
            self.log_audit(
                action="UPDATE_STATUS",
                entity_type="FraudCase",
                entity_id=str(case_id),
                old_values=json.dumps({"status": old_status}),
                new_values=json.dumps({"status": new_status, "notes": notes}),
                user=user,
                fraud_case_id=case_id
            )
            
            session.commit()
            return True
    
    def get_detector_configs(self, enabled_only: bool = True) -> List[DetectorConfig]:
        """Obtiene configuraciones de detectores"""
        with self.get_session() as session:
            query = session.query(DetectorConfig)
            if enabled_only:
                query = query.filter(DetectorConfig.enabled == True)
            return query.all()
    
    def log_audit(self, action: str, entity_type: str, entity_id: str, 
                  old_values: str = None, new_values: str = None, 
                  user: str = "SYSTEM", fraud_case_id: int = None):
        """Registra una entrada en el log de auditoría"""
        with self.get_session() as session:
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
    
    def get_fraud_statistics(self, date_from: datetime = None, date_to: datetime = None) -> Dict:
        """Obtiene estadísticas de casos de fraude"""
        with self.get_session() as session:
            query = session.query(FraudCase)
            
            if date_from:
                query = query.filter(FraudCase.detection_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.detection_date <= date_to)
            
            cases = query.all()
            
            return {
                "total_cases": len(cases),
                "pending": len([c for c in cases if c.status.value == "PENDIENTE"]),
                "confirmed": len([c for c in cases if c.status.value == "CONFIRMADO"]),
                "rejected": len([c for c in cases if c.status.value == "RECHAZADO"]),
                "total_amount": sum([c.amount or 0 for c in cases]),
                "by_severity": {
                    "CRITICO": len([c for c in cases if c.severity.value == "CRITICO"]),
                    "ALTO": len([c for c in cases if c.severity.value == "ALTO"]),
                    "MEDIO": len([c for c in cases if c.severity.value == "MEDIO"]),
                    "BAJO": len([c for c in cases if c.severity.value == "BAJO"])
                }
            }
    
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