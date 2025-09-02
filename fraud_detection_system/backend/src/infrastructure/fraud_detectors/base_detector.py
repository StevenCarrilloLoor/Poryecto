# backend/src/infrastructure/fraud_detectors/base_detector.py

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.src.infrastructure.persistence.models import (
    DetectorType, FraudCase, FraudSeverity, FraudStatus
)

logger = logging.getLogger(__name__)


class DetectionResult:
    """Result of a fraud detection check."""
    
    def __init__(
        self,
        detected: bool,
        severity: FraudSeverity = None,
        confidence_score: float = 0.0,
        description: str = "",
        evidence: Dict[str, Any] = None,
        anomaly_details: Dict[str, Any] = None,
        related_transactions: List[str] = None
    ):
        self.detected = detected
        self.severity = severity or FraudSeverity.LOW
        self.confidence_score = confidence_score
        self.description = description
        self.evidence = evidence or {}
        self.anomaly_details = anomaly_details or {}
        self.related_transactions = related_transactions or []
        
    def to_fraud_case(self, detector_type: DetectorType) -> FraudCase:
        """Convert detection result to a FraudCase entity."""
        import json
        from uuid import uuid4
        
        return FraudCase(
            case_number=f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
            detector_type=detector_type,
            severity=self.severity,
            status=FraudStatus.PENDING,
            confidence_score=self.confidence_score,
            description=self.description,
            evidence_json=json.dumps(self.evidence),
            anomaly_details=json.dumps(self.anomaly_details),
            detection_date=datetime.now()
        )


class BaseDetector(ABC):
    """
    Abstract base class for all fraud detectors.
    Implements Strategy Pattern for detection algorithms.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.detector_type = self._get_detector_type()
        self._load_configuration()
        
    @abstractmethod
    def _get_detector_type(self) -> DetectorType:
        """Return the detector type."""
        pass
    
    @abstractmethod
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """
        Perform fraud detection on the provided data.
        Returns a DetectionResult indicating if fraud was detected.
        """
        pass
    
    def _load_configuration(self):
        """Load detector configuration from database."""
        from backend.src.infrastructure.persistence.db_context import get_db_context
        from backend.src.infrastructure.persistence.models import DetectorConfig
        
        try:
            db_context = get_db_context()
            with db_context.get_session() as session:
                configs = session.query(DetectorConfig).filter(
                    DetectorConfig.detector_type == self.detector_type,
                    DetectorConfig.is_active == True
                ).all()
                
                for config in configs:
                    self.config[config.parameter_name] = self._parse_config_value(
                        config.parameter_value,
                        config.data_type
                    )
                    
        except Exception as e:
            logger.warning(f"Could not load configuration for {self.detector_type}: {e}")
    
    def _parse_config_value(self, value: str, data_type: str) -> Any:
        """Parse configuration value based on its data type."""
        if data_type == "INTEGER":
            return int(value)
        elif data_type == "DECIMAL":
            return float(value)
        elif data_type == "BOOLEAN":
            return value.lower() in ('true', '1', 'yes')
        elif data_type == "JSON":
            import json
            return json.loads(value)
        else:
            return value
    
    def _calculate_severity(self, score: float) -> FraudSeverity:
        """Calculate fraud severity based on confidence score."""
        if score >= 80:
            return FraudSeverity.CRITICAL
        elif score >= 60:
            return FraudSeverity.HIGH
        elif score >= 40:
            return FraudSeverity.MEDIUM
        else:
            return FraudSeverity.LOW
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that required fields are present in the data.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present, False otherwise
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing required fields for {self.detector_type}: {missing_fields}")
            return False
        
        return True
    
    def log_detection(self, result: DetectionResult):
        """Log detection result for auditing."""
        if result.detected:
            logger.info(
                f"Fraud detected by {self.detector_type.value}: "
                f"Severity={result.severity.value}, "
                f"Confidence={result.confidence_score:.2f}%, "
                f"Description={result.description[:100]}..."
            )
        else:
            logger.debug(f"No fraud detected by {self.detector_type.value}")
    
    def enrich_with_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich detection data with additional context.
        Override in subclasses to add detector-specific context.
        
        Args:
            data: Original data dictionary
            
        Returns:
            Enriched data dictionary
        """
        enriched = data.copy()
        enriched['detection_timestamp'] = datetime.now().isoformat()
        enriched['detector_type'] = self.detector_type.value
        enriched['detector_version'] = '1.0.0'
        
        return enriched
    
    def should_skip_detection(self, data: Dict[str, Any]) -> bool:
        """
        Determine if detection should be skipped for this data.
        Override in subclasses for specific skip conditions.
        
        Args:
            data: Data to evaluate
            
        Returns:
            True if detection should be skipped, False otherwise
        """
        # Skip if explicitly marked
        if data.get('skip_detection', False):
            return True
        
        # Skip if from trusted source
        if data.get('trusted_source', False):
            return True
        
        # Skip if amount is below minimum threshold
        min_amount = self.config.get('min_detection_amount', 0)
        if 'amount' in data and data['amount'] < min_amount:
            return True
        
        return False
    
    def create_alert_message(self, result: DetectionResult) -> str:
        """
        Create an alert message for notifications.
        
        Args:
            result: Detection result
            
        Returns:
            Formatted alert message
        """
        severity_emoji = {
            FraudSeverity.LOW: "🟡",
            FraudSeverity.MEDIUM: "🟠",
            FraudSeverity.HIGH: "🔴",
            FraudSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(result.severity, "⚠️")
        
        message = (
            f"{emoji} ALERTA DE FRAUDE DETECTADO {emoji}\n"
            f"Tipo: {self.detector_type.value}\n"
            f"Severidad: {result.severity.value}\n"
            f"Confianza: {result.confidence_score:.1f}%\n"
            f"Descripción: {result.description}\n"
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return message
    
    def batch_detect(self, data_list: List[Dict[str, Any]]) -> List[DetectionResult]:
        """
        Perform batch detection on multiple data entries.
        
        Args:
            data_list: List of data dictionaries to analyze
            
        Returns:
            List of detection results
        """
        results = []
        
        for data in data_list:
            try:
                if not self.should_skip_detection(data):
                    result = self.detect(data)
                    self.log_detection(result)
                    results.append(result)
            except Exception as e:
                logger.error(f"Error in batch detection for {self.detector_type}: {e}")
                # Create error result
                error_result = DetectionResult(
                    detected=False,
                    description=f"Error during detection: {str(e)}"
                )
                results.append(error_result)
        
        return results