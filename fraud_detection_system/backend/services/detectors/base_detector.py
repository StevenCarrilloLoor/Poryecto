"""
Clase base para todos los detectores de fraude
backend/services/detectors/base_detector.py
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from decimal import Decimal
import json
import re

from database.db_context import db_context
from models.fraud_models import DetectorType, FraudSeverity


class BaseDetector(ABC):
    """Clase base abstracta para todos los detectores de fraude"""
    
    # Cada detector debe definir estos atributos
    detector_type: DetectorType = None
    detector_name: str = "Base Detector"
    detector_description: str = "Detector base"
    enabled_by_default: bool = True
    
    def __init__(self):
        self.db = db_context
        self.results = []
        
    @abstractmethod
    def detect(self) -> List[Dict[str, Any]]:
        """
        Método abstracto que debe ser implementado por cada detector.
        Retorna una lista de casos de fraude detectados.
        """
        pass
    
    @abstractmethod
    def get_detector_info(self) -> Dict[str, Any]:
        """
        Retorna información sobre el detector para configuración y UI
        """
        return {
            "type": self.detector_type.value if self.detector_type else "UNKNOWN",
            "name": self.detector_name,
            "description": self.detector_description,
            "enabled": self.enabled_by_default,
            "rules": self.get_detection_rules()
        }
    
    @abstractmethod
    def get_detection_rules(self) -> List[str]:
        """
        Retorna lista de reglas que aplica este detector
        """
        pass
    
    def check_existing_case(self, source_table: str, source_record_id: str, 
                           detector_type: DetectorType = None) -> bool:
        """Verifica si ya existe un caso para este registro"""
        try:
            with self.db.get_session() as session:
                from models.fraud_models import FraudCase
                
                # Usar el detector_type del detector actual si no se especifica
                if detector_type is None:
                    detector_type = self.detector_type
                    
                existing = session.query(FraudCase).filter(
                    FraudCase.source_table == source_table,
                    FraudCase.source_record_id == str(source_record_id),
                    FraudCase.detector_type == detector_type
                ).first()
                return existing is not None
        except Exception as e:
            print(f"Error verificando caso existente: {e}")
            return False
    
    def parse_firebird_date(self, date_value) -> Optional[datetime]:
        """Convierte fecha de Firebird a datetime de Python"""
        if date_value is None:
            return None
            
        # Si ya es datetime, devolverlo
        if isinstance(date_value, datetime):
            return date_value
            
        # Si es date, convertir a datetime
        if isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time())
            
        # Si es string, intentar parsear
        if isinstance(date_value, str):
            # Limpiar espacios extras que vienen de Firebird
            date_str = date_value.strip()
            
            # Si tiene más de 19 caracteres, truncar
            if len(date_str) > 19:
                date_str = date_str[:19]
            
            # Manejar formato con hora de un solo dígito
            match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_str)
            if match:
                date_part = match.group(1)
                hour = match.group(2).zfill(2)
                minute = match.group(3)
                second = match.group(4)
                date_str = f"{date_part} {hour}:{minute}:{second}"
            
            # Intentar varios formatos comunes
            formats = [
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        
        return None
    
    def safe_float(self, value, default=0.0) -> float:
        """Convierte valor a float de forma segura"""
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default
    
    def safe_divide(self, numerator, denominator, default=0.0) -> float:
        """División segura que evita división por cero"""
        num = self.safe_float(numerator)
        den = self.safe_float(denominator)
        
        if den == 0:
            return default
        return num / den
    
    def create_fraud_case(self, 
                         title: str,
                         description: str,
                         severity: FraudSeverity,
                         amount: Decimal = None,
                         source_table: str = None,
                         source_record_id: str = None,
                         client_code: str = None,
                         client_name: str = None,
                         client_ruc: str = None,
                         transaction_date: datetime = None,
                         confidence_score: float = None,
                         detection_rules: Dict = None) -> Optional[Dict]:
        """Crea un caso de fraude con verificación de duplicados"""
        
        # Usar el detector_type de la clase
        detector_type = self.detector_type
        
        # Verificar duplicados antes de crear
        if source_table and source_record_id:
            if self.check_existing_case(source_table, source_record_id, detector_type):
                print(f"    ⚠ Caso ya existe para {source_table}:{source_record_id}")
                return None
        
        # Asegurar que transaction_date sea datetime válido
        if transaction_date:
            transaction_date = self.parse_firebird_date(transaction_date)
        
        return {
            "title": title,
            "description": description,
            "detector_type": detector_type,
            "severity": severity,
            "amount": self.safe_float(amount) if amount else None,
            "source_table": source_table,
            "source_record_id": str(source_record_id) if source_record_id else None,
            "client_code": str(client_code) if client_code else None,
            "client_name": str(client_name) if client_name else None,
            "client_ruc": str(client_ruc) if client_ruc else None,
            "transaction_date": transaction_date,
            "confidence_score": confidence_score,
            "detection_rules": json.dumps(detection_rules) if detection_rules else None,
            "created_by": "SYSTEM"
        }
    
    def log_detection_start(self):
        """Log al iniciar detección"""
        print(f"  Iniciando {self.detector_name}...")
    
    def log_detection_end(self, count: int):
        """Log al finalizar detección"""
        print(f"  {self.detector_name} completado: {count} casos detectados")