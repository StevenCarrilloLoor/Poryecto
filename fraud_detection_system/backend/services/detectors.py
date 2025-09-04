# backend/services/detectors_fixed.py
"""
Detectores de fraude corregidos para Firebird
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal
import json

from database.db_context import db_context
from models.fraud_models import DetectorType, FraudSeverity

class BaseDetector:
    """Clase base para todos los detectores de fraude"""
    
    def __init__(self):
        self.db = db_context
        self.results = []
        
    def detect(self) -> List[Dict[str, Any]]:
        """Método abstracto que debe ser implementado por cada detector"""
        raise NotImplementedError
    
    def create_fraud_case(self, 
                         title: str,
                         description: str,
                         detector_type: DetectorType,
                         severity: FraudSeverity,
                         amount: Decimal = None,
                         source_table: str = None,
                         source_record_id: str = None,
                         client_code: str = None,
                         client_name: str = None,
                         client_ruc: str = None,
                         transaction_date: datetime = None,
                         confidence_score: float = None,
                         detection_rules: Dict = None) -> Dict:
        """Crea un caso de fraude con los parámetros dados"""
        
        return {
            "title": title,
            "description": description,
            "detector_type": detector_type,
            "severity": severity,
            "amount": amount,
            "source_table": source_table,
            "source_record_id": source_record_id,
            "client_code": client_code,
            "client_name": client_name,
            "client_ruc": client_ruc,
            "transaction_date": transaction_date,
            "confidence_score": confidence_score,
            "detection_rules": json.dumps(detection_rules) if detection_rules else None,
            "created_by": "SYSTEM"
        }

class FacturasAnomalias(BaseDetector):
    """Detector de anomalías en facturas - Versión Firebird"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_montos_redondos()
        self._detect_descuentos_excesivos()
        self._detect_fuera_horario()
        
        return self.results
    
    def _detect_montos_redondos(self):
        """Detecta facturas con montos exactamente redondos repetitivos"""
        # Query corregida para Firebird
        query = """
        SELECT d.SEC_DCTO, d.TIP_DCTO, d.NUM_DCTO, d.FEC_DCTO, 
               d.COD_CLIE, d.TNI_DCTO, d.TSI_DCTO, d.IVA_DCTO,
               (d.TNI_DCTO + d.TSI_DCTO + d.IVA_DCTO) as TOTAL,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV')
          AND d.FEC_DCTO >= CURRENT_DATE - 30
          AND MOD(d.TNI_DCTO + d.TSI_DCTO + d.IVA_DCTO, 100) = 0
          AND (d.TNI_DCTO + d.TSI_DCTO + d.IVA_DCTO) > 500
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            # Agrupar por cliente
            cliente_montos = {}
            for f in facturas:
                key = f['COD_CLIE']
                if key not in cliente_montos:
                    cliente_montos[key] = []
                cliente_montos[key].append(f)
            
            # Detectar clientes con múltiples montos redondos
            for cliente, facts in cliente_montos.items():
                if len(facts) >= 3:  # 3 o más facturas redondas
                    total_amount = sum([f['TOTAL'] for f in facts])
                    
                    self.results.append(self.create_fraud_case(
                        title=f"Montos redondos sospechosos - Cliente {facts[0]['NOM_CLIE'] or cliente}",
                        description=f"Se detectaron {len(facts)} facturas con montos exactamente redondos "
                                   f"para el cliente {facts[0]['NOM_CLIE'] or 'Desconocido'}. "
                                   f"Total acumulado: ${total_amount:,.2f}",
                        detector_type=DetectorType.ROUND_AMOUNT,
                        severity=FraudSeverity.MEDIUM if len(facts) < 5 else FraudSeverity.HIGH,
                        amount=total_amount,
                        source_table="DCTO",
                        source_record_id=",".join([str(f['SEC_DCTO']) for f in facts[:10]]),
                        client_code=cliente,
                        client_name=facts[0]['NOM_CLIE'],
                        client_ruc=facts[0]['RUC_CLIE'],
                        transaction_date=facts[-1]['FEC_DCTO'],
                        confidence_score=75.0,
                        detection_rules={"rule": "montos_redondos", "count": len(facts)}
                    ))
                    
        except Exception as e:
            print(f"  Error en _detect_montos_redondos: {e}")
    
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
          AND d.DSC_DCTO > 0
          AND d.TNI_DCTO > 0
          AND (d.DSC_DCTO * 1.0 / d.TNI_DCTO) > 0.15
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            for f in facturas:
                if f['TNI_DCTO'] and f['TNI_DCTO'] > 0:
                    porcentaje_desc = (f['DSC_DCTO'] / f['TNI_DCTO']) * 100
                    
                    if porcentaje_desc > 30:  # Descuento mayor al 30%
                        self.results.append(self.create_fraud_case(
                            title=f"Descuento excesivo - Factura {f['NUM_DCTO']}",
                            description=f"Descuento del {porcentaje_desc:.1f}% detectado en factura {f['NUM_DCTO']}. "
                                       f"Cliente: {f['NOM_CLIE'] or 'Desconocido'}. "
                                       f"Monto original: ${f['TNI_DCTO']:,.2f}, Descuento: ${f['DSC_DCTO']:,.2f}",
                            detector_type=DetectorType.EXCESSIVE_DISCOUNT,
                            severity=FraudSeverity.HIGH if porcentaje_desc > 50 else FraudSeverity.MEDIUM,
                            amount=f['DSC_DCTO'],
                            source_table="DCTO",
                            source_record_id=str(f['SEC_DCTO']),
                            client_code=f['COD_CLIE'],
                            client_name=f['NOM_CLIE'],
                            client_ruc=f['RUC_CLIE'],
                            transaction_date=f['FEC_DCTO'],
                            confidence_score=85.0,
                            detection_rules={"rule": "descuento_excesivo", "porcentaje": porcentaje_desc}
                        ))
                        
        except Exception as e:
            print(f"  Error en _detect_descuentos_excesivos: {e}")
    
    def _detect_fuera_horario(self):
        """Detecta facturas creadas fuera del horario laboral"""
        # En Firebird usamos EXTRACT para obtener hora y día
        query = """
        SELECT d.SEC_DCTO, d.TIP_DCTO, d.NUM_DCTO, d.FEC_DCTO,
               d.COD_CLIE, d.COD_VEND, d.TNI_DCTO, d.TSI_DCTO, d.IVA_DCTO,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV', 'EB')
          AND d.FEC_DCTO >= CURRENT_DATE - 30
          AND (
              EXTRACT(HOUR FROM d.FEC_DCTO) < 7 
              OR EXTRACT(HOUR FROM d.FEC_DCTO) > 20
              OR EXTRACT(WEEKDAY FROM d.FEC_DCTO) IN (0, 6)
          )
        """
        
        try:
            facturas = self.db.execute_firebird_query(query)
            
            if len(facturas) > 0:
                # Agrupar por vendedor o cliente
                by_client = {}
                for f in facturas:
                    client = f['COD_CLIE'] or 'SIN_CLIENTE'
                    if client not in by_client:
                        by_client[client] = []
                    by_client[client].append(f)
                
                for client, facts in by_client.items():
                    if len(facts) >= 2:  # Al menos 2 transacciones fuera de horario
                        total = sum([(f.get('TNI_DCTO', 0) or 0) + 
                                   (f.get('TSI_DCTO', 0) or 0) + 
                                   (f.get('IVA_DCTO', 0) or 0) for f in facts])
                        
                        self.results.append(self.create_fraud_case(
                            title=f"Transacciones fuera de horario - {facts[0].get('NOM_CLIE', client)}",
                            description=f"Se detectaron {len(facts)} transacciones fuera del horario laboral "
                                       f"(7am-8pm L-V). Cliente: {facts[0].get('NOM_CLIE', 'Desconocido')}. "
                                       f"Total: ${total:,.2f}",
                            detector_type=DetectorType.AFTERHOURS,
                            severity=FraudSeverity.MEDIUM if len(facts) < 5 else FraudSeverity.HIGH,
                            amount=total,
                            source_table="DCTO",
                            source_record_id=",".join([str(f['SEC_DCTO']) for f in facts[:10]]),
                            transaction_date=facts[-1]['FEC_DCTO'],
                            confidence_score=80.0,
                            detection_rules={"rule": "fuera_horario", "count": len(facts)}
                        ))
                        
        except Exception as e:
            print(f"  Error en _detect_fuera_horario: {e}")


class RoboDeCombustible(BaseDetector):
    """Detector de posible robo de combustible - Versión Firebird"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_consumo_anormal()
        self._detect_repostajes_excesivos()
        
        return self.results
    
    def _detect_consumo_anormal(self):
        """Detecta consumo anormal vs capacidad del tanque"""
        query = """
        SELECT d.NUM_DESP, d.FEC_DESP, d.CAN_DESP, d.VTO_DESP,
               d.COD_PROD, d.NOM_PROD, d.COD_CLIE,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DESP d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.FEC_DESP >= CURRENT_DATE - 30
          AND d.CAN_DESP > 100
        ORDER BY d.CAN_DESP DESC
        """
        
        try:
            despachos = self.db.execute_firebird_query(query)
            
            for d in despachos:
                # Si el despacho supera 200 galones
                if d.get('CAN_DESP', 0) > 200:
                    self.results.append(self.create_fraud_case(
                        title=f"Despacho excesivo de combustible - {d['CAN_DESP']:.1f} galones",
                        description=f"Despacho anormal de {d['CAN_DESP']:.1f} galones detectado. "
                                   f"Cliente: {d.get('NOM_CLIE', 'Desconocido')}. "
                                   f"Producto: {d.get('NOM_PROD', 'N/A')}. Valor: ${d.get('VTO_DESP', 0):,.2f}",
                        detector_type=DetectorType.FUEL_THEFT,
                        severity=FraudSeverity.HIGH,
                        amount=d.get('VTO_DESP', 0),
                        source_table="DESP",
                        source_record_id=str(d.get('NUM_DESP', '')),
                        client_code=d.get('COD_CLIE'),
                        client_name=d.get('NOM_CLIE'),
                        client_ruc=d.get('RUC_CLIE'),
                        transaction_date=d.get('FEC_DESP'),
                        confidence_score=85.0,
                        detection_rules={"rule": "consumo_excesivo", "cantidad": d.get('CAN_DESP', 0)}
                    ))
                    
        except Exception as e:
            print(f"  Error en _detect_consumo_anormal: {e}")
    
    def _detect_repostajes_excesivos(self):
        """Detecta múltiples repostajes en corto tiempo"""
        # Para Firebird, comparamos fechas directamente
        query = """
        SELECT COD_CLIE, COUNT(*) as NUM_DESPACHOS,
               SUM(CAN_DESP) as TOTAL_GALONES,
               SUM(VTO_DESP) as TOTAL_VALOR,
               MIN(FEC_DESP) as PRIMERA,
               MAX(FEC_DESP) as ULTIMA
        FROM DESP
        WHERE FEC_DESP >= CURRENT_DATE
        GROUP BY COD_CLIE
        HAVING COUNT(*) > 3
        """
        
        try:
            repetidos = self.db.execute_firebird_query(query)
            
            for r in repetidos:
                if r['NUM_DESPACHOS'] > 3:
                    # Obtener info del cliente
                    cliente_query = f"SELECT NOM_CLIE, RUC_CLIE FROM CLIE WHERE COD_CLIE = '{r['COD_CLIE']}'"
                    try:
                        cliente_info = self.db.execute_firebird_query(cliente_query)
                        nombre_cliente = cliente_info[0]['NOM_CLIE'] if cliente_info else 'Desconocido'
                    except:
                        nombre_cliente = 'Desconocido'
                    
                    self.results.append(self.create_fraud_case(
                        title=f"Múltiples repostajes mismo día - {nombre_cliente}",
                        description=f"Cliente {nombre_cliente} realizó {r['NUM_DESPACHOS']} despachos "
                                   f"en el mismo día. Total: {r.get('TOTAL_GALONES', 0):.1f} galones, "
                                   f"${r.get('TOTAL_VALOR', 0):,.2f}",
                        detector_type=DetectorType.FUEL_THEFT,
                        severity=FraudSeverity.HIGH if r['NUM_DESPACHOS'] > 5 else FraudSeverity.MEDIUM,
                        amount=r.get('TOTAL_VALOR', 0),
                        source_table="DESP",
                        client_code=r['COD_CLIE'],
                        client_name=nombre_cliente,
                        confidence_score=90.0,
                        detection_rules={"rule": "repostajes_multiples", "count": r['NUM_DESPACHOS']}
                    ))
                    
        except Exception as e:
            print(f"  Error en _detect_repostajes_excesivos: {e}")


class ManipulacionDatos(BaseDetector):
    """Detector de manipulación de datos - Versión Firebird"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_cambios_masivos()
        
        return self.results
    
    def _detect_cambios_masivos(self):
        """Detecta cambios masivos de registros"""
        query = """
        SELECT COD_XUSUA, CAST(FEC_XDCTO AS DATE) as FECHA, COUNT(*) as NUM_CAMBIOS
        FROM XDCTO
        WHERE FEC_XDCTO >= CURRENT_DATE - 7
        GROUP BY COD_XUSUA, CAST(FEC_XDCTO AS DATE)
        HAVING COUNT(*) > 20
        """
        
        try:
            cambios = self.db.execute_firebird_query(query)
            
            for c in cambios:
                if c.get('NUM_CAMBIOS', 0) > 20:
                    self.results.append(self.create_fraud_case(
                        title=f"Cambios masivos detectados - Usuario {c.get('COD_XUSUA', 'DESCONOCIDO')}",
                        description=f"El usuario {c.get('COD_XUSUA', 'DESCONOCIDO')} realizó {c.get('NUM_CAMBIOS', 0)} "
                                   f"modificaciones en un día. Esto requiere revisión.",
                        detector_type=DetectorType.DATA_MANIPULATION,
                        severity=FraudSeverity.HIGH if c.get('NUM_CAMBIOS', 0) > 50 else FraudSeverity.MEDIUM,
                        source_table="XDCTO",
                        created_by=c.get('COD_XUSUA', 'SYSTEM'),
                        confidence_score=80.0,
                        detection_rules={"rule": "cambios_masivos", "count": c.get('NUM_CAMBIOS', 0)}
                    ))
                    
        except Exception as e:
            print(f"  Error en _detect_cambios_masivos: {e}")