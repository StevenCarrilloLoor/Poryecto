# backend/src/infrastructure/fraud_detectors/data_manipulation_detector.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from backend.src.infrastructure.fraud_detectors.base_detector import (
    BaseDetector, DetectionResult
)
from backend.src.infrastructure.persistence.models import DetectorType, FraudSeverity

logger = logging.getLogger(__name__)


class DataManipulationDetector(BaseDetector):
    """
    Detector for data manipulation patterns:
    - Massive record changes
    - Suspicious deletions
    - Modifications outside business hours
    - Unauthorized user modifications
    - Audit trail anomalies
    """
    
    def _get_detector_type(self) -> DetectorType:
        return DetectorType.DATA_MANIPULATION
    
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """Analyze audit logs for data manipulation patterns."""
        anomalies = []
        evidence = {}
        confidence_score = 0.0
        
        # Check massive changes
        if self._check_massive_changes(data):
            anomalies.append("massive_changes")
            evidence["change_count"] = data.get("change_count")
            confidence_score += 35
            
        # Check suspicious deletions
        if self._check_suspicious_deletions(data):
            anomalies.append("suspicious_deletions")
            evidence["deletion_info"] = data.get("deletion_details")
            confidence_score += 40
            
        # Check after-hours modifications
        if self._check_afterhours_modifications(data):
            anomalies.append("afterhours_modifications")
            evidence["modification_times"] = data.get("afterhours_times")
            confidence_score += 25
            
        # Check unauthorized modifications
        if self._check_unauthorized_modifications(data):
            anomalies.append("unauthorized_modifications")
            evidence["unauthorized_users"] = data.get("unauthorized_list")
            confidence_score += 45
            
        # Check audit trail gaps
        if self._check_audit_gaps(data):
            anomalies.append("audit_gaps")
            evidence["gap_details"] = data.get("audit_gap_info")
            confidence_score += 30
            
        detected = len(anomalies) > 0
        severity = self._calculate_manipulation_severity(anomalies, confidence_score)
        description = self._create_manipulation_description(anomalies, data)
        
        return DetectionResult(
            detected=detected,
            severity=severity,
            confidence_score=min(confidence_score, 100),
            description=description,
            evidence=evidence,
            anomaly_details={"manipulation_patterns": anomalies},
            related_transactions=data.get("affected_records", [])
        )
    
    def _check_massive_changes(self, data: Dict[str, Any]) -> bool:
        """Check for massive record changes in short period."""
        changes = data.get("recent_changes", [])
        time_window = self.config.get("massive_change_window_hours", 2)
        threshold = self.config.get("massive_change_threshold", 50)
        
        if len(changes) < threshold:
            return False
            
        # Group changes by time window
        now = datetime.now()
        cutoff = now - timedelta(hours=time_window)
        
        recent_changes = [
            c for c in changes 
            if self._parse_date(c.get("timestamp", "")) > cutoff
        ]
        
        if len(recent_changes) >= threshold:
            data["change_count"] = {
                "count": len(recent_changes),
                "window_hours": time_window,
                "user": recent_changes[0].get("user") if recent_changes else "unknown"
            }
            return True
            
        return False
    
    def _check_suspicious_deletions(self, data: Dict[str, Any]) -> bool:
        """Check for suspicious deletion patterns."""
        deletions = data.get("deletions", [])
        
        if not deletions:
            return False
            
        suspicious_patterns = []
        
        # Pattern 1: Deleting old records (covering tracks)
        old_deletions = [
            d for d in deletions 
            if self._is_old_record(d.get("record_date"))
        ]
        
        if len(old_deletions) >= 5:
            suspicious_patterns.append("old_records")
            
        # Pattern 2: Selective deletions (specific dates/amounts)
        if self._check_selective_deletions(deletions):
            suspicious_patterns.append("selective")
            
        # Pattern 3: Deletions without backup
        no_backup = [d for d in deletions if not d.get("has_backup", False)]
        if len(no_backup) >= 3:
            suspicious_patterns.append("no_backup")
            
        if suspicious_patterns:
            data["deletion_details"] = {
                "patterns": suspicious_patterns,
                "count": len(deletions),
                "old_records": len(old_deletions)
            }
            return True
            
        return False
    
    def _check_afterhours_modifications(self, data: Dict[str, Any]) -> bool:
        """Check for modifications outside business hours."""
        modifications = data.get("modifications", [])
        
        if not modifications:
            return False
            
        start_hour = self.config.get("business_start_hour", 7)
        end_hour = self.config.get("business_end_hour", 19)
        
        afterhours_mods = []
        
        for mod in modifications:
            try:
                timestamp = self._parse_date(mod.get("timestamp", ""))
                hour = timestamp.hour
                
                # Check if outside hours or weekend
                if hour < start_hour or hour >= end_hour or timestamp.weekday() >= 5:
                    afterhours_mods.append({
                        "time": str(timestamp),
                        "user": mod.get("user"),
                        "action": mod.get("action")
                    })
            except:
                continue
                
        if len(afterhours_mods) >= 3:
            data["afterhours_times"] = afterhours_mods[:10]  # Limit to 10 examples
            return True
            
        return False
    
    def _check_unauthorized_modifications(self, data: Dict[str, Any]) -> bool:
        """Check for modifications by unauthorized users."""
        modifications = data.get("modifications", [])
        authorized_users = data.get("authorized_users", [])
        
        if not modifications or not authorized_users:
            return False
            
        unauthorized = []
        
        for mod in modifications:
            user = mod.get("user", "")
            if user and user not in authorized_users:
                if user not in unauthorized:
                    unauthorized.append(user)
                    
        if unauthorized:
            data["unauthorized_list"] = unauthorized
            return True
            
        return False
    
    def _check_audit_gaps(self, data: Dict[str, Any]) -> bool:
        """Check for gaps in audit trail."""
        audit_logs = data.get("audit_logs", [])
        
        if len(audit_logs) < 2:
            return False
            
        # Sort by ID or timestamp
        sorted_logs = sorted(audit_logs, key=lambda x: x.get("id", 0))
        
        gaps = []
        for i in range(len(sorted_logs) - 1):
            current_id = sorted_logs[i].get("id", 0)
            next_id = sorted_logs[i + 1].get("id", 0)
            
            if next_id - current_id > 1:
                gaps.append({
                    "from_id": current_id,
                    "to_id": next_id,
                    "missing": next_id - current_id - 1
                })
                
        if gaps:
            data["audit_gap_info"] = {
                "gap_count": len(gaps),
                "total_missing": sum(g["missing"] for g in gaps),
                "largest_gap": max(g["missing"] for g in gaps)
            }
            return True
            
        return False
    
    def _is_old_record(self, record_date: Any) -> bool:
        """Check if a record is considered old."""
        if not record_date:
            return False
            
        try:
            date = self._parse_date(record_date)
            age_days = (datetime.now() - date).days
            return age_days > self.config.get("old_record_days", 365)
        except:
            return False
    
    def _check_selective_deletions(self, deletions: List[Dict]) -> bool:
        """Check for selective deletion patterns."""
        if len(deletions) < 3:
            return False
            
        # Check if deletions target specific patterns
        amounts = [d.get("amount", 0) for d in deletions if d.get("amount")]
        dates = [d.get("date") for d in deletions if d.get("date")]
        
        # Check for round amounts
        if amounts:
            round_amounts = [a for a in amounts if a > 0 and a % 100 == 0]
            if len(round_amounts) >= len(amounts) * 0.7:
                return True
                
        # Check for specific date patterns
        if dates:
            try:
                parsed_dates = [self._parse_date(d) for d in dates]
                # Check if all are from same day of month
                days = [d.day for d in parsed_dates]
                if len(set(days)) == 1:
                    return True
            except:
                pass
                
        return False
    
    def _parse_date(self, date_str: Any) -> datetime:
        """Parse date string to datetime."""
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str)
        raise ValueError(f"Cannot parse date: {date_str}")
    
    def _calculate_manipulation_severity(
        self,
        anomalies: List[str],
        confidence_score: float
    ) -> FraudSeverity:
        """Calculate severity for data manipulation."""
        critical_patterns = ["unauthorized_modifications", "audit_gaps"]
        high_patterns = ["suspicious_deletions", "massive_changes"]
        
        if any(p in critical_patterns for p in anomalies):
            return FraudSeverity.CRITICAL
            
        if any(p in high_patterns for p in anomalies):
            if confidence_score >= 60:
                return FraudSeverity.HIGH
            return FraudSeverity.MEDIUM
            
        if confidence_score >= 50:
            return FraudSeverity.MEDIUM
            
        return FraudSeverity.LOW
    
    def _create_manipulation_description(
        self,
        anomalies: List[str],
        data: Dict[str, Any]
    ) -> str:
        """Create description for data manipulation detection."""
        descriptions = []
        
        if "massive_changes" in anomalies:
            count = data.get("change_count", {}).get("count", 0)
            descriptions.append(f"Cambios masivos detectados: {count} registros modificados")
            
        if "suspicious_deletions" in anomalies:
            descriptions.append("Patrón sospechoso de eliminación de registros")
            
        if "afterhours_modifications" in anomalies:
            descriptions.append("Modificaciones realizadas fuera de horario laboral")
            
        if "unauthorized_modifications" in anomalies:
            users = data.get("unauthorized_list", [])
            descriptions.append(f"Modificaciones por usuarios no autorizados: {', '.join(users[:3])}")
            
        if "audit_gaps" in anomalies:
            missing = data.get("audit_gap_info", {}).get("total_missing", 0)
            descriptions.append(f"Brechas en auditoría: {missing} registros faltantes")
            
        if descriptions:
            return "Manipulación de datos detectada: " + "; ".join(descriptions)
            
        return "No se detectaron manipulaciones de datos"