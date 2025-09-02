# backend/src/infrastructure/fraud_detectors/liquidation_fraud_detector.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from backend.src.infrastructure.fraud_detectors.base_detector import (
    BaseDetector, DetectionResult
)
from backend.src.infrastructure.persistence.models import DetectorType, FraudSeverity

logger = logging.getLogger(__name__)


class LiquidationFraudDetector(BaseDetector):
    """
    Detector for liquidation and cash closing fraud patterns:
    - Cash discrepancies
    - Missing deposits
    - Altered liquidation amounts
    - Timing irregularities
    - Pattern of shortages
    """
    
    def _get_detector_type(self) -> DetectorType:
        return DetectorType.LIQUIDATION_FRAUD
    
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """Analyze liquidation data for fraud patterns."""
        anomalies = []
        evidence = {}
        confidence_score = 0.0
        
        # Check cash discrepancies
        if self._check_cash_discrepancy(data):
            anomalies.append("cash_discrepancy")
            evidence["discrepancy_details"] = data.get("cash_info")
            confidence_score += 40
            
        # Check missing deposits
        if self._check_missing_deposits(data):
            anomalies.append("missing_deposits")
            evidence["deposit_info"] = data.get("deposit_details")
            confidence_score += 35
            
        # Check altered amounts
        if self._check_altered_amounts(data):
            anomalies.append("altered_amounts")
            evidence["alteration_evidence"] = data.get("alteration_info")
            confidence_score += 45
            
        # Check timing irregularities
        if self._check_timing_irregularities(data):
            anomalies.append("timing_irregularity")
            evidence["timing_details"] = data.get("timing_info")
            confidence_score += 25
            
        # Check shortage patterns
        if self._check_shortage_patterns(data):
            anomalies.append("shortage_pattern")
            evidence["shortage_history"] = data.get("shortage_info")
            confidence_score += 30
            
        detected = len(anomalies) > 0
        severity = self._calculate_liquidation_severity(anomalies, confidence_score, data)
        description = self._create_liquidation_description(anomalies, data)
        
        return DetectionResult(
            detected=detected,
            severity=severity,
            confidence_score=min(confidence_score, 100),
            description=description,
            evidence=evidence,
            anomaly_details={"liquidation_anomalies": anomalies},
            related_transactions=data.get("related_liquidations", [])
        )
    
    def _check_cash_discrepancy(self, data: Dict[str, Any]) -> bool:
        """Check for discrepancies between reported and actual cash."""
        reported_cash = data.get("reported_cash", 0)
        system_cash = data.get("system_cash", 0)
        sales_total = data.get("sales_total", 0)
        
        if sales_total <= 0:
            return False
            
        # Calculate expected cash
        credit_sales = data.get("credit_sales", 0)
        expected_cash = sales_total - credit_sales
        
        # Check discrepancy
        discrepancy = abs(reported_cash - expected_cash)
        tolerance = self.config.get("cash_discrepancy_tolerance", 10)
        
        if discrepancy > tolerance:
            discrepancy_percent = (discrepancy / expected_cash) * 100 if expected_cash > 0 else 0
            
            data["cash_info"] = {
                "reported_cash": reported_cash,
                "expected_cash": expected_cash,
                "system_cash": system_cash,
                "discrepancy_amount": discrepancy,
                "discrepancy_percent": discrepancy_percent,
                "is_shortage": reported_cash < expected_cash
            }
            return True
            
        return False
    
    def _check_missing_deposits(self, data: Dict[str, Any]) -> bool:
        """Check for missing or delayed deposits."""
        liquidations = data.get("liquidation_history", [])
        deposits = data.get("deposit_history", [])
        
        if not liquidations:
            return False
            
        missing_deposits = []
        delay_threshold = self.config.get("deposit_delay_hours", 48)
        
        for liquidation in liquidations:
            liq_date = self._parse_date(liquidation.get("date"))
            liq_amount = liquidation.get("amount", 0)
            liq_id = liquidation.get("id")
            
            # Find corresponding deposit
            deposit_found = False
            for deposit in deposits:
                dep_date = self._parse_date(deposit.get("date"))
                dep_amount = deposit.get("amount", 0)
                dep_ref = deposit.get("liquidation_ref")
                
                # Match by reference or by amount and timing
                if dep_ref == liq_id or (
                    abs(dep_amount - liq_amount) < 1 and
                    abs((dep_date - liq_date).total_seconds() / 3600) < delay_threshold
                ):
                    deposit_found = True
                    break
                    
            if not deposit_found:
                missing_deposits.append({
                    "liquidation_id": liq_id,
                    "date": str(liq_date),
                    "amount": liq_amount
                })
                
        if missing_deposits:
            data["deposit_details"] = {
                "missing_count": len(missing_deposits),
                "missing_deposits": missing_deposits[:5],  # Limit to 5 examples
                "total_missing_amount": sum(d["amount"] for d in missing_deposits)
            }
            return True
            
        return False
    
    def _check_altered_amounts(self, data: Dict[str, Any]) -> bool:
        """Check for signs of altered liquidation amounts."""
        modifications = data.get("modification_history", [])
        
        if not modifications:
            return False
            
        suspicious_mods = []
        
        for mod in modifications:
            # Check if modification was after initial submission
            time_diff = self._get_time_difference(
                mod.get("original_date"),
                mod.get("modified_date")
            )
            
            if time_diff > 2:  # Modified after 2 hours
                old_amount = mod.get("old_amount", 0)
                new_amount = mod.get("new_amount", 0)
                
                # Check if amount was reduced (potential theft)
                if new_amount < old_amount:
                    suspicious_mods.append({
                        "date": mod.get("modified_date"),
                        "old_amount": old_amount,
                        "new_amount": new_amount,
                        "difference": old_amount - new_amount,
                        "user": mod.get("modified_by")
                    })
                    
        if suspicious_mods:
            data["alteration_info"] = {
                "alteration_count": len(suspicious_mods),
                "total_reduced": sum(m["difference"] for m in suspicious_mods),
                "alterations": suspicious_mods[:3]  # Limit to 3 examples
            }
            return True
            
        return False
    
    def _check_timing_irregularities(self, data: Dict[str, Any]) -> bool:
        """Check for irregular liquidation timing patterns."""
        liquidation_times = data.get("liquidation_times", [])
        
        if len(liquidation_times) < 5:
            return False
            
        irregular_patterns = []
        
        # Check for consistently late submissions
        late_submissions = 0
        expected_hour = self.config.get("expected_liquidation_hour", 23)
        
        for time_str in liquidation_times:
            try:
                liq_time = self._parse_date(time_str)
                if liq_time.hour > expected_hour or liq_time.hour < 5:
                    late_submissions += 1
            except:
                continue
                
        if late_submissions >= len(liquidation_times) * 0.6:
            irregular_patterns.append("consistently_late")
            
        # Check for weekend/holiday liquidations
        weekend_count = sum(
            1 for t in liquidation_times
            if self._parse_date(t).weekday() >= 5
        )
        
        if weekend_count >= 3:
            irregular_patterns.append("weekend_pattern")
            
        if irregular_patterns:
            data["timing_info"] = {
                "patterns": irregular_patterns,
                "late_submissions": late_submissions,
                "weekend_submissions": weekend_count
            }
            return True
            
        return False
    
    def _check_shortage_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for patterns of cash shortages."""
        shortage_history = data.get("shortage_history", [])
        
        if len(shortage_history) < 3:
            return False
            
        # Analyze shortage patterns
        total_shortages = len(shortage_history)
        total_amount = sum(s.get("amount", 0) for s in shortage_history)
        
        # Check frequency
        days_period = self.config.get("shortage_analysis_days", 30)
        cutoff_date = datetime.now() - timedelta(days=days_period)
        
        recent_shortages = [
            s for s in shortage_history
            if self._parse_date(s.get("date")) > cutoff_date
        ]
        
        max_shortages = self.config.get("max_shortages_per_month", 2)
        
        if len(recent_shortages) > max_shortages:
            # Check if amounts are similar (systematic theft)
            amounts = [s.get("amount", 0) for s in recent_shortages]
            avg_amount = sum(amounts) / len(amounts)
            
            similar_amounts = sum(
                1 for a in amounts
                if abs(a - avg_amount) / avg_amount < 0.2  # Within 20% of average
            )
            
            pattern_type = "systematic" if similar_amounts >= len(amounts) * 0.7 else "frequent"
            
            data["shortage_info"] = {
                "shortage_count": len(recent_shortages),
                "period_days": days_period,
                "total_shortage": total_amount,
                "pattern_type": pattern_type,
                "average_shortage": avg_amount
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
    
    def _get_time_difference(self, date1: Any, date2: Any) -> float:
        """Get time difference in hours between two dates."""
        try:
            d1 = self._parse_date(date1)
            d2 = self._parse_date(date2)
            return abs((d2 - d1).total_seconds() / 3600)
        except:
            return 0
    
    def _calculate_liquidation_severity(
        self,
        anomalies: List[str],
        confidence_score: float,
        data: Dict[str, Any]
    ) -> FraudSeverity:
        """Calculate severity for liquidation fraud."""
        # Altered amounts is critical
        if "altered_amounts" in anomalies:
            return FraudSeverity.CRITICAL
            
        # Cash discrepancy with high amount
        if "cash_discrepancy" in anomalies:
            discrepancy = data.get("cash_info", {}).get("discrepancy_amount", 0)
            if discrepancy > 1000:
                return FraudSeverity.HIGH
            elif discrepancy > 500:
                return FraudSeverity.MEDIUM
                
        # Multiple patterns
        if len(anomalies) >= 3:
            return FraudSeverity.HIGH
            
        # Systematic shortages
        if "shortage_pattern" in anomalies:
            pattern_type = data.get("shortage_info", {}).get("pattern_type")
            if pattern_type == "systematic":
                return FraudSeverity.HIGH
                
        if confidence_score >= 60:
            return FraudSeverity.MEDIUM
            
        return FraudSeverity.LOW
    
    def _create_liquidation_description(
        self,
        anomalies: List[str],
        data: Dict[str, Any]
    ) -> str:
        """Create description for liquidation fraud detection."""
        descriptions = []
        
        if "cash_discrepancy" in anomalies:
            info = data.get("cash_info", {})
            amount = info.get("discrepancy_amount", 0)
            shortage = info.get("is_shortage", False)
            descriptions.append(
                f"{'Faltante' if shortage else 'Sobrante'} de efectivo: ${amount:.2f}"
            )
            
        if "missing_deposits" in anomalies:
            info = data.get("deposit_details", {})
            count = info.get("missing_count", 0)
            descriptions.append(f"Depósitos faltantes: {count}")
            
        if "altered_amounts" in anomalies:
            info = data.get("alteration_info", {})
            total = info.get("total_reduced", 0)
            descriptions.append(f"Montos alterados después del cierre: ${total:.2f}")
            
        if "timing_irregularity" in anomalies:
            patterns = data.get("timing_info", {}).get("patterns", [])
            if "consistently_late" in patterns:
                descriptions.append("Liquidaciones consistentemente tardías")
            if "weekend_pattern" in patterns:
                descriptions.append("Patrón de liquidaciones en fin de semana")
                
        if "shortage_pattern" in anomalies:
            info = data.get("shortage_info", {})
            pattern = info.get("pattern_type")
            count = info.get("shortage_count", 0)
            descriptions.append(f"Patrón {pattern} de faltantes: {count} casos")
            
        if descriptions:
            return "Fraude en liquidaciones detectado: " + "; ".join(descriptions)
            
        return "No se detectaron anomalías en liquidaciones"