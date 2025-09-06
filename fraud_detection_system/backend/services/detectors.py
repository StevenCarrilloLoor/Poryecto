"""
Detectores de fraude con corrección de fechas Firebird y prevención de duplicados
"""

from datetime import datetime, timedelta, date
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
    
    def check_existing_case(self, source_table: str, source_record_id: str, detector_type: DetectorType) -> bool:
        """Verifica si ya existe un caso para este registro"""
        try:
            with self.db.get_session() as session:
                from models.fraud_models import FraudCase
                existing = session.query(FraudCase).filter(
                    FraudCase.source_table == source_table,
                    FraudCase.source_record_id == str(source_record_id),
                    FraudCase.detector_type == detector_type
                ).first()
                return existing is not None
        except:
            return False
    
    def parse_firebird_date(self, date_value):
        """Convierte fecha de Firebird a datetime de Python - VERSIÓN CORREGIDA"""
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
            # IMPORTANTE: Limpiar espacios extras que vienen de Firebird
            date_str = date_value.strip()
            
            # Si tiene más de 19 caracteres, truncar (para manejar espacios al final)
            if len(date_str) > 19:
                date_str = date_str[:19]
            
            # Manejar formato con hora de un solo dígito
            import re
            match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_str)
            if match:
                date_part = match.group(1)
                hour = match.group(2).zfill(2)  # Agregar 0 si es necesario
                minute = match.group(3)
                second = match.group(4)
                date_str = f"{date_part} {hour}:{minute}:{second}"
            
            # Intentar varios formatos comunes
            formats = [
                '%d/%m/%Y %H:%M:%S',      # 26/03/2025 06:08:42
                '%Y-%m-%d %H:%M:%S',       # 2025-03-26 06:08:42
                '%d/%m/%Y',                # 26/03/2025
                '%Y-%m-%d',                # 2025-03-26
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        
        return None
    
    def safe_float(self, value, default=0.0):
        """Convierte valor a float de forma segura"""
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default
    
    def safe_divide(self, numerator, denominator, default=0.0):
        """División segura que evita división por cero"""
        num = self.safe_float(numerator)
        den = self.safe_float(denominator)
        
        if den == 0:
            return default
        return num / den
    
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
        """Crea un caso de fraude con verificación de duplicados"""
        
        # VERIFICAR DUPLICADOS ANTES DE CREAR
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

class FacturasAnomalias(BaseDetector):
    """Detector de anomalías en facturas"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_montos_redondos()
        self._detect_descuentos_excesivos()
        self._detect_fuera_horario()
        
        # Filtrar None (casos duplicados)
        self.results = [r for r in self.results if r is not None]
        
        return self.results
    
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
                            detector_type=DetectorType.ROUND_AMOUNT,
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
                            detector_type=DetectorType.EXCESSIVE_DISCOUNT,
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
            print(f"  Error en _detect_descuentos_excesivos: {e}")
    
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
                            detector_type=DetectorType.AFTERHOURS,
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
            print(f"  Error en _detect_fuera_horario: {e}")

class RoboDeCombustible(BaseDetector):
    """Detector de posible robo de combustible"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        print("  Detectando consumo anormal...")
        self._detect_consumo_anormal()
        
        print("  Detectando repostajes excesivos...")
        self._detect_repostajes_excesivos()
        
        # Filtrar None (casos duplicados)
        self.results = [r for r in self.results if r is not None]
        
        return self.results
    
    def _detect_consumo_anormal(self):
        """Detecta consumo anormal vs capacidad del tanque"""
        query = """
        SELECT 
            NUM_DESP, FEC_DESP, CAN_DESP, VTO_DESP,
            COD_PROD, NOM_PROD, COD_CLIE
        FROM DESP
        WHERE CAN_DESP > 150
        """
        
        try:
            despachos = self.db.execute_firebird_query(query, fetch_size=300)
            print(f"    Despachos encontrados: {len(despachos)}")
            
            # Obtener nombres de clientes
            clientes = {}
            cliente_query = "SELECT COD_CLIE, NOM_CLIE, RUC_CLIE FROM CLIE"
            try:
                cliente_data = self.db.execute_firebird_query(cliente_query, fetch_size=5000)
                for c in cliente_data:
                    if c.get('COD_CLIE'):
                        clientes[c['COD_CLIE']] = {
                            'nombre': c.get('NOM_CLIE'),
                            'ruc': c.get('RUC_CLIE')
                        }
            except:
                pass
            
            for d in despachos:
                cantidad = self.safe_float(d.get('CAN_DESP', 0))
                
                if cantidad > 200:
                    cod_cliente = d.get('COD_CLIE')
                    cliente_info = clientes.get(cod_cliente, {})
                    fecha_desp = self.parse_firebird_date(d.get('FEC_DESP'))
                    
                    case = self.create_fraud_case(
                        title=f"Despacho excesivo de combustible - {cantidad:.1f} galones",
                        description=f"Despacho anormal de {cantidad:.1f} galones detectado. "
                                   f"Cliente: {cliente_info.get('nombre', cod_cliente or 'Desconocido')}. "
                                   f"Producto: {d.get('NOM_PROD', 'N/A')}. "
                                   f"Valor: ${self.safe_float(d.get('VTO_DESP', 0)):,.2f}",
                        detector_type=DetectorType.FUEL_THEFT,
                        severity=FraudSeverity.HIGH if cantidad > 300 else FraudSeverity.MEDIUM,
                        amount=d.get('VTO_DESP'),
                        source_table="DESP",
                        source_record_id=str(d.get('NUM_DESP', '')),
                        client_code=cod_cliente,
                        client_name=cliente_info.get('nombre'),
                        client_ruc=cliente_info.get('ruc'),
                        transaction_date=fecha_desp,
                        confidence_score=85.0,
                        detection_rules={"rule": "consumo_excesivo", "cantidad": cantidad}
                    )
                    
                    if case:
                        self.results.append(case)
                    
        except Exception as e:
            print(f"    Error en _detect_consumo_anormal: {e}")
    
    def _detect_repostajes_excesivos(self):
        """Detecta múltiples repostajes en el mismo día - CORREGIDO"""
        # Query simplificada para evitar el error de conversión
        query = """
        SELECT 
            COD_CLIE, CAN_DESP, VTO_DESP, NUM_DESP
        FROM DESP
        WHERE COD_CLIE IS NOT NULL
        """
        
        try:
            # Traer despachos sin filtro de fecha en SQL
            despachos = self.db.execute_firebird_query(query, fetch_size=1000)
            print(f"    Total despachos a analizar: {len(despachos)}")
            
            # Traer fechas por separado para evitar el error
            fecha_query = """
            SELECT NUM_DESP, FEC_DESP
            FROM DESP
            WHERE FEC_DESP IS NOT NULL
            """
            fechas_data = self.db.execute_firebird_query(fecha_query, fetch_size=1000)
            
            # Crear diccionario de fechas
            fechas_dict = {}
            for fd in fechas_data:
                num = fd.get('NUM_DESP')
                if num:
                    fechas_dict[num] = self.parse_firebird_date(fd.get('FEC_DESP'))
            
            # Obtener info de clientes
            clientes = {}
            cliente_query = "SELECT COD_CLIE, NOM_CLIE, RUC_CLIE FROM CLIE"
            try:
                cliente_data = self.db.execute_firebird_query(cliente_query, fetch_size=5000)
                for c in cliente_data:
                    if c.get('COD_CLIE'):
                        clientes[c['COD_CLIE']] = {
                            'nombre': c.get('NOM_CLIE'),
                            'ruc': c.get('RUC_CLIE')
                        }
            except:
                pass
            
            # Agrupar por cliente y fecha
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=7)
            cliente_dias = {}
            
            for d in despachos:
                num_desp = d.get('NUM_DESP')
                fecha = fechas_dict.get(num_desp)
                cliente = d.get('COD_CLIE')
                
                if fecha and cliente and fecha >= fecha_limite:
                    fecha_dia = fecha.date()
                    key = f"{cliente}_{fecha_dia}"
                    
                    if key not in cliente_dias:
                        cliente_info = clientes.get(cliente, {})
                        cliente_dias[key] = {
                            'cliente': cliente,
                            'nombre': cliente_info.get('nombre'),
                            'ruc': cliente_info.get('ruc'),
                            'fecha': fecha,
                            'despachos': []
                        }
                    
                    cliente_dias[key]['despachos'].append({
                        'num': num_desp,
                        'cantidad': self.safe_float(d.get('CAN_DESP', 0)),
                        'valor': self.safe_float(d.get('VTO_DESP', 0))
                    })
            
            print(f"    Días-cliente analizados: {len(cliente_dias)}")
            
            # Detectar múltiples despachos el mismo día
            for key, info in cliente_dias.items():
                num_despachos = len(info['despachos'])
                
                if num_despachos > 3:  # Más de 3 despachos el mismo día
                    # ID único para el grupo
                    group_id = f"MULTIPLE_{key}_{num_despachos}"
                    
                    if not self.check_existing_case("DESP", group_id, DetectorType.FUEL_THEFT):
                        total_galones = sum([d['cantidad'] for d in info['despachos']])
                        total_valor = sum([d['valor'] for d in info['despachos']])
                        
                        case = self.create_fraud_case(
                            title=f"Múltiples repostajes mismo día - {info['nombre'] or info['cliente']}",
                            description=f"Cliente {info['nombre'] or 'Desconocido'} realizó "
                                       f"{num_despachos} despachos en el mismo día. "
                                       f"Total: {total_galones:.1f} galones, ${total_valor:,.2f}",
                            detector_type=DetectorType.FUEL_THEFT,
                            severity=FraudSeverity.HIGH if num_despachos > 5 else FraudSeverity.MEDIUM,
                            amount=total_valor,
                            source_table="DESP",
                            source_record_id=group_id,
                            client_code=info['cliente'],
                            client_name=info['nombre'],
                            client_ruc=info['ruc'],
                            transaction_date=info['fecha'],
                            confidence_score=90.0,
                            detection_rules={"rule": "repostajes_multiples", "count": num_despachos}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"    Error en _detect_repostajes_excesivos: {e}")

class ManipulacionDatos(BaseDetector):
    """Detector de manipulación de datos"""
    
    def detect(self) -> List[Dict[str, Any]]:
        self.results = []
        
        self._detect_cambios_masivos()
        self._detect_secuencias_faltantes()
        
        # Filtrar None (casos duplicados)
        self.results = [r for r in self.results if r is not None]
        
        return self.results
    
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
            
            for key, info in usuario_cambios.items():
                if info['count'] > 20:
                    # ID único para el grupo
                    group_id = f"MASSIVE_{key}_{info['count']}"
                    
                    if not self.check_existing_case("XDCTO", group_id, DetectorType.DATA_MANIPULATION):
                        case = self.create_fraud_case(
                            title=f"Cambios masivos detectados - Usuario {info['usuario']}",
                            description=f"El usuario {info['usuario']} realizó {info['count']} "
                                       f"modificaciones en el día {info['fecha'].date()}. "
                                       f"Esto requiere revisión.",
                            detector_type=DetectorType.DATA_MANIPULATION,
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
            print(f"    Error en _detect_cambios_masivos: {e}")
    
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
                    import re
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
                            detector_type=DetectorType.SEQUENCE_GAP,
                            severity=FraudSeverity.MEDIUM if total_gap < 50 else FraudSeverity.HIGH,
                            source_table="DCTO",
                            source_record_id=group_id,
                            confidence_score=70.0,
                            detection_rules={"rule": "secuencia_faltante", "gaps": len(gaps), "total": total_gap}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"    Error en _detect_secuencias_faltantes: {e}")