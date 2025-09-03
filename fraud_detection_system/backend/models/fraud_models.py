"""
Modelos SQLAlchemy para el Sistema de Detección de Fraude
backend/models/fraud_models.py
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, BigInteger, String, DateTime, Numeric, Integer, 
    Boolean, Text, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class FraudStatus(enum.Enum):
    """Estados posibles de un caso de fraude"""
    PENDING = "PENDIENTE"
    CONFIRMED = "CONFIRMADO"
    REJECTED = "RECHAZADO"
    INVESTIGATING = "INVESTIGANDO"
    RESOLVED = "RESUELTO"

class FraudSeverity(enum.Enum):
    """Niveles de severidad del fraude"""
    LOW = "BAJO"
    MEDIUM = "MEDIO"
    HIGH = "ALTO"
    CRITICAL = "CRITICO"

class DetectorType(enum.Enum):
    """Tipos de detectores disponibles"""
    INVOICE_ANOMALY = "ANOMALIA_FACTURA"
    FUEL_THEFT = "ROBO_COMBUSTIBLE"
    DATA_MANIPULATION = "MANIPULACION_DATOS"
    DUPLICATE_TRANSACTION = "TRANSACCION_DUPLICADA"
    EXCESSIVE_DISCOUNT = "DESCUENTO_EXCESIVO"
    AFTERHOURS = "FUERA_HORARIO"
    ROUND_AMOUNT = "MONTO_REDONDO"
    SEQUENCE_GAP = "SECUENCIA_FALTANTE"

class FraudCase(Base):
    """Modelo principal para casos de fraude detectados"""
    __tablename__ = "fraud_cases"
    
    id = Column(BigInteger, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False)
    detector_type = Column(SQLEnum(DetectorType), nullable=False, index=True)
    severity = Column(SQLEnum(FraudSeverity), nullable=False, index=True)
    status = Column(SQLEnum(FraudStatus), default=FraudStatus.PENDING, nullable=False, index=True)
    
    # Información del fraude
    title = Column(String(200), nullable=False)
    description = Column(Text)
    amount = Column(Numeric(15, 2))
    
    # Referencias a datos originales de Firebird
    source_table = Column(String(50))
    source_record_id = Column(String(100))
    transaction_date = Column(DateTime)
    
    # Datos del cliente/entidad involucrada
    client_code = Column(String(20), index=True)
    client_name = Column(String(200))
    client_ruc = Column(String(20))
    
    # Datos de detección
    detection_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    detection_rules = Column(Text)  # JSON con las reglas que se activaron
    confidence_score = Column(Numeric(5, 2))  # 0-100%
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    updated_by = Column(String(50))
    
    # Relaciones
    confirmations = relationship("FraudConfirmation", back_populates="fraud_case")
    audit_logs = relationship("AuditLog", back_populates="fraud_case")
    
    # Índices compuestos
    __table_args__ = (
        Index('idx_fraud_date_status', 'transaction_date', 'status'),
        Index('idx_fraud_client_date', 'client_code', 'transaction_date'),
        Index('idx_fraud_detector_severity', 'detector_type', 'severity'),
    )

class FraudConfirmation(Base):
    """Registro de confirmaciones y decisiones sobre casos de fraude"""
    __tablename__ = "fraud_confirmations"
    
    id = Column(BigInteger, primary_key=True, index=True)
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"), nullable=False)
    
    decision = Column(SQLEnum(FraudStatus), nullable=False)
    decision_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    decision_by = Column(String(50), nullable=False)
    
    notes = Column(Text)
    evidence = Column(Text)  # JSON con URLs o referencias a evidencia
    
    # Relación con FraudCase
    fraud_case = relationship("FraudCase", back_populates="confirmations")

class DetectorConfig(Base):
    """Configuración de los detectores de fraude"""
    __tablename__ = "detector_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    detector_type = Column(SQLEnum(DetectorType), unique=True, nullable=False)
    
    enabled = Column(Boolean, default=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Configuración específica del detector (JSON)
    config_json = Column(Text, nullable=False, default='{}')
    
    # Umbrales
    threshold_low = Column(Numeric(10, 2))
    threshold_medium = Column(Numeric(10, 2))
    threshold_high = Column(Numeric(10, 2))
    
    # Control de ejecución
    last_run = Column(DateTime)
    run_frequency_minutes = Column(Integer, default=60)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    """Log de auditoría completo del sistema"""
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Referencia opcional a caso de fraude
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"), nullable=True)
    
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100))
    
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    
    user = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relación con FraudCase
    fraud_case = relationship("FraudCase", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_timestamp_user', 'timestamp', 'user'),
    )

class FraudMetrics(Base):
    """Métricas y KPIs del sistema de detección"""
    __tablename__ = "fraud_metrics"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    metric_date = Column(DateTime, nullable=False, index=True)
    detector_type = Column(SQLEnum(DetectorType), nullable=False, index=True)
    
    # Contadores
    cases_detected = Column(Integer, default=0)
    cases_confirmed = Column(Integer, default=0)
    cases_rejected = Column(Integer, default=0)
    
    # Valores
    total_amount = Column(Numeric(15, 2), default=0)
    recovered_amount = Column(Numeric(15, 2), default=0)
    
    # Performance
    detection_time_ms = Column(Integer)
    false_positive_rate = Column(Numeric(5, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_metrics_date_detector', 'metric_date', 'detector_type'),
    )