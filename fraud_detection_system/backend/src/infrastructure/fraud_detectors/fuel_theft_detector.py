# backend/src/infrastructure/fraud_detectors/fuel_theft_detector.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from backend.src.infrastructure.fraud_detectors.base_detector import (
    BaseDetector, DetectionResult
)
from backend.src.infrastructure.persistence.models import DetectorType, FraudSeverity

logger = logging.getLogger(__name__)


class FuelTheftDetector(BaseDetector):
    """
    Detector for fuel-related fraud patterns:
    - Fuel consumption vs distance anomalies
    - Excessive refueling for vehicle type
    - Suspicious loading patterns
    - Refueling at unusual locations
    - Tank capacity violations
    """
    
    def _get_detector_type(self) -> DetectorType:
        return DetectorType.FUEL_THEFT
    
    def detect(self, data: Dict[str, Any]) -> DetectionResult:
        """Analyze fuel dispatch data for theft patterns."""
        anomalies = []
        evidence = {}
        confidence_score = 0.0
        
        # Check tank capacity violation
        if self._check_overcapacity(data):
            anomalies.append("overcapacity")
            evidence["overcapacity_details"] = data.get("overcapacity_info")
            confidence_score += 40  # High confidence - physical impossibility
            
        # Check consumption vs distance
        if self._check_consumption_anomaly(data):
            anomalies.append("consumption_anomaly")
            evidence["consumption_ratio"] = data.get("consumption_ratio")
            confidence_score += 30
            
        # Check refueling frequency
        if self._check_excessive_refueling(data):
            anomalies.append("excessive_refueling")
            evidence["refuel_frequency"] = data.get("refuel_count")
            confidence_score += 25
            
        # Check suspicious patterns
        if self._check_suspicious_patterns(data):
            anomalies.append("suspicious_pattern")
            evidence["pattern_details"] = data.get("pattern_info")
            confidence_score += 35
            
        # Check location anomalies
        if self._check_location_anomaly(data):
            anomalies.append("location_anomaly")
            evidence["location_info"] = data.get("location_details")
            confidence_score += 20
            
        detected = len(anomalies) > 0
        severity = self._calculate_severity_for_fuel(anomalies, confidence_score)
        description = self._create_fuel_description(anomalies, data)
        
        return DetectionResult(
            detected=detected,
            severity=severity,
            confidence_score=min(confidence_score, 100),
            description=description,
            evidence=evidence,
            anomaly_details={"fuel_anomalies": anomalies},
            related_transactions=data.get("related_dispatches", [])
        )
    
    def _check_overcapacity(self, data: Dict[str, Any]) -> bool:
        """Check if fuel amount exceeds tank capacity."""
        fuel_amount = data.get("fuel_amount", 0)
        tank_capacity = data.get("tank_capacity", 0)
        
        if tank_capacity <= 0 or fuel_amount <= 0:
            return False
            
        # Allow small margin for measurement error
        tolerance = self.config.get("capacity_tolerance_percent", 5) / 100
        max_allowed = tank_capacity * (1 + tolerance)
        
        if fuel_amount > max_allowed:
            data["overcapacity_info"] = {
                "fuel_amount": fuel_amount,
                "tank_capacity": tank_capacity,
                "excess_percent": ((fuel_amount - tank_capacity) / tank_capacity) * 100
            }
            return True
            
        return False
    
    def _check_consumption_anomaly(self, data: Dict[str, Any]) -> bool:
        """Check if fuel consumption doesn't match distance traveled."""
        distance = data.get("distance_traveled", 0)
        fuel_consumed = data.get("fuel_consumed", 0)
        vehicle_type = data.get("vehicle_type", "")
        
        if distance <= 0 or fuel_consumed <= 0:
            return False
            
        # Calculate km per liter
        km_per_liter = distance / fuel_consumed
        
        # Expected ranges by vehicle type (configurable)
        expected_ranges = self.config.get("expected_consumption", {
            "car": {"min": 8, "max": 20},
            "truck": {"min": 3, "max": 8},
            "motorcycle": {"min": 20, "max": 40},
            "bus": {"min": 2, "max": 6}
        })
        
        # Get range for vehicle type
        vehicle_range = expected_ranges.get(vehicle_type.lower(), {"min": 2, "max": 40})
        
        # Check if outside expected range
        if km_per_liter < vehicle_range["min"] or km_per_liter > vehicle_range["max"]:
            data["consumption_ratio"] = {
                "km_per_liter": km_per_liter,
                "expected_min": vehicle_range["min"],
                "expected_max": vehicle_range["max"],
                "vehicle_type": vehicle_type
            }
            return True
            
        return False
    
    def _check_excessive_refueling(self, data: Dict[str, Any]) -> bool:
        """Check for excessive refueling frequency."""
        refuel_history = data.get("refuel_history", [])
        days_period = self.config.get("refuel_check_days", 7)
        
        if not refuel_history:
            return False
            
        # Count refuels in the period
        cutoff_date = datetime.now() - timedelta(days=days_period)
        recent_refuels = [
            r for r in refuel_history 
            if self._parse_date(r.get("date")) > cutoff_date
        ]
        
        # Get thresholds by vehicle type
        vehicle_type = data.get("vehicle_type", "").lower()
        max_refuels = self.config.get("max_refuels_per_week", {
            "car": 3,
            "truck": 7,
            "motorcycle": 2,
            "bus": 10
        }).get(vehicle_type, 5)
        
        if len(recent_refuels) > max_refuels:
            data["refuel_count"] = {
                "count": len(recent_refuels),
                "period_days": days_period,
                "max_expected": max_refuels,
                "dates": [r.get("date") for r in recent_refuels]
            }
            return True
            
        return False
    
    def _check_suspicious_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for suspicious refueling patterns."""
        patterns_found = []
        
        # Pattern 1: Same amount repeatedly
        if self._check_repeated_amounts(data):
            patterns_found.append("repeated_amounts")
            
        # Pattern 2: Always filling at same time
        if self._check_time_pattern(data):
            patterns_found.append("time_pattern")
            
        # Pattern 3: Split refueling (multiple small amounts quickly)
        if self._check_split_refueling(data):
            patterns_found.append("split_refueling")
            
        if patterns_found:
            data["pattern_info"] = patterns_found
            return True
            
        return False
    
    def _check_repeated_amounts(self, data: Dict[str, Any]) -> bool:
        """Check for suspiciously repeated fuel amounts."""
        recent_amounts = data.get("recent_fuel_amounts", [])
        
        if len(recent_amounts) < 5:
            return False
            
        # Count frequency of each amount
        from collections import Counter
        amount_counts = Counter(recent_amounts)
        
        # Check if any amount appears too frequently
        for amount, count in amount_counts.most_common(1):
            if count >= 3 and amount > 0:  # Same amount 3+ times
                return True
                
        return False
    
    def _check_time_pattern(self, data: Dict[str, Any]) -> bool:
        """Check if refueling always happens at similar times."""
        refuel_times = data.get("refuel_times", [])
        
        if len(refuel_times) < 5:
            return False
            
        # Extract hours
        hours = []
        for time_str in refuel_times:
            try:
                dt = self._parse_date(time_str)
                hours.append(dt.hour)
            except:
                continue
                
        if len(hours) < 3:
            return False
            
        # Check if most refuels happen in same 2-hour window
        from collections import Counter
        hour_counts = Counter(hours)
        
        # Group into 2-hour windows
        window_counts = {}
        for hour, count in hour_counts.items():
            window = hour // 2
            window_counts[window] = window_counts.get(window, 0) + count
            
        # Check if any window has majority
        max_count = max(window_counts.values())
        if max_count >= len(hours) * 0.7:  # 70% in same window
            return True
            
        return False
    
    def _check_split_refueling(self, data: Dict[str, Any]) -> bool:
        """Check for split refueling pattern (avoiding limits)."""
        refuel_history = data.get("refuel_history", [])
        
        if len(refuel_history) < 2:
            return False
            
        # Look for multiple refuels within short time
        for i in range(len(refuel_history) - 1):
            current = refuel_history[i]
            next_refuel = refuel_history[i + 1]
            
            try:
                current_time = self._parse_date(current.get("date"))
                next_time = self._parse_date(next_refuel.get("date"))
                
                time_diff = (next_time - current_time).total_seconds() / 3600  # Hours
                
                # Multiple refuels within 2 hours
                if time_diff < 2:
                    return True
                    
            except:
                continue
                
        return False
    
    def _check_location_anomaly(self, data: Dict[str, Any]) -> bool:
        """Check for refueling at unusual locations."""
        location = data.get("refuel_location", "")
        usual_locations = data.get("usual_locations", [])
        
        if not location or not usual_locations:
            return False
            
        # Check if current location is unusual
        if location not in usual_locations:
            data["location_details"] = {
                "current_location": location,
                "usual_locations": usual_locations
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
    
    def _calculate_severity_for_fuel(
        self,
        anomalies: List[str],
        confidence_score: float
    ) -> FraudSeverity:
        """Calculate severity for fuel theft."""
        # Overcapacity is always critical (physical impossibility)
        if "overcapacity" in anomalies:
            return FraudSeverity.CRITICAL
            
        # Multiple patterns indicate organized theft
        if len(anomalies) >= 3:
            return FraudSeverity.HIGH
            
        # Suspicious patterns are medium to high
        if "suspicious_pattern" in anomalies or "consumption_anomaly" in anomalies:
            if confidence_score >= 60:
                return FraudSeverity.HIGH
            return FraudSeverity.MEDIUM
            
        # Other anomalies
        if confidence_score >= 50:
            return FraudSeverity.MEDIUM
            
        return FraudSeverity.LOW
    
    def _create_fuel_description(self, anomalies: List[str], data: Dict[str, Any]) -> str:
        """Create description for fuel theft detection."""
        descriptions = []
        
        if "overcapacity" in anomalies:
            info = data.get("overcapacity_info", {})
            excess = info.get("excess_percent", 0)
            descriptions.append(f"Carga de combustible excede capacidad del tanque en {excess:.1f}%")
            
        if "consumption_anomaly" in anomalies:
            descriptions.append("Consumo de combustible no corresponde con distancia recorrida")
            
        if "excessive_refueling" in anomalies:
            count = data.get("refuel_count", {}).get("count", 0)
            descriptions.append(f"Frecuencia excesiva de repostaje: {count} veces en período")
            
        if "suspicious_pattern" in anomalies:
            descriptions.append("Patrones sospechosos de repostaje detectados")
            
        if "location_anomaly" in anomalies:
            descriptions.append("Repostaje en ubicación inusual")
            
        if descriptions:
            return "Posible robo de combustible: " + "; ".join(descriptions)
            
        return "No se detectaron anomalías en el consumo de combustible"