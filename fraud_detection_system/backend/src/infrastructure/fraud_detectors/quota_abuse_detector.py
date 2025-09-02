# backend/src/infrastructure/fraud_detectors/quota_abuse_detector.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from backend.src.infrastructure.fraud_detectors.base_detector import (
    BaseDetector, DetectionResult
)
from backend.src.infrastructure.persistence.models import DetectorType, FraudSeverity

logger = logging.getLogger(__name__)


class QuotaAbuseDetector(BaseDetector):
    """
    Detector for quota and limit abuse patterns:
    - Exceeding assigned quotas
    - Rapid quota consumption
    - Multiple quota requests
    - Quota manipulation attempts
    - Suspicious quota increases
    """
    
    def _get_detector_type(self) -> DetectorType:
        return DetectorType.QUOTA_ABUSE
    
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """Analyze quota usage for abuse patterns."""
        anomalies = []
        evidence = {}
        confidence_score = 0.0
        
        # Check quota exceeded
        if self._check_quota_exceeded(data):
            anomalies.append("quota_exceeded")
            evidence["quota_violation"] = data.get("quota_info")
            confidence_score += 40
            
        # Check rapid consumption
        if self._check_rapid_consumption(data):
            anomalies.append("rapid_consumption")
            evidence["consumption_rate"] = data.get("consumption_details")
            confidence_score += 30
            
        # Check multiple requests
        if self._check_multiple_requests(data):
            anomalies.append("multiple_requests")
            evidence["request_pattern"] = data.get("request_info")
            confidence_score += 25
            
        # Check suspicious increases
        if self._check_suspicious_increases(data):
            anomalies.append("suspicious_increase")
            evidence["increase_details"] = data.get("increase_info")
            confidence_score += 35
            
        # Check near-limit patterns
        if self._check_near_limit_pattern(data):
            anomalies.append("near_limit_pattern")
            evidence["limit_pattern"] = data.get("limit_usage")
            confidence_score += 20
            
        detected = len(anomalies) > 0
        severity = self._calculate_quota_severity(anomalies, confidence_score, data)
        description = self._create_quota_description(anomalies, data)
        
        return DetectionResult(
            detected=detected,
            severity=severity,
            confidence_score=min(confidence_score, 100),
            description=description,
            evidence=evidence,
            anomaly_details={"quota_anomalies": anomalies},
            related_transactions=data.get("related_transactions", [])
        )
    
    def _check_quota_exceeded(self, data: Dict[str, Any]) -> bool:
        """Check if quota has been exceeded."""
        current_usage = data.get("current_usage", 0)
        quota_limit = data.get("quota_limit", 0)
        
        if quota_limit <= 0:
            return False
            
        # Check if over limit
        if current_usage > quota_limit:
            tolerance = self.config.get("quota_tolerance_percent", 5) / 100
            excess_percent = ((current_usage - quota_limit) / quota_limit)
            
            if excess_percent > tolerance:
                data["quota_info"] = {
                    "current_usage": current_usage,
                    "quota_limit": quota_limit,
                    "excess_percent": excess_percent * 100,
                    "exceeded_by": current_usage - quota_limit
                }
                return True
                
        return False
    
    def _check_rapid_consumption(self, data: Dict[str, Any]) -> bool:
        """Check for unusually rapid quota consumption."""
        consumption_history = data.get("consumption_history", [])
        
        if len(consumption_history) < 2:
            return False
            
        # Calculate consumption rate
        time_window_hours = self.config.get("rapid_consumption_hours", 24)
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        recent_consumption = []
        for record in consumption_history:
            try:
                timestamp = self._parse_date(record.get("timestamp"))
                if timestamp > cutoff_time:
                    recent_consumption.append(record.get("amount", 0))
            except:
                continue
                
        if not recent_consumption:
            return False
            
        # Check if consumption rate is suspicious
        total_consumed = sum(recent_consumption)
        quota_limit = data.get("quota_limit", 0)
        
        if quota_limit > 0:
            consumption_rate = (total_consumed / quota_limit) * 100
            max_rate = self.config.get("max_consumption_rate_percent", 50)
            
            if consumption_rate > max_rate:
                data["consumption_details"] = {
                    "consumed_amount": total_consumed,
                    "time_window_hours": time_window_hours,
                    "consumption_rate": consumption_rate,
                    "transaction_count": len(recent_consumption)
                }
                return True
                
        return False
    
    def _check_multiple_requests(self, data: Dict[str, Any]) -> bool:
        """Check for multiple quota increase requests."""
        increase_requests = data.get("increase_requests", [])
        
        if not increase_requests:
            return False
            
        # Check frequency of requests
        days_window = self.config.get("request_window_days", 30)
        cutoff_date = datetime.now() - timedelta(days=days_window)
        
        recent_requests = []
        for request in increase_requests:
            try:
                request_date = self._parse_date(request.get("date"))
                if request_date > cutoff_date:
                    recent_requests.append(request)
            except:
                continue
                
        max_requests = self.config.get("max_increase_requests", 2)
        
        if len(recent_requests) > max_requests:
            data["request_info"] = {
                "request_count": len(recent_requests),
                "window_days": days_window,
                "max_allowed": max_requests,
                "request_dates": [r.get("date") for r in recent_requests]
            }
            return True
            
        return False
    
    def _check_suspicious_increases(self, data: Dict[str, Any]) -> bool:
        """Check for suspicious quota increase patterns."""
        increase_history = data.get("increase_history", [])
        
        if not increase_history:
            return False
            
        suspicious_patterns = []
        
        # Pattern 1: Large sudden increase
        if len(increase_history) >= 2:
            last_increase = increase_history[-1]
            prev_increase = increase_history[-2]
            
            if last_increase.get("amount") and prev_increase.get("amount"):
                increase_ratio = last_increase["amount"] / prev_increase["amount"]
                max_ratio = self.config.get("max_increase_ratio", 2.0)
                
                if increase_ratio > max_ratio:
                    suspicious_patterns.append("sudden_increase")
                    
        # Pattern 2: Frequent small increases (salami slicing)
        if len(increase_history) >= 5:
            recent_increases = increase_history[-5:]
            small_increase_count = sum(
                1 for i in recent_increases 
                if i.get("percent_increase", 0) < 20
            )
            
            if small_increase_count >= 4:
                suspicious_patterns.append("salami_slicing")
                
        if suspicious_patterns:
            data["increase_info"] = {
                "patterns": suspicious_patterns,
                "total_increases": len(increase_history),
                "recent_increase": increase_history[-1] if increase_history else None
            }
            return True
            
        return False
    
    def _check_near_limit_pattern(self, data: Dict[str, Any]) -> bool:
        """Check if usage consistently stays near limit."""
        usage_history = data.get("usage_history", [])
        quota_limit = data.get("quota_limit", 0)
        
        if not usage_history or quota_limit <= 0:
            return False
            
        # Check how often usage is near limit (90-99%)
        near_limit_count = 0
        for usage_record in usage_history:
            usage_percent = (usage_record.get("amount", 0) / quota_limit) * 100
            if 90 <= usage_percent <= 99:
                near_limit_count += 1
                
        # If consistently near limit (suspicious optimization)
        threshold_percent = self.config.get("near_limit_threshold_percent", 60)
        if (near_limit_count / len(usage_history)) * 100 > threshold_percent:
            data["limit_usage"] = {
                "near_limit_count": near_limit_count,
                "total_periods": len(usage_history),
                "percentage_near_limit": (near_limit_count / len(usage_history)) * 100
            }
            return True
            
        return False
    
    def _parse_date(self, date_str: Any) -> datetime:
        """Parse date string to datetime."""
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str)
        raise ValueError(f"Cannot parse date: {date_str}")
    
    def _calculate_quota_severity(
        self,
        anomalies: List[str],
        confidence_score: float,
        data: Dict[str, Any]
    ) -> FraudSeverity:
        """Calculate severity for quota abuse."""
        # Quota exceeded is always high priority
        if "quota_exceeded" in anomalies:
            excess_info = data.get("quota_info", {})
            excess_percent = excess_info.get("excess_percent", 0)
            
            if excess_percent > 50:
                return FraudSeverity.CRITICAL
            elif excess_percent > 20:
                return FraudSeverity.HIGH
            else:
                return FraudSeverity.MEDIUM
                
        # Multiple patterns indicate systematic abuse
        if len(anomalies) >= 3:
            return FraudSeverity.HIGH
            
        # Suspicious increases are concerning
        if "suspicious_increase" in anomalies:
            if confidence_score >= 60:
                return FraudSeverity.HIGH
            return FraudSeverity.MEDIUM
            
        # Other patterns
        if confidence_score >= 50:
            return FraudSeverity.MEDIUM
            
        return FraudSeverity.LOW
    
    def _create_quota_description(self, anomalies: List[str], data: Dict[str, Any]) -> str:
        """Create description for quota abuse detection."""
        descriptions = []
        
        if "quota_exceeded" in anomalies:
            info = data.get("quota_info", {})
            excess = info.get("excess_percent", 0)
            descriptions.append(f"Cupo excedido en {excess:.1f}%")
            
        if "rapid_consumption" in anomalies:
            info = data.get("consumption_details", {})
            rate = info.get("consumption_rate", 0)
            descriptions.append(f"Consumo acelerado del cupo: {rate:.1f}% en período")
            
        if "multiple_requests" in anomalies:
            info = data.get("request_info", {})
            count = info.get("request_count", 0)
            descriptions.append(f"Múltiples solicitudes de aumento: {count} solicitudes")
            
        if "suspicious_increase" in anomalies:
            patterns = data.get("increase_info", {}).get("patterns", [])
            if "sudden_increase" in patterns:
                descriptions.append("Aumento repentino sospechoso del cupo")
            if "salami_slicing" in patterns:
                descriptions.append("Patrón de aumentos pequeños frecuentes")
                
        if "near_limit_pattern" in anomalies:
            info = data.get("limit_usage", {})
            percent = info.get("percentage_near_limit", 0)
            descriptions.append(f"Uso consistente cerca del límite: {percent:.1f}% del tiempo")
            
        if descriptions:
            return "Abuso de cupos detectado: " + "; ".join(descriptions)
            
        return "No se detectaron abusos de cupo"