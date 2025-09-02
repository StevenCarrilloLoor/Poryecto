# backend/src/infrastructure/fraud_detectors/detector_factory.py

import logging
from typing import Dict, List, Type

from backend.src.infrastructure.fraud_detectors.base_detector import BaseDetector
from backend.src.infrastructure.fraud_detectors.invoice_anomaly_detector import InvoiceAnomalyDetector
from backend.src.infrastructure.fraud_detectors.fuel_theft_detector import FuelTheftDetector
from backend.src.infrastructure.fraud_detectors.data_manipulation_detector import DataManipulationDetector
from backend.src.infrastructure.fraud_detectors.quota_abuse_detector import QuotaAbuseDetector
from backend.src.infrastructure.fraud_detectors.liquidation_fraud_detector import LiquidationFraudDetector
from backend.src.infrastructure.persistence.models import DetectorType

logger = logging.getLogger(__name__)


class DetectorFactory:
    """
    Factory pattern for creating fraud detector instances.
    Manages registration and instantiation of all detector types.
    """
    
    # Registry of available detectors
    _detectors: Dict[DetectorType, Type[BaseDetector]] = {
        DetectorType.INVOICE_ANOMALY: InvoiceAnomalyDetector,
        DetectorType.FUEL_THEFT: FuelTheftDetector,
        DetectorType.DATA_MANIPULATION: DataManipulationDetector,
        DetectorType.QUOTA_ABUSE: QuotaAbuseDetector,
        DetectorType.LIQUIDATION_FRAUD: LiquidationFraudDetector,
    }
    
    @classmethod
    def create_detector(
        cls,
        detector_type: DetectorType,
        config: Dict = None
    ) -> BaseDetector:
        """
        Create a detector instance of the specified type.
        
        Args:
            detector_type: Type of detector to create
            config: Optional configuration dictionary
            
        Returns:
            Configured detector instance
            
        Raises:
            ValueError: If detector type is not registered
        """
        if detector_type not in cls._detectors:
            raise ValueError(f"Unknown detector type: {detector_type}")
            
        detector_class = cls._detectors[detector_type]
        detector = detector_class(config)
        
        logger.info(f"Created detector: {detector_type.value}")
        return detector
    
    @classmethod
    def create_all_detectors(cls, config: Dict = None) -> List[BaseDetector]:
        """
        Create instances of all registered detectors.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            List of all detector instances
        """
        detectors = []
        
        for detector_type in cls._detectors.keys():
            try:
                detector = cls.create_detector(detector_type, config)
                detectors.append(detector)
            except Exception as e:
                logger.error(f"Failed to create detector {detector_type}: {e}")
                
        return detectors
    
    @classmethod
    def register_detector(
        cls,
        detector_type: DetectorType,
        detector_class: Type[BaseDetector]
    ):
        """
        Register a new detector type.
        
        Args:
            detector_type: Type identifier for the detector
            detector_class: Class implementing BaseDetector
        """
        if not issubclass(detector_class, BaseDetector):
            raise TypeError(f"{detector_class} must inherit from BaseDetector")
            
        cls._detectors[detector_type] = detector_class
        logger.info(f"Registered detector: {detector_type.value}")
    
    @classmethod
    def get_available_detectors(cls) -> List[DetectorType]:
        """Get list of available detector types."""
        return list(cls._detectors.keys())
    
    @classmethod
    def is_detector_available(cls, detector_type: DetectorType) -> bool:
        """Check if a detector type is available."""
        return detector_type in cls._detectors