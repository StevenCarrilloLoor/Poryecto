# backend/src/infrastructure/fraud_detectors/invoice_anomaly_detector.py

import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List

from backend.src.infrastructure.fraud_detectors.base_detector import (
    BaseDetector, DetectionResult
)
from backend.src.infrastructure.persistence.models import DetectorType, FraudSeverity

logger = logging.getLogger(__name__)


class InvoiceAnomalyDetector(BaseDetector):
    """
    Detector for invoice-related fraud patterns:
    - Round amounts that repeat suspiciously
    - Missing sequences in invoice numbers
    - Transactions outside business hours
    - Duplicate invoices with different prices
    - Excessive discounts
    """
    
    def _get_detector_type(self) -> DetectorType:
        return DetectorType.INVOICE_ANOMALY
    
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """Analyze invoice data for anomalies."""
        anomalies = []
        evidence = {}
        confidence_score = 0.0
        
        # Check round amounts
        if self._check_round_amounts(data):
            anomalies.append("round_amounts")
            evidence["round_amount"] = data.get("total_amount")
            confidence_score += 20
            
        # Check invoice sequence
        if self._check_missing_sequence(data):
            anomalies.append("missing_sequence")
            evidence["sequence_gap"] = data.get("sequence_gap")
            confidence_score += 30
            
        # Check business hours
        if self._check_outside_hours(data):
            anomalies.append("outside_hours")
            evidence["transaction_time"] = str(data.get("transaction_date"))
            confidence_score += 25
            
        # Check for duplicates
        if self._check_duplicates(data):
            anomalies.append("duplicate_invoice")
            evidence["duplicate_info"] = data.get("duplicate_info")
            confidence_score += 35
            
        # Check excessive discounts
        if self._check_excessive_discount(data):
            anomalies.append("excessive_discount")
            evidence["discount_percent"] = data.get("discount_percent")
            confidence_score += 25
            
        # Determine if fraud is detected
        detected = len(anomalies) > 0
        
        # Calculate severity
        severity = self._calculate_severity_from_anomalies(anomalies, confidence_score)
        
        # Create description
        description = self._create_description(anomalies, data)
        
        return DetectionResult(
            detected=detected,
            severity=severity,
            confidence_score=min(confidence_score, 100),
            description=description,
            evidence=evidence,
            anomaly_details={"detected_anomalies": anomalies},
            related_transactions=data.get("related_transactions", [])
        )
    
    def _check_round_amounts(self, data: Dict[str, Any]) -> bool:
        """Check if amount is suspiciously round."""
        amount = data.get("total_amount", 0)
        threshold = self.config.get("round_amount_threshold", 100)
        
        if amount <= 0:
            return False
            
        # Check if amount is exactly divisible by threshold
        if amount >= threshold and amount % threshold == 0:
            # Check if this pattern repeats
            recent_amounts = data.get("recent_amounts", [])
            round_count = sum(1 for a in recent_amounts if a % threshold == 0)
            
            return round_count >= 3  # Suspicious if 3+ round amounts
            
        return False
    
    def _check_missing_sequence(self, data: Dict[str, Any]) -> bool:
        """Check for missing sequences in invoice numbers."""
        invoice_numbers = data.get("invoice_sequence", [])
        
        if len(invoice_numbers) < 2:
            return False
            
        # Try to parse as integers
        try:
            numbers = sorted([int(n) for n in invoice_numbers if n.isdigit()])
            
            if len(numbers) < 2:
                return False
                
            # Check for gaps
            expected_count = numbers[-1] - numbers[0] + 1
            actual_count = len(numbers)
            gap_threshold = self.config.get("sequence_gap_threshold", 5)
            
            missing_count = expected_count - actual_count
            
            if missing_count > gap_threshold:
                data["sequence_gap"] = missing_count
                return True
                
        except (ValueError, TypeError):
            pass
            
        return False
    
    def _check_outside_hours(self, data: Dict[str, Any]) -> bool:
        """Check if transaction occurred outside business hours."""
        transaction_date = data.get("transaction_date")
        
        if not transaction_date:
            return False
            
        if isinstance(transaction_date, str):
            try:
                transaction_date = datetime.fromisoformat(transaction_date)
            except:
                return False
                
        # Get configured hours
        start_hour = self.config.get("business_start_hour", 6)
        end_hour = self.config.get("business_end_hour", 22)
        
        hour = transaction_date.hour
        
        # Check if outside business hours
        if hour < start_hour or hour >= end_hour:
            # Check if it's a weekend
            if transaction_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return True
                
            # Weekday but outside hours
            return True
            
        return False
    
    def _check_duplicates(self, data: Dict[str, Any]) -> bool:
        """Check for duplicate invoices with different prices."""
        duplicates = data.get("potential_duplicates", [])
        
        if not duplicates:
            return False
            
        # Check for same client, similar date, different amounts
        for dup in duplicates:
            amount_diff = abs(dup.get("amount_difference", 0))
            date_diff = dup.get("date_difference_days", 0)
            
            # Same client, within 7 days, different amount
            if date_diff <= 7 and amount_diff > 0:
                data["duplicate_info"] = {
                    "original_amount": dup.get("original_amount"),
                    "duplicate_amount": dup.get("duplicate_amount"),
                    "date_difference": date_diff
                }
                return True
                
        return False
    
    def _check_excessive_discount(self, data: Dict[str, Any]) -> bool:
        """Check for excessive discounts."""
        original_amount = data.get("original_amount", 0)
        discount_amount = data.get("discount_amount", 0)
        
        if original_amount <= 0:
            return False
            
        discount_percent = (discount_amount / original_amount) * 100
        max_discount = self.config.get("max_discount_percent", 30)
        
        if discount_percent > max_discount:
            data["discount_percent"] = discount_percent
            return True
            
        return False
    
    def _calculate_severity_from_anomalies(
        self,
        anomalies: List[str],
        confidence_score: float
    ) -> FraudSeverity:
        """Calculate severity based on detected anomalies."""
        critical_anomalies = ["duplicate_invoice", "missing_sequence"]
        high_anomalies = ["excessive_discount", "outside_hours"]
        
        # Check for critical patterns
        if any(a in critical_anomalies for a in anomalies):
            if confidence_score >= 70:
                return FraudSeverity.CRITICAL
            return FraudSeverity.HIGH
            
        # Check for high severity patterns
        if any(a in high_anomalies for a in anomalies):
            if confidence_score >= 60:
                return FraudSeverity.HIGH
            return FraudSeverity.MEDIUM
            
        # Default based on confidence
        if confidence_score >= 50:
            return FraudSeverity.MEDIUM
            
        return FraudSeverity.LOW
    
    def _create_description(self, anomalies: List[str], data: Dict[str, Any]) -> str:
        """Create human-readable description of detected anomalies."""
        descriptions = []
        
        if "round_amounts" in anomalies:
            descriptions.append(f"Monto sospechosamente redondo: ${data.get('total_amount', 0):.2f}")
            
        if "missing_sequence" in anomalies:
            gap = data.get("sequence_gap", 0)
            descriptions.append(f"Secuencia de facturas con {gap} números faltantes")
            
        if "outside_hours" in anomalies:
            descriptions.append(f"Transacción fuera de horario laboral")
            
        if "duplicate_invoice" in anomalies:
            descriptions.append(f"Posible factura duplicada con montos diferentes")
            
        if "excessive_discount" in anomalies:
            discount = data.get("discount_percent", 0)
            descriptions.append(f"Descuento excesivo del {discount:.1f}%")
            
        if descriptions:
            return "Anomalías detectadas: " + "; ".join(descriptions)
            
        return "No se detectaron anomalías significativas"