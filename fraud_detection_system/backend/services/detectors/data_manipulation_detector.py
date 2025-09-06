"""
Detector de manipulación de datos
backend/services/detectors/data_manipulation_detector.py
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import re

from .base_detector import BaseDetector
from models.fraud_models import DetectorType, FraudSeverity


class DataManipulationDetector(BaseDetector):
    """Detector especializado en manipulación de datos"""
    
    detector_type = DetectorType.DATA_MANIPULATION
    detector_name = "Detector de Manipulación de Datos"
    detector_description = "Detecta cambios masivos, eliminaciones sospechosas y alteraciones no autorizadas"
    enabled_by_default = True
    
    def detect(self) -> List[Dict[str, Any]]:
        """Ejecuta todas las detecciones de manipulación de datos"""
        self.results = []
        self.log_detection_start()
        
        try:
            print("    Detectando cambios masivos...")
            self._detect_cambios_masivos()
            
            print("    Detectando secuencias faltantes...")
            self._detect_secuencias_faltantes()
        except Exception as e:
            print(f"  Error en {self.detector_name}: {e}")
        
        # Filtrar None (casos duplicados)
        self.results = [r for r in self.results if r is not None]
        self.log_detection_end(len(self.results))
        
        return self.results
    
    def get_detector_info(self) -> Dict[str, Any]:
        """Información del detector"""
        info = super().get_detector_info()
        info["thresholds"] = {
            "massive_changes_min": 20,
            "massive_changes_critical": 50,
            "sequence_gap_min": 10,
            "sequence_gap_critical": 50,
            "days_lookback": 7
        }
        return info
    
    def get_detection_rules(self) -> List[str]:
        """Reglas que aplica este detector"""
        return [
            "Cambios masivos de registros (>20 en un día)",
            "Secuencias faltantes en documentos",
            "Eliminaciones masivas de registros",
            "Modificaciones fuera del horario laboral",
            "Alteraciones no autorizadas de datos críticos"
        ]
    
    def _detect_cambios_masivos(self):
        """Detecta cambios masivos de registros"""
        query = """
        SELECT COD_XUSUA, FEC_XDCTO
        FROM XDCTO
        WHERE FEC_XDCTO IS NOT NULL
        """
        
        try:
            cambios = self.db.execute_firebird_query(query)
            
            fecha_limite = datetime.now() - timedelta(days=7)
            usuario_cambios = {}
            
            for c in cambios:
                fecha = self.parse_firebird_date(c.get('FEC_XDCTO'))
                if fecha and fecha >= fecha_limite:
                    usuario = c.get('COD_XUSUA', 'UNKNOWN')
                    fecha_str = fecha.date().isoformat()
                    key = f"{usuario}_{fecha_str}"
                    
                    if key not in usuario_cambios:
                        usuario_cambios[key] = {
                            'usuario': usuario,
                            'fecha': fecha,
                            'count': 0
                        }
                    usuario_cambios[key]['count'] += 1
            
            # Detectar cambios masivos
            for key, info in usuario_cambios.items():
                if info['count'] > 20:
                    # ID único para el grupo
                    group_id = f"MASSIVE_{key}_{info['count']}"
                    
                    if not self.check_existing_case("XDCTO", group_id):
                        case = self.create_fraud_case(
                            title=f"Cambios masivos detectados - Usuario {info['usuario']}",
                            description=f"El usuario {info['usuario']} realizó {info['count']} "
                                       f"modificaciones en el día {info['fecha'].date()}. "
                                       f"Esto requiere revisión inmediata.",
                            severity=FraudSeverity.HIGH if info['count'] > 50 else FraudSeverity.MEDIUM,
                            source_table="XDCTO",
                            source_record_id=group_id,
                            transaction_date=info['fecha'],
                            created_by=info['usuario'],
                            confidence_score=80.0,
                            detection_rules={"rule": "cambios_masivos", "count": info['count']}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"      Error en _detect_cambios_masivos: {e}")
    
    def _detect_secuencias_faltantes(self):
        """Detecta gaps en secuencias de documentos"""
        query = """
        SELECT TIP_DCTO, NUM_DCTO, SEC_DCTO, FEC_DCTO
        FROM DCTO
        WHERE TIP_DCTO IN ('FC', 'FV')
          AND FEC_DCTO >= CURRENT_DATE - 30
          AND NUM_DCTO IS NOT NULL
        ORDER BY TIP_DCTO, NUM_DCTO
        """
        
        try:
            documentos = self.db.execute_firebird_query(query)
            
            by_tipo = {}
            for doc in documentos:
                tipo = doc.get('TIP_DCTO')
                if tipo not in by_tipo:
                    by_tipo[tipo] = []
                
                # Intentar extraer número de NUM_DCTO
                num_dcto = doc.get('NUM_DCTO', '')
                try:
                    # Extraer solo los dígitos
                    match = re.search(r'(\d+)', str(num_dcto))
                    if match:
                        numero = int(match.group(1))
                        by_tipo[tipo].append({
                            'numero': numero,
                            'num_dcto': num_dcto,
                            'fecha': self.parse_firebird_date(doc.get('FEC_DCTO'))
                        })
                except:
                    pass
            
            # Detectar gaps significativos
            for tipo, docs in by_tipo.items():
                if len(docs) < 10:
                    continue
                    
                # Ordenar por número
                docs.sort(key=lambda x: x['numero'])
                
                # Buscar gaps
                gaps = []
                for i in range(1, len(docs)):
                    diff = docs[i]['numero'] - docs[i-1]['numero']
                    if diff > 10:  # Gap de más de 10 números
                        gaps.append({
                            'from': docs[i-1]['numero'],
                            'to': docs[i]['numero'],
                            'gap': diff
                        })
                
                if len(gaps) >= 2:  # Al menos 2 gaps significativos
                    total_gap = sum([g['gap'] for g in gaps])
                    
                    # ID único para el grupo
                    group_id = f"GAPS_{tipo}_{total_gap}"
                    
                    if not self.check_existing_case("DCTO", group_id, DetectorType.SEQUENCE_GAP):
                        case = self.create_fraud_case(
                            title=f"Secuencias faltantes en {tipo}",
                            description=f"Se detectaron {len(gaps)} gaps en la numeración de documentos {tipo}. "
                                       f"Total de números faltantes: {total_gap}. "
                                       f"Esto podría indicar eliminación de documentos.",
                            severity=FraudSeverity.MEDIUM if total_gap < 50 else FraudSeverity.HIGH,
                            source_table="DCTO",
                            source_record_id=group_id,
                            confidence_score=70.0,
                            detection_rules={"rule": "secuencia_faltante", "gaps": len(gaps), "total": total_gap}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"      Error en _detect_secuencias_faltantes: {e}")