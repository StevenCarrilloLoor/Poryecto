"""
Factory para gestión dinámica de detectores
backend/services/detectors/detector_factory.py
"""

import os
import importlib
import inspect
from typing import List, Dict, Type, Optional, Any
from pathlib import Path

from .base_detector import BaseDetector
from models.fraud_models import DetectorType


class DetectorFactory:
    """
    Factory que gestiona dinámicamente los detectores de fraude.
    Permite agregar/quitar detectores sin modificar el código principal.
    """
    
    def __init__(self):
        self._detectors: Dict[str, Type[BaseDetector]] = {}
        self._detector_instances: Dict[str, BaseDetector] = {}
        self._load_detectors()
    
    def _load_detectors(self):
        """
        Carga dinámicamente todos los detectores del directorio actual.
        Busca todas las clases que heredan de BaseDetector.
        """
        # Obtener el directorio actual
        current_dir = Path(__file__).parent
        
        # Buscar todos los archivos Python en el directorio
        for file_path in current_dir.glob("*_detector.py"):
            if file_path.name == "base_detector.py":
                continue
                
            # Obtener el nombre del módulo
            module_name = file_path.stem
            
            try:
                # Importar el módulo dinámicamente
                module = importlib.import_module(f".{module_name}", package="services.detectors")
                
                # Buscar clases que heredan de BaseDetector
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseDetector) and 
                        obj != BaseDetector):
                        
                        # Verificar que tenga un detector_type válido
                        if hasattr(obj, 'detector_type') and obj.detector_type:
                            detector_key = obj.detector_type.value
                            self._detectors[detector_key] = obj
                            print(f"  ✓ Detector cargado: {obj.detector_name} ({detector_key})")
                        
            except Exception as e:
                print(f"  ✗ Error cargando detector desde {module_name}: {e}")
    
    def get_available_detectors(self) -> List[str]:
        """Retorna lista de detectores disponibles"""
        return list(self._detectors.keys())
    
    def get_detector_info(self) -> List[Dict[str, Any]]:
        """Retorna información de todos los detectores disponibles"""
        info = []
        for key, detector_class in self._detectors.items():
            instance = self.get_detector(key)
            if instance:
                info.append({
                    "key": key,
                    "name": instance.detector_name,
                    "description": instance.detector_description,
                    "enabled": instance.enabled_by_default,
                    "info": instance.get_detector_info()
                })
        return info
    
    def get_detector(self, detector_type: str) -> Optional[BaseDetector]:
        """
        Obtiene una instancia del detector especificado.
        Usa singleton pattern para reutilizar instancias.
        """
        if detector_type not in self._detectors:
            print(f"  ✗ Detector no encontrado: {detector_type}")
            return None
        
        # Crear instancia si no existe
        if detector_type not in self._detector_instances:
            self._detector_instances[detector_type] = self._detectors[detector_type]()
        
        return self._detector_instances[detector_type]
    
    def get_all_detectors(self) -> List[BaseDetector]:
        """Retorna instancias de todos los detectores disponibles"""
        detectors = []
        for detector_type in self._detectors.keys():
            detector = self.get_detector(detector_type)
            if detector:
                detectors.append(detector)
        return detectors
    
    def get_detectors_by_types(self, detector_types: List[DetectorType]) -> List[BaseDetector]:
        """Retorna detectores específicos por tipo"""
        detectors = []
        for dt in detector_types:
            detector = self.get_detector(dt.value)
            if detector:
                detectors.append(detector)
        return detectors
    
    def run_all_detectors(self) -> Dict[str, List[Dict[str, Any]]]:
        """Ejecuta todos los detectores disponibles"""
        results = {}
        
        for detector_type, detector_class in self._detectors.items():
            try:
                detector = self.get_detector(detector_type)
                if detector and detector.enabled_by_default:
                    print(f"\nEjecutando {detector.detector_name}...")
                    detector_results = detector.detect()
                    results[detector_type] = detector_results
                    print(f"  Completado: {len(detector_results)} casos detectados")
            except Exception as e:
                print(f"  Error ejecutando {detector_type}: {e}")
                results[detector_type] = []
        
        return results
    
    def run_specific_detectors(self, detector_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Ejecuta detectores específicos"""
        results = {}
        
        for detector_type in detector_types:
            if detector_type in self._detectors:
                try:
                    detector = self.get_detector(detector_type)
                    if detector:
                        print(f"\nEjecutando {detector.detector_name}...")
                        detector_results = detector.detect()
                        results[detector_type] = detector_results
                        print(f"  Completado: {len(detector_results)} casos detectados")
                except Exception as e:
                    print(f"  Error ejecutando {detector_type}: {e}")
                    results[detector_type] = []
            else:
                print(f"  Detector no encontrado: {detector_type}")
        
        return results
    
    def reload_detectors(self):
        """Recarga todos los detectores (útil para desarrollo)"""
        self._detectors.clear()
        self._detector_instances.clear()
        self._load_detectors()
        print(f"Detectores recargados: {len(self._detectors)} disponibles")


# Instancia singleton del factory
detector_factory = DetectorFactory()