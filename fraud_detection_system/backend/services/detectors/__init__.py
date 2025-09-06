"""
Módulo de detectores de fraude
backend/services/detectors/__init__.py
"""

from .base_detector import BaseDetector
from .detector_factory import detector_factory
from .invoice_anomaly_detector import InvoiceAnomalyDetector
from .fuel_theft_detector import FuelTheftDetector
from .data_manipulation_detector import DataManipulationDetector

# Para compatibilidad con el código existente
# Mapeo de nombres antiguos a nuevas clases
FacturasAnomalias = InvoiceAnomalyDetector
RoboDeCombustible = FuelTheftDetector
ManipulacionDatos = DataManipulationDetector

__all__ = [
    'BaseDetector',
    'detector_factory',
    'InvoiceAnomalyDetector',
    'FuelTheftDetector',
    'DataManipulationDetector',
    # Compatibilidad
    'FacturasAnomalias',
    'RoboDeCombustible',
    'ManipulacionDatos'
]