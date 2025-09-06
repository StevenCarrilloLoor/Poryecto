"""
Detector de anomalías en facturas
backend/services/detectors/invoice_anomaly_detector.py
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from .base_detector import BaseDetector
from models.fraud_models import DetectorType, FraudSeverity


class InvoiceAnomalyDetector(BaseDetector):
    """Detector especializado en anomalías de facturas"""
    
    detector_type = DetectorType.INVOICE_ANOMALY
    detector_name = "Detector de Anomalías en Facturas"
    detector_description = "Detecta patrones anómalos en facturas: montos redondos, descuentos excesivos, transacciones fuera de horario"
    enabled_by_default = True
    
    def detect(self) -> List[Dict[str, Any]]:
        """Ejecuta todas las detecciones de anomalías en facturas"""
        self.results = []
        self.log_detection_start()
        
        try:
            self._detect_montos_redondos()
            self._detect_descuentos_excesivos()
            self._detect_fuera_horario()
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
            "round_amount_min": 500,
            "round_amount_count": 3,
            "excessive_discount_percent": 30,
            "afterhours_start": 7,
            "afterhours_end": 20
        }
        return info
    
    def get_detection_rules(self) -> List[str]:
        """Reglas que aplica este detector"""
        return [
            "Montos redondos repetitivos (múltiplos de 100)",
            "Descuentos superiores al 30%",
            "Facturas fuera del horario laboral (7am-8pm)",
            "Facturas en fines de semana",
            "Múltiples facturas redondas del mismo cliente"
        ]
    
    def _detect_montos_redondos(self):
        """Detecta facturas con montos exactamente redondos repetitivos"""
        query = """
        SELECT d.SEC_DCTO, d.TIP_DCTO, d.NUM_DCTO, d.FEC_DCTO, 
               d.COD_CLIE, d.TNI_DCTO, d.TSI_DCTO, d.IVA_DCTO,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV')
          AND d.FEC_DCTO >= CURRENT_DATE - 30
          AND d.TNI_DCTO IS NOT NULL
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            cliente_montos = {}
            for f in facturas:
                total = self.safe_float(f.get('TNI_DCTO', 0)) + \
                        self.safe_float(f.get('TSI_DCTO', 0)) + \
                        self.safe_float(f.get('IVA_DCTO', 0))
                
                # Verificar si es monto redondo (múltiplo de 100) y mayor a 500
                if total > 500 and total % 100 == 0:
                    key = f.get('COD_CLIE', 'UNKNOWN')
                    if key not in cliente_montos:
                        cliente_montos[key] = []
                    f['TOTAL_CALC'] = total
                    cliente_montos[key].append(f)
            
            # Detectar clientes con múltiples montos redondos
            for cliente, facts in cliente_montos.items():
                if len(facts) >= 3:  # 3 o más facturas redondas
                    # ID único para el grupo
                    group_id = f"ROUND_{cliente}_{len(facts)}"
                    
                    if not self.check_existing_case("DCTO", group_id, DetectorType.ROUND_AMOUNT):
                        total_amount = sum([f['TOTAL_CALC'] for f in facts])
                        
                        case = self.create_fraud_case(
                            title=f"Montos redondos sospechosos - Cliente {facts[0].get('NOM_CLIE', cliente)}",
                            description=f"Se detectaron {len(facts)} facturas con montos exactamente redondos "
                                       f"para el cliente {facts[0].get('NOM_CLIE', 'Desconocido')}. "
                                       f"Total acumulado: ${total_amount:,.2f}",
                            severity=FraudSeverity.MEDIUM if len(facts) < 5 else FraudSeverity.HIGH,
                            amount=total_amount,
                            source_table="DCTO",
                            source_record_id=group_id,
                            client_code=cliente,
                            client_name=facts[0].get('NOM_CLIE'),
                            client_ruc=facts[0].get('RUC_CLIE'),
                            transaction_date=facts[-1].get('FEC_DCTO'),
                            confidence_score=75.0,
                            detection_rules={"rule": "montos_redondos", "count": len(facts)}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"    Error en _detect_montos_redondos: {e}")
    
    def _detect_descuentos_excesivos(self):
        """Detecta descuentos excesivos en facturas"""
        query = """
        SELECT d.SEC_DCTO, d.TIP_DCTO, d.NUM_DCTO, d.FEC_DCTO,
               d.COD_CLIE, d.DSC_DCTO, d.TNI_DCTO, d.TSI_DCTO,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV')
          AND d.FEC_DCTO >= CURRENT_DATE - 30
          AND d.DSC_DCTO IS NOT NULL
          AND d.TNI_DCTO IS NOT NULL
          AND d.DSC_DCTO > 0
          AND d.TNI_DCTO > 0
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            for f in facturas:
                descuento = self.safe_float(f.get('DSC_DCTO', 0))
                total_neto = self.safe_float(f.get('TNI_DCTO', 0))
                
                if descuento > 0 and total_neto > 0:
                    porcentaje_desc = self.safe_divide(descuento, total_neto, 0) * 100
                    
                    if porcentaje_desc > 30:  # Descuento mayor al 30%
                        case = self.create_fraud_case(
                            title=f"Descuento excesivo - Factura {f.get('NUM_DCTO', 'N/A')}",
                            description=f"Descuento del {porcentaje_desc:.1f}% detectado en factura {f.get('NUM_DCTO', 'N/A')}. "
                                       f"Cliente: {f.get('NOM_CLIE', 'Desconocido')}. "
                                       f"Monto original: ${total_neto:,.2f}, Descuento: ${descuento:,.2f}",
                            severity=FraudSeverity.HIGH if porcentaje_desc > 50 else FraudSeverity.MEDIUM,
                            amount=descuento,
                            source_table="DCTO",
                            source_record_id=str(f.get('SEC_DCTO')),
                            client_code=f.get('COD_CLIE'),
                            client_name=f.get('NOM_CLIE'),
                            client_ruc=f.get('RUC_CLIE'),
                            transaction_date=f.get('FEC_DCTO'),
                            confidence_score=85.0,
                            detection_rules={"rule": "descuento_excesivo", "porcentaje": porcentaje_desc}
                        )
                        
                        if case:
                            self.results.append(case)
                        
        except Exception as e:
            print(f"    Error en _detect_descuentos_excesivos: {e}")
    
    def _detect_fuera_horario(self):
        """Detecta facturas creadas fuera del horario laboral"""
        query = """
        SELECT d.SEC_DCTO, d.TIP_DCTO, d.NUM_DCTO, d.FEC_DCTO,
               d.COD_CLIE, d.COD_VEND, d.TNI_DCTO, d.TSI_DCTO, d.IVA_DCTO,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV', 'EB')
          AND d.FEC_DCTO >= CURRENT_DATE - 30
          AND d.FEC_DCTO IS NOT NULL
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            fuera_horario = []
            for f in facturas:
                fecha = self.parse_firebird_date(f.get('FEC_DCTO'))
                if fecha:
                    hora = fecha.hour
                    dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
                    
                    # Fuera de horario: antes de 7am, después de 8pm, o fin de semana
                    if hora < 7 or hora > 20 or dia_semana in [5, 6]:
                        fuera_horario.append(f)
            
            # Agrupar por cliente
            by_client = {}
            for f in fuera_horario:
                client = f.get('COD_CLIE', 'SIN_CLIENTE')
                if client not in by_client:
                    by_client[client] = []
                by_client[client].append(f)
            
            for client, facts in by_client.items():
                if len(facts) >= 2:  # Al menos 2 transacciones fuera de horario
                    # ID único para el grupo
                    group_id = f"AFTERHOURS_{client}_{len(facts)}"
                    
                    if not self.check_existing_case("DCTO", group_id, DetectorType.AFTERHOURS):
                        total = sum([
                            self.safe_float(f.get('TNI_DCTO', 0)) + 
                            self.safe_float(f.get('TSI_DCTO', 0)) + 
                            self.safe_float(f.get('IVA_DCTO', 0)) 
                            for f in facts
                        ])
                        
                        case = self.create_fraud_case(
                            title=f"Transacciones fuera de horario - {facts[0].get('NOM_CLIE', client)}",
                            description=f"Se detectaron {len(facts)} transacciones fuera del horario laboral "
                                       f"(7am-8pm L-V). Cliente: {facts[0].get('NOM_CLIE', 'Desconocido')}. "
                                       f"Total: ${total:,.2f}",
                            severity=FraudSeverity.MEDIUM if len(facts) < 5 else FraudSeverity.HIGH,
                            amount=total,
                            source_table="DCTO",
                            source_record_id=group_id,
                            client_code=client,
                            client_name=facts[0].get('NOM_CLIE'),
                            transaction_date=facts[-1].get('FEC_DCTO'),
                            confidence_score=80.0,
                            detection_rules={"rule": "fuera_horario", "count": len(facts)}
                        )
                        
                        if case:
                            self.results.append(case)
                        
        except Exception as e:
            print(f"    Error en _detect_fuera_horario: {e}")