# backend/src/infrastructure/persistence/models.py

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Decimal as SQLDecimal,
    Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class FraudSeverity(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudStatus(PyEnum):
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    RESOLVED = "RESOLVED"


class DetectorType(PyEnum):
    INVOICE_ANOMALY = "INVOICE_ANOMALY"
    FUEL_THEFT = "FUEL_THEFT"
    DATA_MANIPULATION = "DATA_MANIPULATION"
    QUOTA_ABUSE = "QUOTA_ABUSE"
    LIQUIDATION_FRAUD = "LIQUIDATION_FRAUD"
    TRANSACTION_PATTERN = "TRANSACTION_PATTERN"
    NIGHT_OPERATION = "NIGHT_OPERATION"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    fraud_confirmations = relationship("FraudConfirmation", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class FraudCase(Base):
    __tablename__ = "fraud_cases"
    __table_args__ = (
        Index('idx_fraud_cases_date', 'detection_date'),
        Index('idx_fraud_cases_status', 'status'),
        Index('idx_fraud_cases_severity', 'severity'),
        Index('idx_fraud_cases_client', 'client_code'),
    )
    
    id = Column(BigInteger, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False)
    detector_type = Column(Enum(DetectorType), nullable=False)
    severity = Column(Enum(FraudSeverity), nullable=False)
    status = Column(Enum(FraudStatus), default=FraudStatus.PENDING)
    
    # Detection details
    detection_date = Column(DateTime(timezone=True), server_default=func.now())
    detection_rule = Column(String(200))
    confidence_score = Column(SQLDecimal(5, 2))  # 0.00 to 100.00
    
    # Entity references (from Firebird)
    document_id = Column(String(50))
    document_type = Column(String(10))
    client_code = Column(String(20), index=True)
    client_name = Column(String(200))
    vendor_code = Column(String(20))
    
    # Financial impact
    amount_involved = Column(SQLDecimal(15, 2))
    currency = Column(String(3), default='USD')
    potential_loss = Column(SQLDecimal(15, 2))
    recovered_amount = Column(SQLDecimal(15, 2))
    
    # Evidence and details
    description = Column(Text)
    evidence_json = Column(Text)  # JSON string with evidence details
    anomaly_details = Column(Text)  # JSON string with specific anomalies
    
    # Investigation
    investigation_notes = Column(Text)
    resolution_date = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    confirmations = relationship("FraudConfirmation", back_populates="fraud_case")
    related_transactions = relationship("RelatedTransaction", back_populates="fraud_case")
    audit_logs = relationship("AuditLog", back_populates="fraud_case")


class FraudConfirmation(Base):
    __tablename__ = "fraud_confirmations"
    __table_args__ = (
        UniqueConstraint('fraud_case_id', 'user_id', name='uq_fraud_user'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    decision = Column(String(50), nullable=False)  # CONFIRM, REJECT, ESCALATE
    confidence_level = Column(SQLDecimal(5, 2))
    comments = Column(Text)
    action_taken = Column(String(200))
    
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fraud_case = relationship("FraudCase", back_populates="confirmations")
    user = relationship("User", back_populates="fraud_confirmations")


class DetectorConfig(Base):
    __tablename__ = "detector_configs"
    __table_args__ = (
        UniqueConstraint('detector_type', 'parameter_name', name='uq_detector_param'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    detector_type = Column(Enum(DetectorType), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(String(500))
    data_type = Column(String(20))  # INTEGER, DECIMAL, STRING, BOOLEAN, JSON
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    min_value = Column(String(100))
    max_value = Column(String(100))
    default_value = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(50))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_date', 'action_date'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"))
    
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, EXPORT
    entity_type = Column(String(50))
    entity_id = Column(String(50))
    
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(100))
    
    action_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    fraud_case = relationship("FraudCase", back_populates="audit_logs")


class FraudMetrics(Base):
    __tablename__ = "fraud_metrics"
    __table_args__ = (
        Index('idx_metrics_date', 'metric_date'),
        UniqueConstraint('metric_date', 'metric_type', 'dimension', name='uq_metric'),
    )
    
    id = Column(BigInteger, primary_key=True, index=True)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    metric_type = Column(String(50), nullable=False)  # DAILY_CASES, SEVERITY_DIST, etc.
    dimension = Column(String(100))  # Additional grouping dimension
    
    # Metrics
    count_value = Column(Integer, default=0)
    sum_value = Column(SQLDecimal(15, 2))
    avg_value = Column(SQLDecimal(15, 4))
    min_value = Column(SQLDecimal(15, 2))
    max_value = Column(SQLDecimal(15, 2))
    
    # Additional stats
    confirmed_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RelatedTransaction(Base):
    __tablename__ = "related_transactions"
    __table_args__ = (
        Index('idx_related_fraud', 'fraud_case_id'),
    )
    
    id = Column(BigInteger, primary_key=True, index=True)
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"), nullable=False)
    
    # Transaction details from Firebird
    transaction_id = Column(String(50))
    transaction_type = Column(String(20))
    transaction_date = Column(DateTime(timezone=True))
    amount = Column(SQLDecimal(15, 2))
    
    # Additional context
    relevance_score = Column(SQLDecimal(5, 2))
    relationship_type = Column(String(50))  # PRIMARY, RELATED, PATTERN_MATCH
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fraud_case = relationship("FraudCase", back_populates="related_transactions")


class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    detector_type = Column(Enum(DetectorType))
    severity_threshold = Column(Enum(FraudSeverity))
    
    # Alert channels
    email_enabled = Column(Boolean, default=False)
    email_recipients = Column(Text)  # JSON array
    sms_enabled = Column(Boolean, default=False)
    sms_recipients = Column(Text)  # JSON array
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500))
    
    # Alert conditions
    min_confidence_score = Column(SQLDecimal(5, 2), default=50.0)
    cooldown_minutes = Column(Integer, default=60)  # Avoid alert spam
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    fraud_case_id = Column(BigInteger, ForeignKey("fraud_cases.id"))
    alert_config_id = Column(Integer, ForeignKey("alert_configurations.id"))
    
    notification_type = Column(String(20))  # EMAIL, SMS, WEBHOOK
    recipient = Column(String(200))
    status = Column(String(20))  # SENT, FAILED, PENDING
    error_message = Column(Text)
    
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())