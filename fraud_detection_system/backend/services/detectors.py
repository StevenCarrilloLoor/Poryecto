"""
Detectores de fraude basados en reglas de negocio
backend/services/detectors.py
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
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
    """Detector de anomalías en facturas"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        # Detectar múltiples tipos de anomalías
        self._detect_montos_redondos()
        self._detect_secuencias_faltantes()
        self._detect_fuera_horario()
        self._detect_duplicados_precio_diferente()
        self._detect_descuentos_excesivos()
        
        return self.results
    
    def _detect_montos_redondos(self):
        """Detecta facturas con montos exactamente redondos repetitivos"""
        query = """
        SELECT SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO, 
               COD_CLIE, TNI_DCTO, TSI_DCTO, IVA_DCTO,
               (TNI_DCTO + TSI_DCTO + IVA_DCTO) as TOTAL,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV')
          AND d.FEC_DCTO >= DATEADD(day, -30, GETDATE())
          AND (TNI_DCTO + TSI_DCTO + IVA_DCTO) % 100 = 0
          AND (TNI_DCTO + TSI_DCTO + IVA_DCTO) > 500
        """
        
        facturas = self.db.execute_firebird_query(query)
        
        # Agrupar por cliente y contar repeticiones
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
                    title=f"Montos redondos sospechosos - Cliente {facts[0]['NOM_CLIE']}",
                    description=f"Se detectaron {len(facts)} facturas con montos exactamente redondos "
                               f"para el cliente {facts[0]['NOM_CLIE']} (RUC: {facts[0]['RUC_CLIE']}). "
                               f"Total acumulado: ${total_amount:,.2f}",
                    detector_type=DetectorType.INVOICE_ANOMALY,
                    severity=FraudSeverity.MEDIUM if len(facts) < 5 else FraudSeverity.HIGH,
                    amount=total_amount,
                    source_table="DCTO",
                    source_record_id=",".join([str(f['SEC_DCTO']) for f in facts]),
                    client_code=cliente,
                    client_name=facts[0]['NOM_CLIE'],
                    client_ruc=facts[0]['RUC_CLIE'],
                    transaction_date=facts[-1]['FEC_DCTO'],
                    confidence_score=75.0,
                    detection_rules={"rule": "montos_redondos", "count": len(facts)}
                ))
    
    def _detect_secuencias_faltantes(self):
        """Detecta gaps en secuencias de números de factura"""
        query = """
        SELECT TIP_DCTO, NUM_DCTO, FEC_DCTO, SEC_DCTO
        FROM DCTO
        WHERE TIP_DCTO IN ('FC', 'FV')
          AND FEC_DCTO >= DATEADD(day, -30, GETDATE())
          AND NUM_DCTO IS NOT NULL
        ORDER BY TIP_DCTO, CAST(NUM_DCTO AS INTEGER)
        """
        
        facturas = self.db.execute_firebird_query(query)
        
        # Analizar secuencias por tipo de documento
        by_type = {}
        for f in facturas:
            tipo = f['TIP_DCTO']
            if tipo not in by_type:
                by_type[tipo] = []
            try:
                num = int(f['NUM_DCTO'])
                by_type[tipo].append((num, f))
            except:
                continue
        
        # Detectar gaps
        for tipo, nums in by_type.items():
            nums.sort(key=lambda x: x[0])
            gaps = []
            
            for i in range(1, len(nums)):
                expected = nums[i-1][0] + 1
                actual = nums[i][0]
                
                if actual - expected > 1:
                    gaps.append({
                        'from': nums[i-1][0],
                        'to': actual,
                        'missing': actual - expected - 1
                    })
            
            if gaps and sum([g['missing'] for g in gaps]) > 5:
                total_missing = sum([g['missing'] for g in gaps])
                
                # Construir string de rangos sin comillas problemáticas
                rangos_list = []
                for g in gaps[:3]:
                    rangos_list.append(str(g['from']) + '-' + str(g['to']))
                rangos_str = ', '.join(rangos_list)
                
                self.results.append(self.create_fraud_case(
                    title=f"Secuencias faltantes en {tipo}",
                    description=f"Se detectaron {len(gaps)} gaps en la numeración de {tipo}. "
                               f"Total de números faltantes: {total_missing}. "
                               f"Rangos: {rangos_str}",
                    detector_type=DetectorType.INVOICE_ANOMALY,
                    severity=FraudSeverity.HIGH if total_missing > 20 else FraudSeverity.MEDIUM,
                    source_table="DCTO",
                    source_record_id=tipo,
                    confidence_score=90.0,
                    detection_rules={"rule": "secuencias_faltantes", "gaps": gaps[:5]}
                ))
    
    def _detect_fuera_horario(self):
        """Detecta facturas creadas fuera del horario laboral"""
        query = """
        SELECT SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO,
               COD_CLIE, COD_VEND, TNI_DCTO, TSI_DCTO, IVA_DCTO,
               c.NOM_CLIE, c.RUC_CLIE, v.NOM_VEND
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        LEFT JOIN VEND v ON d.COD_VEND = v.COD_VEND
        WHERE d.TIP_DCTO IN ('FC', 'FV', 'EB')
          AND d.FEC_DCTO >= DATEADD(day, -30, GETDATE())
          AND (DATEPART(hour, d.FEC_DCTO) < 7 OR DATEPART(hour, d.FEC_DCTO) > 20
               OR DATEPART(weekday, d.FEC_DCTO) IN (1, 7))
        """
        
        facturas = self.db.execute_firebird_query(query)
        
        if len(facturas) > 0:
            # Agrupar por vendedor
            by_vendor = {}
            for f in facturas:
                vendor = f['COD_VEND'] or 'SIN_VENDEDOR'
                if vendor not in by_vendor:
                    by_vendor[vendor] = []
                by_vendor[vendor].append(f)
            
            for vendor, facts in by_vendor.items():
                if len(facts) >= 2:  # Al menos 2 transacciones fuera de horario
                    total = sum([f['TNI_DCTO'] + f['TSI_DCTO'] + f['IVA_DCTO'] for f in facts])
                    
                    self.results.append(self.create_fraud_case(
                        title=f"Transacciones fuera de horario - {facts[0]['NOM_VEND'] or vendor}",
                        description=f"Se detectaron {len(facts)} transacciones fuera del horario laboral "
                                   f"(7am-8pm L-V). Vendedor: {facts[0]['NOM_VEND'] or 'Desconocido'}. "
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
    
    def _detect_duplicados_precio_diferente(self):
        """Detecta productos vendidos múltiples veces con precios diferentes"""
        query = """
        SELECT m.COD_ITEM, m.VAL_MOVI, m.CAN_MOVI, d.FEC_DCTO,
               d.COD_CLIE, d.SEC_DCTO, i.NOM_ITEM, c.NOM_CLIE
        FROM MOVI m
        INNER JOIN DCTO d ON m.SEC_DCTO = d.SEC_DCTO
        LEFT JOIN ITEM i ON m.COD_ITEM = i.COD_ITEM
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.FEC_DCTO >= DATEADD(day, -30, GETDATE())
          AND d.TIP_DCTO IN ('FC', 'FV')
        ORDER BY m.COD_ITEM, d.FEC_DCTO
        """
        
        movimientos = self.db.execute_firebird_query(query)
        
        # Analizar variaciones de precio por producto
        by_item = {}
        for m in movimientos:
            item = m['COD_ITEM']
            if item not in by_item:
                by_item[item] = []
            by_item[item].append(m)
        
        for item, movs in by_item.items():
            if len(movs) >= 3:
                prices = [m['VAL_MOVI'] for m in movs if m['VAL_MOVI'] > 0]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    # Si la variación es mayor al 30%
                    if max_price > min_price * 1.3:
                        self.results.append(self.create_fraud_case(
                            title=f"Variación sospechosa de precios - {movs[0]['NOM_ITEM']}",
                            description=f"El producto {movs[0]['NOM_ITEM']} (código: {item}) muestra "
                                       f"variaciones de precio significativas. Precio mínimo: ${min_price:,.2f}, "
                                       f"Precio máximo: ${max_price:,.2f} (variación: {((max_price/min_price-1)*100):.1f}%)",
                            detector_type=DetectorType.DUPLICATE_TRANSACTION,
                            severity=FraudSeverity.MEDIUM,
                            amount=Decimal(str(max_price - min_price)),
                            source_table="MOVI",
                            source_record_id=item,
                            confidence_score=70.0,
                            detection_rules={"rule": "variacion_precios", "min": min_price, "max": max_price}
                        ))
    
    def _detect_descuentos_excesivos(self):
        """Detecta descuentos excesivos en facturas"""
        query = """
        SELECT SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO,
               COD_CLIE, DSC_DCTO, TNI_DCTO, TSI_DCTO,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DCTO d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE d.TIP_DCTO IN ('FC', 'FV')
          AND d.FEC_DCTO >= DATEADD(day, -30, GETDATE())
          AND d.DSC_DCTO > 0
          AND d.TNI_DCTO > 0
          AND (d.DSC_DCTO / d.TNI_DCTO) > 0.15
        """
        
        facturas = self.db.execute_firebird_query(query)
        
        for f in facturas:
            if f['TNI_DCTO'] > 0:
                porcentaje_desc = (f['DSC_DCTO'] / f['TNI_DCTO']) * 100
                
                if porcentaje_desc > 30:  # Descuento mayor al 30%
                    self.results.append(self.create_fraud_case(
                        title=f"Descuento excesivo - Factura {f['NUM_DCTO']}",
                        description=f"Descuento del {porcentaje_desc:.1f}% detectado en factura {f['NUM_DCTO']}. "
                                   f"Cliente: {f['NOM_CLIE']} (RUC: {f['RUC_CLIE']}). "
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


class RoboDeCombustible(BaseDetector):
    """Detector de posible robo de combustible"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_consumo_anormal()
        self._detect_repostajes_excesivos()
        self._detect_patrones_sospechosos()
        
        return self.results
    
    def _detect_consumo_anormal(self):
        """Detecta consumo anormal vs capacidad del tanque"""
        query = """
        SELECT d.NUM_DESP, d.FEC_DESP, d.CAN_DESP, d.VTO_DESP,
               d.COD_PROD, d.NOM_PROD, d.COD_CLIE,
               c.NOM_CLIE, c.RUC_CLIE
        FROM DESP d
        LEFT JOIN CLIE c ON d.COD_CLIE = c.COD_CLIE
        WHERE CAST(d.FEC_DESP AS DATE) >= DATEADD(day, -30, GETDATE())
          AND d.CAN_DESP > 100
        ORDER BY d.CAN_DESP DESC
        """
        
        despachos = self.db.execute_firebird_query(query)
        
        for d in despachos:
            # Si el despacho supera 200 galones (sospechoso para vehículos normales)
            if d['CAN_DESP'] > 200:
                self.results.append(self.create_fraud_case(
                    title=f"Despacho excesivo de combustible - {d['CAN_DESP']:.1f} galones",
                    description=f"Despacho anormal de {d['CAN_DESP']:.1f} galones detectado. "
                               f"Cliente: {d['NOM_CLIE'] or 'Desconocido'}. "
                               f"Producto: {d['NOM_PROD']}. Valor: ${d['VTO_DESP']:,.2f}",
                    detector_type=DetectorType.FUEL_THEFT,
                    severity=FraudSeverity.HIGH,
                    amount=d['VTO_DESP'],
                    source_table="DESP",
                    source_record_id=str(d['NUM_DESP']),
                    client_code=d['COD_CLIE'],
                    client_name=d['NOM_CLIE'],
                    client_ruc=d['RUC_CLIE'],
                    transaction_date=d['FEC_DESP'],
                    confidence_score=85.0,
                    detection_rules={"rule": "consumo_excesivo", "cantidad": d['CAN_DESP']}
                ))
    
    def _detect_repostajes_excesivos(self):
        """Detecta múltiples repostajes en corto tiempo"""
        query = """
        SELECT COD_CLIE, COUNT(*) as NUM_DESPACHOS,
               SUM(CAN_DESP) as TOTAL_GALONES,
               SUM(VTO_DESP) as TOTAL_VALOR,
               MIN(FEC_DESP) as PRIMERA,
               MAX(FEC_DESP) as ULTIMA
        FROM DESP
        WHERE CAST(FEC_DESP AS DATE) = CAST(GETDATE() AS DATE)
        GROUP BY COD_CLIE
        HAVING COUNT(*) > 3
        """
        
        repetidos = self.db.execute_firebird_query(query)
        
        for r in repetidos:
            if r['NUM_DESPACHOS'] > 3:
                # Obtener info del cliente
                cliente_query = f"SELECT NOM_CLIE, RUC_CLIE FROM CLIE WHERE COD_CLIE = '{r['COD_CLIE']}'"
                cliente_info = self.db.execute_firebird_query(cliente_query)
                
                nombre_cliente = cliente_info[0]['NOM_CLIE'] if cliente_info else 'Desconocido'
                
                self.results.append(self.create_fraud_case(
                    title=f"Múltiples repostajes mismo día - {nombre_cliente}",
                    description=f"Cliente {nombre_cliente} realizó {r['NUM_DESPACHOS']} despachos "
                               f"en el mismo día. Total: {r['TOTAL_GALONES']:.1f} galones, "
                               f"${r['TOTAL_VALOR']:,.2f}",
                    detector_type=DetectorType.FUEL_THEFT,
                    severity=FraudSeverity.HIGH if r['NUM_DESPACHOS'] > 5 else FraudSeverity.MEDIUM,
                    amount=r['TOTAL_VALOR'],
                    source_table="DESP",
                    client_code=r['COD_CLIE'],
                    client_name=nombre_cliente,
                    confidence_score=90.0,
                    detection_rules={"rule": "repostajes_multiples", "count": r['NUM_DESPACHOS']}
                ))
    
    def _detect_patrones_sospechosos(self):
        """Detecta patrones sospechosos en tanques"""
        query = """
        SELECT t.COD_TANQ, t.NOM_TANQ, tm.FEC_TQMV,
               tm.SCO_TQMV, tm.SAG_TQMV,
               tm.SCO_GAL_TQMV, tm.SAG_GAL_TQMV
        FROM TANQ_MOV tm
        INNER JOIN TANQ t ON tm.COD_TANQ = t.COD_TANQ
        WHERE tm.FEC_TQMV >= DATEADD(day, -7, GETDATE())
        ORDER BY t.COD_TANQ, tm.FEC_TQMV
        """
        
        movimientos = self.db.execute_firebird_query(query)
        
        # Analizar diferencias por tanque
        by_tanque = {}
        for m in movimientos:
            tanque = m['COD_TANQ']
            if tanque not in by_tanque:
                by_tanque[tanque] = []
            by_tanque[tanque].append(m)
        
        for tanque, movs in by_tanque.items():
            if len(movs) >= 2:
                for i in range(1, len(movs)):
                    diff_gal = movs[i-1]['SAG_GAL_TQMV'] - movs[i]['SCO_GAL_TQMV']
                    
                    # Si hay diferencia mayor a 50 galones
                    if abs(diff_gal) > 50:
                        self.results.append(self.create_fraud_case(
                            title=f"Diferencia sospechosa en tanque {movs[i]['NOM_TANQ']}",
                            description=f"Diferencia de {abs(diff_gal):.1f} galones detectada en tanque "
                                       f"{movs[i]['NOM_TANQ']}. Esto podría indicar robo o fuga.",
                            detector_type=DetectorType.FUEL_THEFT,
                            severity=FraudSeverity.CRITICAL if abs(diff_gal) > 100 else FraudSeverity.HIGH,
                            amount=Decimal(str(abs(diff_gal) * 4.5)),  # Estimado a $4.5/galón
                            source_table="TANQ_MOV",
                            source_record_id=tanque,
                            transaction_date=movs[i]['FEC_TQMV'],
                            confidence_score=95.0,
                            detection_rules={"rule": "diferencia_tanque", "diferencia": diff_gal}
                        ))


class ManipulacionDatos(BaseDetector):
    """Detector de manipulación de datos"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_cambios_masivos()
        self._detect_eliminaciones_sospechosas()
        
        return self.results
    
    def _detect_cambios_masivos(self):
        """Detecta cambios masivos de registros"""
        query = """
        SELECT COD_XUSUA, FEC_XDCTO, COUNT(*) as NUM_CAMBIOS
        FROM XDCTO
        WHERE FEC_XDCTO >= DATEADD(day, -7, GETDATE())
        GROUP BY COD_XUSUA, CAST(FEC_XDCTO AS DATE)
        HAVING COUNT(*) > 20
        """
        
        cambios = self.db.execute_firebird_query(query)
        
        for c in cambios:
            self.results.append(self.create_fraud_case(
                title=f"Cambios masivos detectados - Usuario {c['COD_XUSUA']}",
                description=f"El usuario {c['COD_XUSUA']} realizó {c['NUM_CAMBIOS']} "
                           f"modificaciones en un día. Esto requiere revisión.",
                detector_type=DetectorType.DATA_MANIPULATION,
                severity=FraudSeverity.HIGH if c['NUM_CAMBIOS'] > 50 else FraudSeverity.MEDIUM,
                source_table="XDCTO",
                created_by=c['COD_XUSUA'],
                confidence_score=80.0,
                detection_rules={"rule": "cambios_masivos", "count": c['NUM_CAMBIOS']}
            ))
    
    def _detect_eliminaciones_sospechosas(self):
        """Detecta eliminaciones fuera de horario"""
        query = """
        SELECT COD_XUSUA, FEC_XDCTO, MEL_XDCTO, NUM_XDCTO
        FROM XDCTO
        WHERE MEL_XDCTO = 'E'
          AND FEC_XDCTO >= DATEADD(day, -30, GETDATE())
          AND (DATEPART(hour, FEC_XDCTO) < 7 OR DATEPART(hour, FEC_XDCTO) > 20)
        """
        
        eliminaciones = self.db.execute_firebird_query(query)
        
        if len(eliminaciones) > 0:
            by_user = {}
            for e in eliminaciones:
                user = e['COD_XUSUA']
                if user not in by_user:
                    by_user[user] = []
                by_user[user].append(e)
            
            for user, elims in by_user.items():
                if len(elims) >= 2:
                    self.results.append(self.create_fraud_case(
                        title=f"Eliminaciones fuera de horario - {user}",
                        description=f"Se detectaron {len(elims)} eliminaciones fuera del horario "
                                   f"laboral por el usuario {user}.",
                        detector_type=DetectorType.DATA_MANIPULATION,
                        severity=FraudSeverity.HIGH,
                        source_table="XDCTO",
                        created_by=user,
                        confidence_score=85.0,
                        detection_rules={"rule": "eliminaciones_fuera_horario", "count": len(elims)}
                    ))